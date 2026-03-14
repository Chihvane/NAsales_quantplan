from __future__ import annotations

from datetime import datetime, timezone


def sample_audit_log() -> list[dict]:
    return [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": "audit",
            "action": "sample_event",
            "entity_id": "DEC-0001",
            "user": "system",
            "version": "3.0.0",
            "status": "ok",
        }
    ]
