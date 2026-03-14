from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from decision_os_mvp.capital_risk import CapitalState, RiskBudget
from decision_os_mvp.gate_engine import GateEngine
from decision_os_mvp.models import compute_market_factor, monte_carlo_profit_simulation
from decision_os_mvp.sample_data import generate_sample_market_data
from decision_os_ui.backend.database import (
    init_db,
    list_recent_audit_events,
    list_recent_decisions,
    list_recent_reports,
    save_decision_run,
    save_report_export,
)
from decision_os_ui.report_engine.export_pdf import export_markdown_and_pdf
from decision_os_ui.report_engine.report_generator import generate_report


router = APIRouter()


def _build_portfolio_rows(model_outputs: dict[str, Any], free_capital: float) -> list[dict[str, Any]]:
    base_p50 = float(model_outputs["profit_p50"])
    return [
        {
            "channel": "Amazon",
            "roi_proxy": round(base_p50 / 32, 3),
            "allocated_capital": min(250000, free_capital * 0.31),
            "risk_score": 0.22,
        },
        {
            "channel": "DTC",
            "roi_proxy": round((base_p50 * 1.12) / 32, 3),
            "allocated_capital": min(180000, free_capital * 0.24),
            "risk_score": 0.18,
        },
        {
            "channel": "TikTok Shop",
            "roi_proxy": round((base_p50 * 0.96) / 32, 3),
            "allocated_capital": min(150000, free_capital * 0.19),
            "risk_score": 0.27,
        },
    ]


def compute_snapshot() -> dict[str, Any]:
    data = generate_sample_market_data()
    factor_score = compute_market_factor(data)
    model_outputs = monte_carlo_profit_simulation(data, include_series=True)
    capital_state = CapitalState(total=2_000_000, allocated=1_200_000)
    risk_budget = RiskBudget(max_loss_probability=0.3, max_drawdown=0.2)
    required_capital = 500_000
    decision = GateEngine().evaluate(
        factor_score=factor_score,
        model_outputs=model_outputs,
        capital_state=capital_state,
        risk_budget=risk_budget,
        required_capital=required_capital,
    )
    portfolio_rows = _build_portfolio_rows(model_outputs, capital_state.free)
    return {
        "factor_score": factor_score,
        "model_outputs": model_outputs,
        "free_capital": capital_state.free,
        "required_capital": required_capital,
        "risk_budget": {
            "max_loss_probability": risk_budget.max_loss_probability,
            "max_drawdown": risk_budget.max_drawdown,
        },
        "decision": decision,
        "portfolio_rows": portfolio_rows,
        "audit": {
            "data_source": "decision_os_mvp.sample_data",
            "model_version": "mvp-1.0",
            "gate_engine_version": "mvp-1.0",
        },
    }


@router.on_event("startup")
def startup() -> None:  # pragma: no cover
    init_db()


@router.get("/health")
def health() -> dict[str, str]:
    init_db()
    return {"status": "ok"}


@router.get("/decision")
def get_decision(persist: bool = False) -> dict[str, Any]:
    init_db()
    snapshot = compute_snapshot()
    if persist:
        run_id = save_decision_run(snapshot)
        snapshot["run_id"] = run_id
    return snapshot


@router.get("/dashboard/executive")
def executive_dashboard() -> dict[str, Any]:
    snapshot = compute_snapshot()
    return {
        "market_factor": round(snapshot["factor_score"], 3),
        "gate_status": snapshot["decision"],
        "capital_utilization_rate": round(
            snapshot["required_capital"] / max(snapshot["free_capital"], 1.0), 3
        ),
        "risk_budget_utilization": round(
            snapshot["model_outputs"]["loss_probability"]
            / max(snapshot["risk_budget"]["max_loss_probability"], 0.001),
            3,
        ),
        "expected_profit_p50": round(snapshot["model_outputs"]["profit_p50"], 2),
    }


@router.get("/dashboard/model")
def model_dashboard() -> dict[str, Any]:
    snapshot = compute_snapshot()
    return {
        "factor_score": round(snapshot["factor_score"], 3),
        "profit_distribution": snapshot["model_outputs"]["profits"],
        "profit_p10": round(snapshot["model_outputs"]["profit_p10"], 2),
        "profit_p50": round(snapshot["model_outputs"]["profit_p50"], 2),
        "profit_p90": round(snapshot["model_outputs"]["profit_p90"], 2),
        "loss_probability": round(snapshot["model_outputs"]["loss_probability"], 3),
        "factor_weights": {
            "tam": 0.25,
            "growth": 0.25,
            "competition": 0.25,
            "stability": 0.25,
        },
    }


@router.get("/dashboard/portfolio")
def portfolio_dashboard() -> dict[str, Any]:
    snapshot = compute_snapshot()
    return {
        "portfolio_rows": snapshot["portfolio_rows"],
        "capital_allocation_total": round(
            sum(row["allocated_capital"] for row in snapshot["portfolio_rows"]), 2
        ),
        "average_roi_proxy": round(
            sum(row["roi_proxy"] for row in snapshot["portfolio_rows"]) / len(snapshot["portfolio_rows"]),
            3,
        ),
    }


@router.get("/dashboard/audit")
def audit_dashboard() -> dict[str, Any]:
    init_db()
    return {
        "recent_decisions": list_recent_decisions(),
        "recent_reports": list_recent_reports(),
        "audit_events": list_recent_audit_events(),
    }


@router.post("/report/generate")
def generate_automated_report() -> dict[str, Any]:
    init_db()
    snapshot = compute_snapshot()
    run_id = save_decision_run(snapshot)
    snapshot["run_id"] = run_id
    markdown_text = generate_report(snapshot)
    report_dir = Path(__file__).resolve().parents[1] / "artifacts" / "reports"
    paths = export_markdown_and_pdf(markdown_text, report_dir, f"decision_report_run_{run_id}")
    export_id = save_report_export(
        markdown_path=paths["markdown_path"],
        html_path=paths["html_path"],
        pdf_path=paths["pdf_path"],
        decision=snapshot["decision"],
    )
    return {
        "run_id": run_id,
        "export_id": export_id,
        "decision": snapshot["decision"],
        "paths": paths,
    }
