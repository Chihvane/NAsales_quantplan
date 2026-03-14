from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from decision_os_v2.capital_allocator import allocate_portfolio
from decision_os_v2.demo import run_decision_os_v2_demo
from decision_os_v2.feedback_engine import evaluate_feedback_record
from decision_os_v2.gate_engine_v2 import build_decision_record, evaluate_gate_v2
from decision_os_v2.models import CapitalPoolState, OpportunitySpec, RiskBudgetState


class DecisionOSV2Tests(unittest.TestCase):
    def test_gate_engine_passes_and_emits_decision_record(self) -> None:
        gate_config = {
            "gate_schema": {
                "gate_id": "GATE-MARKET-ENTRY-01",
                "schema_version": "2.1",
                "logic": "AND",
                "conditions": [
                    {"source": "model_output", "ref": "profit_p50", "operator": ">=", "value": 0.0},
                    {
                        "source": "model_output",
                        "ref": "loss_probability",
                        "operator": "<=",
                        "budget_ref": "risk_budget.max_loss_probability",
                    },
                    {
                        "source": "capital",
                        "ref": "required_capital",
                        "operator": "<=",
                        "budget_ref": "capital_pool.free_capital",
                    },
                    {"source": "factor", "ref": "FAC-MARKET-ATTRACT", "operator": ">=", "value": 0.5},
                ],
                "decision_output": {"on_pass": "GO", "on_fail": "NO_GO"},
            }
        }

        result = evaluate_gate_v2(
            gate_config,
            model_outputs={"profit_p50": 0.11, "loss_probability": 0.14},
            factor_scores={"FAC-MARKET-ATTRACT": 0.61},
            capital_state={"required_capital": 250000, "free_capital": 1000000},
            risk_state={"max_loss_probability": 0.30},
        )

        self.assertEqual(result.status, "GO")
        self.assertEqual(result.failed_conditions, ())

        record = build_decision_record(
            decision_id="DEC-0001",
            gate_result=result,
            model_version="2.0.0",
            capital_version="2.0",
            risk_version="2.0",
            approved_by="strategy_committee",
            approved_at="2026-03-14T12:00:00Z",
        )
        self.assertEqual(record.status, "GO")
        self.assertEqual(record.gate_id, "GATE-MARKET-ENTRY-01")
        self.assertTrue(record.hash_signature)

    def test_gate_engine_fails_when_budget_backed_threshold_breaks(self) -> None:
        gate_config = {
            "gate_schema": {
                "gate_id": "GATE-RISK-CHECK-01",
                "schema_version": "2.1",
                "logic": "AND",
                "conditions": [
                    {
                        "source": "model_output",
                        "ref": "loss_probability",
                        "operator": "<=",
                        "budget_ref": "risk_budget.max_loss_probability",
                    }
                ],
                "decision_output": {"on_pass": "GO", "on_fail": "NO_GO"},
            }
        }

        result = evaluate_gate_v2(
            gate_config,
            model_outputs={"loss_probability": 0.42},
            risk_state={"max_loss_probability": 0.30},
        )
        self.assertEqual(result.status, "NO_GO")
        self.assertEqual(result.failed_conditions, ("model_output:loss_probability",))

    def test_capital_allocator_respects_limits(self) -> None:
        capital_pool = CapitalPoolState(
            capital_id="CAP-001",
            schema_version="2.0",
            total_capital=1_500_000,
            allocated_capital=300_000,
            free_capital=1_200_000,
            cost_of_capital=0.12,
        )
        risk_budget = RiskBudgetState(
            risk_id="RSK-001",
            schema_version="2.0",
            max_loss_probability=0.30,
            max_drawdown=0.20,
            max_inventory_exposure=0.25,
            max_channel_dependency=0.60,
        )
        opportunities = [
            OpportunitySpec("OPP-001", "Amazon", 400000, 0.22, 0.11, 0.09, 0.10),
            OpportunitySpec("OPP-002", "DTC", 350000, 0.20, 0.10, 0.08, 0.09),
            OpportunitySpec("OPP-003", "Amazon", 380000, 0.21, 0.12, 0.09, 0.08),
            OpportunitySpec("OPP-004", "TikTok Shop", 300000, 0.25, 0.34, 0.10, 0.12),
        ]

        allocation = allocate_portfolio(opportunities, capital_pool, risk_budget)

        self.assertEqual(allocation["accepted_count"], 2)
        self.assertEqual(allocation["rejected_count"], 2)
        reject_reasons = {
            row["opportunity_id"]: row["reject_reason"]
            for row in allocation["rows"]
            if not row["accepted"]
        }
        self.assertEqual(reject_reasons["OPP-004"], "loss_probability_limit")
        self.assertEqual(reject_reasons["OPP-003"], "channel_dependency_limit")

    def test_feedback_engine_flags_recalibration(self) -> None:
        feedback = evaluate_feedback_record(
            decision_id="DEC-0002",
            predicted_profit=100000,
            actual_profit=70000,
            predicted_loss_probability=0.10,
            actual_loss_probability=0.19,
        )
        self.assertEqual(feedback.model_prediction_error, -30000)
        self.assertTrue(feedback.recalibration_required)

    def test_demo_runner_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_decision_os_v2_demo(temp_dir)
            output_path = Path(result["output_json"])
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["gate_result"]["status"], "GO")
            self.assertIn("portfolio", payload)
            self.assertIn("feedback", payload)
