from __future__ import annotations

import random


def _percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    index = int((len(sorted_values) - 1) * quantile)
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def run_profit_simulation(data: dict[str, float], simulations: int = 3000, seed: int = 42) -> dict[str, float]:
    rng = random.Random(seed)
    profits: list[float] = []
    for _ in range(simulations):
        price = rng.normalvariate(data["expected_price"], 5)
        cost = rng.normalvariate(data["landed_cost"], 3)
        profits.append(price - cost - data["platform_fee"])
    profits.sort()
    profit_p50 = _percentile(profits, 0.5)
    expected_price = max(float(data["expected_price"]), 1e-9)
    return {
        "profit_p05": _percentile(profits, 0.05),
        "profit_p10": _percentile(profits, 0.10),
        "profit_p50": profit_p50,
        "profit_p90": _percentile(profits, 0.90),
        "mean_profit": sum(profits) / len(profits) if profits else 0.0,
        "margin_p50_ratio": profit_p50 / expected_price,
        "loss_probability": len([profit for profit in profits if profit < 0]) / simulations,
    }
