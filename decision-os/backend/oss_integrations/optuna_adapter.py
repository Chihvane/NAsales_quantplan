from __future__ import annotations

import importlib


def get_optuna_status() -> dict[str, object]:
    try:
        importlib.import_module("optuna")
        available = True
    except Exception:
        available = False
    return {
        "name": "Optuna",
        "slug": "optuna",
        "package": "optuna",
        "available": available,
        "purpose": "hyperparameter optimization for gate thresholds and simulations",
    }
