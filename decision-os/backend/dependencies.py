from __future__ import annotations

from typing import Any, Generator

from backend.capital_engine.capital_allocator import compute_capital_state
from backend.capital_engine.risk_monitor import build_risk_state
from backend.factor_layer.factor_engine import compute_market_factor
from backend.field_layer.field_loader import load_sample_market_fields
from backend.gate_engine.gate_engine import evaluate_market_gate
from backend.model_layer.monte_carlo import run_profit_simulation
from backend.portfolio_engine.portfolio_optimizer import rank_portfolio_rows
from database.connection import session_scope


def get_db_session() -> Generator:
    with session_scope() as session:
        yield session


def get_current_tenant_id(claims: dict[str, Any]) -> str:
    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise ValueError("tenant_id is missing from claims")
    return tenant_id


def build_market_snapshot() -> dict[str, Any]:
    field_data = load_sample_market_fields()
    factor_score = compute_market_factor(field_data)
    model_outputs = run_profit_simulation(field_data)
    capital_state = compute_capital_state(total=2_000_000, allocated=1_200_000)
    risk_state = build_risk_state(max_loss_probability=0.3, max_drawdown=0.2)
    required_capital = 500_000
    decision = evaluate_market_gate(
        factor_score=factor_score,
        model_outputs=model_outputs,
        capital_state=capital_state,
        risk_state=risk_state,
        required_capital=required_capital,
    )
    portfolio_rows = rank_portfolio_rows(
        [
            {"channel": "Amazon", "score": model_outputs["profit_p50"] / 32, "allocated_capital": 240000},
            {"channel": "DTC", "score": model_outputs["profit_p50"] / 29, "allocated_capital": 180000},
            {"channel": "TikTok Shop", "score": model_outputs["profit_p50"] / 35, "allocated_capital": 140000},
        ]
    )
    return {
        "field_data": field_data,
        "factor_score": factor_score,
        "model_outputs": model_outputs,
        "capital_state": capital_state,
        "risk_state": risk_state,
        "required_capital": required_capital,
        "decision": decision,
        "portfolio_rows": portfolio_rows,
    }
