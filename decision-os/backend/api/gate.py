from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import build_market_snapshot


router = APIRouter(prefix="/gate", tags=["gate"])


@router.get("/status")
def gate_status() -> dict:
    snapshot = build_market_snapshot()
    return {
        "decision": snapshot["decision"],
        "factor_score": round(snapshot["factor_score"], 4),
        "loss_probability": round(snapshot["model_outputs"]["loss_probability"], 4),
    }
