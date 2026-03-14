from __future__ import annotations

import importlib
from statistics import mean


def get_evidently_status() -> dict[str, object]:
    try:
        importlib.import_module("evidently")
        available = True
    except Exception:
        available = False
    return {
        "name": "Evidently",
        "slug": "evidently",
        "package": "evidently",
        "available": available,
        "purpose": "data drift and monitoring summaries",
    }


def build_drift_payload(
    reference_rows: list[dict[str, float]],
    current_rows: list[dict[str, float]],
    monitored_columns: list[str],
) -> dict[str, object]:
    column_deltas: dict[str, float] = {}
    for column in monitored_columns:
        reference_values = [float(row[column]) for row in reference_rows if column in row]
        current_values = [float(row[column]) for row in current_rows if column in row]
        if not reference_values or not current_values:
            column_deltas[column] = 0.0
            continue
        reference_mean = mean(reference_values)
        current_mean = mean(current_values)
        delta = 0.0 if reference_mean == 0 else (current_mean - reference_mean) / reference_mean
        column_deltas[column] = round(delta, 6)
    drifted_columns = [column for column, delta in column_deltas.items() if abs(delta) >= 0.15]
    return {
        "integration": "evidently",
        "status": "review" if drifted_columns else "pass",
        "package_available": get_evidently_status()["available"],
        "drifted_columns": drifted_columns,
        "column_mean_delta": column_deltas,
    }
