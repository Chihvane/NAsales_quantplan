from __future__ import annotations


def fetch_google_trends_stub() -> dict:
    return {"provider": "google_trends", "status": "stub"}


def fetch_interest_over_time() -> dict:
    return {"resource": "interest_over_time", "provider": "google_trends", "status": "planned"}


def fetch_related_queries() -> dict:
    return {"resource": "related_queries", "provider": "google_trends", "status": "planned"}
