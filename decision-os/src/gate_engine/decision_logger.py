from __future__ import annotations

from hashlib import sha256
import json


def build_decision_log(payload: dict) -> dict:
    signature = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    result = dict(payload)
    result["hash_signature"] = signature
    return result
