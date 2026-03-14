from __future__ import annotations


def load_sample_market_fields() -> dict[str, float]:
    return {
        "TAM": 120_000_000,
        "CAGR": 0.12,
        "HHI": 1800,
        "volatility": 0.18,
        "landed_cost": 32,
        "expected_price": 65,
        "platform_fee": 8,
    }
