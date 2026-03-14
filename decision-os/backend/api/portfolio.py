from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import build_market_snapshot


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary")
def portfolio_summary() -> dict:
    snapshot = build_market_snapshot()
    return {"rows": snapshot["portfolio_rows"]}
