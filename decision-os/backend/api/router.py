from __future__ import annotations

from fastapi import APIRouter

from backend.api.audit import router as audit_router
from backend.api.capital import router as capital_router
from backend.api.gate import router as gate_router
from backend.api.market import router as market_router
from backend.api.model import router as model_router
from backend.api.portfolio import router as portfolio_router


api_router = APIRouter()
api_router.include_router(market_router)
api_router.include_router(model_router)
api_router.include_router(gate_router)
api_router.include_router(capital_router)
api_router.include_router(portfolio_router)
api_router.include_router(audit_router)
