from __future__ import annotations

from fastapi import APIRouter

from backend.services.system_flow import (
    build_system_snapshot_payload,
    load_or_run_full_chain_payload,
    run_full_chain_payload,
)


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/snapshot")
def system_snapshot() -> dict:
    return build_system_snapshot_payload()


@router.get("/summary")
def system_summary(refresh: bool = False) -> dict:
    return load_or_run_full_chain_payload(refresh=refresh)


@router.post("/run-full-chain")
def run_full_chain_pipeline() -> dict:
    return run_full_chain_payload()


@router.get("/reports")
def system_reports(refresh: bool = False) -> dict:
    payload = load_or_run_full_chain_payload(refresh=refresh)
    return {
        "status": payload["status"],
        "reports_overview": payload["reports_overview"],
        "artifacts": payload["artifacts"],
    }

