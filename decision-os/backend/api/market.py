from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import build_market_snapshot


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/factor")
def market_factor() -> dict:
    snapshot = build_market_snapshot()
    return {
        "factor_score": round(snapshot["factor_score"], 4),
        "field_data": snapshot["field_data"],
    }
