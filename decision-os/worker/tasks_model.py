from __future__ import annotations

from backend.field_layer.field_loader import load_sample_market_fields
from backend.model_layer.monte_carlo import run_profit_simulation
from worker.celery_app import celery_app


@celery_app.task
def run_model_simulation() -> dict:
    return run_profit_simulation(load_sample_market_fields())


if __name__ == "__main__":
    print(run_model_simulation())
