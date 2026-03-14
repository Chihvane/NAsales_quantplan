from __future__ import annotations

from core.schema_validator import validate_required_fields


def validate_field_record(record: dict) -> list[str]:
    required_fields = ["field_id", "schema_version", "entity", "data_type", "source"]
    return validate_required_fields(record, required_fields)
