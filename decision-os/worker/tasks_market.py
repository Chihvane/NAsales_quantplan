from __future__ import annotations

from backend.api_connectors.amazon_sp import fetch_inventory, fetch_orders, fetch_prices
from backend.api_connectors.google_trends import fetch_interest_over_time, fetch_related_queries
from backend.dependencies import build_market_snapshot
from worker.celery_app import celery_app


@celery_app.task
def fetch_market_snapshot() -> dict:
    return build_market_snapshot()


@celery_app.task
def ingest_external_sources() -> dict:
    return {
        "amazon_orders": fetch_orders(),
        "amazon_inventory": fetch_inventory(),
        "amazon_prices": fetch_prices(),
        "trends_interest": fetch_interest_over_time(),
        "trends_related_queries": fetch_related_queries(),
    }
