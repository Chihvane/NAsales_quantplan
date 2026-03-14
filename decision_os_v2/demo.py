from __future__ import annotations

from pathlib import Path

from .capital_allocator import allocate_portfolio
from .feedback_engine import evaluate_feedback_record
from .gate_engine_v2 import build_decision_record, evaluate_gate_v2
from .models import CapitalPoolState, OpportunitySpec, RiskBudgetState


def run_decision_os_v2_demo(output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gate_config = {
        "gate_schema": {
            "gate_id": "GATE-SKU-LAUNCH",
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

    capital_pool = CapitalPoolState(
        capital_id="CAP-POOL-001",
        schema_version="2.0",
        total_capital=5_000_000,
        allocated_capital=2_100_000,
        free_capital=2_900_000,
        cost_of_capital=0.12,
    )
    risk_budget = RiskBudgetState(
        risk_id="RSK-BUDGET-001",
        schema_version="2.0",
        max_loss_probability=0.30,
        max_drawdown=0.20,
        max_inventory_exposure=0.25,
        max_channel_dependency=0.60,
    )

    gate_result = evaluate_gate_v2(
        gate_config,
        model_outputs={
            "profit_p50": 0.18,
            "loss_probability": 0.12,
        },
        factor_scores={"FAC-MARKET-ATTRACT": 0.64},
        capital_state={"required_capital": 400000, "free_capital": capital_pool.free_capital},
        risk_state={"max_loss_probability": risk_budget.max_loss_probability},
    )
    decision_record = build_decision_record(
        decision_id="DEC-OSV2-0001",
        gate_result=gate_result,
        model_version="2.0.0",
        capital_version=capital_pool.schema_version,
        risk_version=risk_budget.schema_version,
        approved_by="strategy_committee",
        approved_at="2026-03-14T12:00:00Z",
    )

    opportunities = [
        OpportunitySpec("OPP-001", "Amazon", 450000, 0.23, 0.14, 0.08, 0.10),
        OpportunitySpec("OPP-002", "DTC", 320000, 0.19, 0.11, 0.07, 0.08),
        OpportunitySpec("OPP-003", "TikTok Shop", 550000, 0.28, 0.22, 0.12, 0.12),
        OpportunitySpec("OPP-004", "Amazon", 980000, 0.31, 0.35, 0.16, 0.09),
    ]
    portfolio = allocate_portfolio(opportunities, capital_pool, risk_budget)
    feedback = evaluate_feedback_record(
        decision_id=decision_record.decision_id,
        predicted_profit=180000.0,
        actual_profit=147500.0,
        predicted_loss_probability=0.12,
        actual_loss_probability=0.16,
    )

    payload = {
        "gate_result": gate_result.__dict__,
        "decision_record": decision_record.__dict__,
        "portfolio": portfolio,
        "feedback": feedback.__dict__,
    }

    import json

    output_path = output_dir / "decision_os_v2_demo.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_json": str(output_path), "payload": payload}
