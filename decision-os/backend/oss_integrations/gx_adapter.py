from __future__ import annotations

import importlib


def get_gx_status() -> dict[str, object]:
    available = False
    package_name = ""
    for candidate in ("great_expectations", "gx"):
        try:
            importlib.import_module(candidate)
            available = True
            package_name = candidate
            break
        except Exception:
            continue
    return {
        "name": "GX Core",
        "slug": "gx_core",
        "package": package_name or "great_expectations|gx",
        "available": available,
        "purpose": "data quality expectation suites and validation checkpoints",
    }


def build_validation_payload(dataset_name: str, rows: list[dict], required_columns: list[str]) -> dict[str, object]:
    observed_columns = sorted({key for row in rows for key in row.keys()}) if rows else []
    missing_columns = [column for column in required_columns if column not in observed_columns]
    return {
        "integration": "gx_core",
        "dataset_name": dataset_name,
        "row_count": len(rows),
        "required_columns": required_columns,
        "observed_columns": observed_columns,
        "missing_columns": missing_columns,
        "status": "pass" if not missing_columns else "review",
        "package_available": get_gx_status()["available"],
    }
