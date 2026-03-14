from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import build_market_snapshot


router = APIRouter(prefix="/capital", tags=["capital"])


@router.get("/status")
def capital_status() -> dict:
    snapshot = build_market_snapshot()
    return {
        "capital_state": snapshot["capital_state"],
        "risk_state": snapshot["risk_state"],
        "required_capital": snapshot["required_capital"],
    }
