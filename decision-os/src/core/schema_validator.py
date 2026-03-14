from __future__ import annotations


def validate_required_fields(payload: dict, required_fields: list[str]) -> list[str]:
    return [field for field in required_fields if field not in payload or payload[field] in (None, "")]
