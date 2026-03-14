from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .feedback_engine import evaluate_feedback_v3
from .gate_engine_v3 import build_decision_record_v3, evaluate_gate_v3
from .models import CapitalPoolStateV3, PortfolioOpportunityV3, RiskBudgetStateV3
from .portfolio_engine import allocate_portfolio_v3
from .registry_loader import load_registry_file


def _build_capital_pool_state(payload: dict) -> CapitalPoolStateV3:
    body = payload.get("capital_pool", payload)
    return CapitalPoolStateV3(
        capital_pool_id=str(body.get("capital_pool_id", "")),
        schema_version=str(body.get("schema_version", "")),
        total_capital=float(body.get("total_capital", 0.0)),
        allocated_capital=float(body.get("allocated_capital", 0.0)),
        free_capital=float(body.get("free_capital", 0.0)),
        cost_of_capital=float(body.get("cost_of_capital", 0.0)),
    )


def _build_risk_budget_state(payload: dict) -> RiskBudgetStateV3:
    body = payload.get("risk_budget", payload)
    return RiskBudgetStateV3(
        risk_budget_id=str(body.get("risk_budget_id", "")),
        schema_version=str(body.get("schema_version", "")),
        max_loss_probability=float(body.get("max_loss_probability", 0.0)),
        max_drawdown=float(body.get("max_drawdown", 0.0)),
        max_inventory_exposure=float(body.get("max_inventory_exposure", 0.0)),
        max_channel_dependency=float(body.get("max_channel_dependency", 0.0)),
    )


def run_decision_os_v3_demo(output_dir: str | Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    registry_root = root / "decision_os_v3" / "registry"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    system_payload = load_registry_file(registry_root / "system.yaml")
    gate_payload = load_registry_file(registry_root / "examples" / "gate_market_entry.yaml")
    capital_payload = load_registry_file(registry_root / "config" / "capital_pool.yaml")
    risk_payload = load_registry_file(registry_root / "config" / "risk_budget.yaml")

    capital_pool = _build_capital_pool_state(capital_payload)
    risk_budget = _build_risk_budget_state(risk_payload)

    gate_result = evaluate_gate_v3(
        gate_payload,
        model_outputs={"profit_p50": 0.17, "loss_probability": 0.11},
        factor_scores={"FAC-MARKET-ATTRACT": 0.68},
        capital_state={"required_capital": 420000, "free_capital": capital_pool.free_capital},
        risk_state={
            "max_loss_probability": risk_budget.max_loss_probability,
            "max_drawdown": risk_budget.max_drawdown,
        },
    )

    portfolio_id = "PF-0001"
    decision_record = build_decision_record_v3(
        decision_id="DEC-V3-0001",
        gate_result=gate_result,
        model_version="3.0.0",
        capital_version=capital_pool.schema_version,
        risk_version=risk_budget.schema_version,
        portfolio_id=portfolio_id,
        approved_by="strategy_committee",
        approved_at="2026-03-14T12:00:00Z",
        notes="Initial market-entry portfolio decision.",
    )

    opportunities = [
        PortfolioOpportunityV3("OPP-V3-001", portfolio_id, "Amazon", 450000, 0.24, 0.12, 0.09, 0.18, 0.11),
        PortfolioOpportunityV3("OPP-V3-002", portfolio_id, "DTC", 330000, 0.21, 0.10, 0.08, 0.12, 0.10),
        PortfolioOpportunityV3("OPP-V3-003", portfolio_id, "TikTok Shop", 520000, 0.29, 0.18, 0.12, 0.16, 0.13),
        PortfolioOpportunityV3("OPP-V3-004", portfolio_id, "Amazon", 980000, 0.32, 0.34, 0.18, 0.24, 0.09),
    ]
    portfolio = allocate_portfolio_v3(opportunities, capital_pool, risk_budget)

    feedback = evaluate_feedback_v3(
        decision_id=decision_record.decision_id,
        portfolio_id=portfolio_id,
        predicted_profit=205000.0,
        actual_profit=156000.0,
        predicted_loss_probability=0.11,
        actual_loss_probability=0.17,
        predicted_drawdown=0.12,
        actual_drawdown=0.18,
    )

    payload = {
        "system": system_payload,
        "gate_result": asdict(gate_result),
        "decision_record": asdict(decision_record),
        "portfolio": portfolio,
        "feedback": asdict(feedback),
    }
    output_path = output_dir / "decision_os_v3_demo.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output_json": str(output_path), "payload": payload}
