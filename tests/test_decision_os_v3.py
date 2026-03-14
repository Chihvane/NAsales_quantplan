from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from decision_os_v3.feedback_engine import evaluate_feedback_v3
from decision_os_v3.gate_engine_v3 import build_decision_record_v3, evaluate_gate_v3
from decision_os_v3.models import CapitalPoolStateV3, PortfolioOpportunityV3, RiskBudgetStateV3
from decision_os_v3.portfolio_engine import allocate_portfolio_v3
from decision_os_v3.registry_loader import load_registry_file
from decision_os_v3.demo import run_decision_os_v3_demo


class DecisionOSV3Tests(unittest.TestCase):
    def test_registry_loader_reads_yaml(self) -> None:
        root = Path(__file__).resolve().parents[1]
        payload = load_registry_file(root / "decision_os_v3" / "registry" / "system.yaml")
        self.assertEqual(payload["decision_os"]["system_id"], "DOS-V3-NA-001")

    def test_gate_engine_v3_passes_and_builds_record(self) -> None:
        gate_payload = {
            "gate": {
                "gate_id": "GATE-MARKET-ENTRY",
                "schema_version": "3.0",
                "logic": "AND",
                "conditions": [
                    {"source": "model_output", "ref": "profit_p50", "operator": ">=", "value": 0.0},
                    {
                        "source": "model_output",
                        "ref": "loss_probability",
                        "operator": "<=",
                        "budget_ref": "risk_budget.max_loss_probability",
                    },
                    {"source": "factor", "ref": "FAC-MARKET-ATTRACT", "operator": ">=", "value": 0.5},
                    {
                        "source": "capital",
                        "ref": "required_capital",
                        "operator": "<=",
                        "budget_ref": "capital_pool.free_capital",
                    },
                ],
                "decision_output": {"pass": "GO", "fail": "NO_GO"},
            }
        }

        gate_result = evaluate_gate_v3(
            gate_payload,
            model_outputs={"profit_p50": 0.15, "loss_probability": 0.10},
            factor_scores={"FAC-MARKET-ATTRACT": 0.62},
            capital_state={"required_capital": 250000, "free_capital": 900000},
            risk_state={"max_loss_probability": 0.30},
        )
        self.assertEqual(gate_result.status, "GO")
        self.assertFalse(gate_result.capital_blocked)
        self.assertFalse(gate_result.risk_blocked)

        record = build_decision_record_v3(
            decision_id="DEC-V3-0001",
            gate_result=gate_result,
            model_version="3.0.0",
            capital_version="3.0",
            risk_version="3.0",
            portfolio_id="PF-0001",
        )
        self.assertEqual(record.portfolio_id, "PF-0001")
        self.assertTrue(record.hash_signature)

    def test_gate_engine_v3_flags_risk_block(self) -> None:
        gate_payload = {
            "gate": {
                "gate_id": "GATE-RISK-CHECK",
                "schema_version": "3.0",
                "logic": "AND",
                "conditions": [
                    {
                        "source": "model_output",
                        "ref": "loss_probability",
                        "operator": "<=",
                        "budget_ref": "risk_budget.max_loss_probability",
                    }
                ],
                "decision_output": {"pass": "GO", "fail": "NO_GO"},
            }
        }
        gate_result = evaluate_gate_v3(
            gate_payload,
            model_outputs={"loss_probability": 0.41},
            risk_state={"max_loss_probability": 0.30},
        )
        self.assertEqual(gate_result.status, "NO_GO")
        self.assertTrue(gate_result.risk_blocked)

    def test_portfolio_engine_respects_limits(self) -> None:
        capital_pool = CapitalPoolStateV3("CAP-POOL-001", "3.0", 1_600_000, 300_000, 1_300_000, 0.12)
        risk_budget = RiskBudgetStateV3("RSK-BUDGET-001", "3.0", 0.30, 0.20, 0.25, 0.60)
        opportunities = [
            PortfolioOpportunityV3("OPP-1", "PF-0001", "Amazon", 420000, 0.22, 0.11, 0.09, 0.18, 0.10),
            PortfolioOpportunityV3("OPP-2", "PF-0001", "DTC", 350000, 0.20, 0.10, 0.08, 0.15, 0.11),
            PortfolioOpportunityV3("OPP-3", "PF-0001", "Amazon", 450000, 0.19, 0.12, 0.10, 0.20, 0.08),
            PortfolioOpportunityV3("OPP-4", "PF-0001", "TikTok Shop", 300000, 0.27, 0.36, 0.11, 0.14, 0.12),
        ]

        allocation = allocate_portfolio_v3(opportunities, capital_pool, risk_budget)
        self.assertEqual(allocation["accepted_count"], 2)
        self.assertEqual(allocation["rejected_count"], 2)
        reject_reasons = {
            row["opportunity_id"]: row["reject_reason"]
            for row in allocation["rows"]
            if not row["accepted"]
        }
        self.assertEqual(reject_reasons["OPP-4"], "loss_probability_limit")
        self.assertEqual(reject_reasons["OPP-3"], "channel_dependency_limit")

    def test_feedback_v3_marks_recalibration(self) -> None:
        feedback = evaluate_feedback_v3(
            decision_id="DEC-V3-0002",
            portfolio_id="PF-0001",
            predicted_profit=200000,
            actual_profit=140000,
            predicted_loss_probability=0.12,
            actual_loss_probability=0.20,
            predicted_drawdown=0.10,
            actual_drawdown=0.18,
        )
        self.assertTrue(feedback.recalibration_required)
        self.assertEqual(feedback.model_prediction_error, -60000)

    def test_demo_runner_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_decision_os_v3_demo(temp_dir)
            output_path = Path(result["output_json"])
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["gate_result"]["status"], "GO")
            self.assertEqual(payload["decision_record"]["portfolio_id"], "PF-0001")
