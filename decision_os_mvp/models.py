from __future__ import annotations

import random


def _clamp(value: float, floor: float = 0.0, ceiling: float = 1.0) -> float:
    return max(floor, min(ceiling, value))


def compute_market_factor(data: dict[str, float]) -> float:
    # Normalize raw market signals into a bounded 0-1 attractiveness score.
    tam_score = _clamp(data["TAM"] / 200_000_000)
    growth_score = _clamp(data["CAGR"] / 0.20)
    competition_score = _clamp(1 - (data["HHI"] / 5000))
    stability_score = _clamp(1 - data["volatility"])
    return (
        tam_score * 0.25
        + growth_score * 0.25
        + competition_score * 0.25
        + stability_score * 0.25
    )


def monte_carlo_profit_simulation(
    data: dict[str, float],
    simulations: int = 5000,
    seed: int = 42,
    include_series: bool = False,
) -> dict[str, float]:
    rng = random.Random(seed)
    profits: list[float] = []

    for _ in range(simulations):
        price = rng.normalvariate(data["expected_price"], 5)
        cost = rng.normalvariate(data["landed_cost"], 3)
        fee = data["platform_fee"]
        profits.append(price - cost - fee)

    profits.sort()
    p10 = profits[int(0.1 * simulations)]
    p50 = profits[int(0.5 * simulations)]
    p90 = profits[int(0.9 * simulations)]
    loss_probability = len([profit for profit in profits if profit < 0]) / simulations

    result: dict[str, float | list[float]] = {
        "profit_p10": p10,
        "profit_p50": p50,
        "profit_p90": p90,
        "loss_probability": loss_probability,
    }
    if include_series:
        result["profits"] = profits
    return result
