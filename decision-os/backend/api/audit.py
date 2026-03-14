from __future__ import annotations

from fastapi import APIRouter

from backend.audit.audit_logger import sample_audit_log


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def audit_logs() -> dict:
    return {"logs": sample_audit_log()}
