from __future__ import annotations

from hashlib import sha256
import json
from datetime import datetime, timezone


def build_decision_log(entity_id: str, action: str, status: str, user: str = "system") -> dict:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": "gate_engine",
        "action": action,
        "entity_id": entity_id,
        "user": user,
        "version": "3.0.0",
        "status": status,
    }
    payload["hash_signature"] = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return payload
