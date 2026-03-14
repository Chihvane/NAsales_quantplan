from __future__ import annotations

from backend.oss_integrations.evidently_adapter import get_evidently_status
from backend.oss_integrations.gx_adapter import get_gx_status
from backend.oss_integrations.mlflow_adapter import get_mlflow_status
from backend.oss_integrations.optuna_adapter import get_optuna_status


def list_integrations() -> list[dict[str, object]]:
    return [
        get_gx_status(),
        get_evidently_status(),
        get_mlflow_status(),
        get_optuna_status(),
    ]


def summarize_integrations() -> dict[str, object]:
    integrations = list_integrations()
    return {
        "integration_count": len(integrations),
        "available_count": sum(1 for item in integrations if item["available"]),
        "integrations": integrations,
    }
