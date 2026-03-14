from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import build_market_snapshot


router = APIRouter(prefix="/model", tags=["model"])


@router.get("/simulation")
def model_simulation() -> dict:
    snapshot = build_market_snapshot()
    return snapshot["model_outputs"]
