from __future__ import annotations

import importlib
import json
from pathlib import Path


def get_mlflow_status() -> dict[str, object]:
    try:
        importlib.import_module("mlflow")
        available = True
    except Exception:
        available = False
    return {
        "name": "MLflow",
        "slug": "mlflow",
        "package": "mlflow",
        "available": available,
        "purpose": "tracking backtests, params, and metrics",
    }


def log_tracking_payload(
    output_path: str | Path,
    run_name: str,
    params: dict[str, object],
    metrics: dict[str, object],
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "integration": "mlflow",
        "run_name": run_name,
        "package_available": get_mlflow_status()["available"],
        "params": params,
        "metrics": metrics,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
