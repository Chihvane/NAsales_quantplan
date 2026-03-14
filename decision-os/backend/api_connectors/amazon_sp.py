from __future__ import annotations


def fetch_amazon_sp_stub() -> dict:
    return {"provider": "amazon_sp", "status": "stub"}


def fetch_orders() -> dict:
    return {"resource": "orders", "provider": "amazon_sp", "status": "planned"}


def fetch_inventory() -> dict:
    return {"resource": "inventory", "provider": "amazon_sp", "status": "planned"}


def fetch_prices() -> dict:
    return {"resource": "prices", "provider": "amazon_sp", "status": "planned"}
