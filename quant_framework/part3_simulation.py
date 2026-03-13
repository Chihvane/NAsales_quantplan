from __future__ import annotations

from random import Random

from .models import Part3Assumptions


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (percentile / 100)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    return lower_value + (upper_value - lower_value) * fraction


def _band(values: list[float]) -> dict[str, float]:
    return {
        "p10": round(_percentile(values, 10), 4),
        "p50": round(_percentile(values, 50), 4),
        "p90": round(_percentile(values, 90), 4),
    }


def run_landed_cost_monte_carlo(
    best_scenario: dict,
    assumptions: Part3Assumptions,
    route_volatility_score: float = 0.2,
    iterations: int = 1200,
    seed: int = 42,
) -> dict:
    if not best_scenario:
        return {}

    rng = Random(seed)
    landed_costs = []
    sellable_costs = []
    net_margins = []
    margin_rates = []
    break_even_prices = []

    for _ in range(iterations):
        procurement_cost = best_scenario.get("procurement_cost", 0.0) * rng.triangular(0.96, 1.08, 1.0)
        compliance_cost = best_scenario.get("compliance_cost", 0.0) * rng.triangular(0.95, 1.15, 1.02)
        logistics_low = max(0.7, 1 - route_volatility_score * 1.2)
        logistics_high = 1 + route_volatility_score * 2.2
        logistics_mode = 1 + route_volatility_score * 0.45
        logistics_cost = best_scenario.get("logistics_cost", 0.0) * rng.triangular(
            logistics_low,
            logistics_high,
            logistics_mode,
        )
        duty_cost = best_scenario.get("duty_cost", 0.0) * rng.triangular(0.9, 1.25, 1.02)
        fees_cost = best_scenario.get("fees_cost", 0.0) * rng.triangular(0.95, 1.15, 1.0)
        landed_cost = procurement_cost + compliance_cost + logistics_cost + duty_cost + fees_cost

        working_capital_rate = rng.triangular(
            assumptions.working_capital_rate * 0.75,
            assumptions.working_capital_rate * 1.75,
            assumptions.working_capital_rate,
        )
        return_rate = rng.triangular(
            max(0.0, assumptions.return_rate * 0.5),
            assumptions.return_rate * 2.0,
            assumptions.return_rate,
        )
        return_cost_per_unit = rng.triangular(
            assumptions.return_cost_per_unit * 0.75,
            assumptions.return_cost_per_unit * 1.35,
            assumptions.return_cost_per_unit,
        )
        realized_sell_price = rng.triangular(
            assumptions.target_sell_price * 0.92,
            assumptions.target_sell_price * 1.03,
            assumptions.target_sell_price * 0.985,
        )
        channel_fee_rate = rng.triangular(
            assumptions.channel_fee_rate * 0.97,
            assumptions.channel_fee_rate * 1.05,
            assumptions.channel_fee_rate,
        )
        marketing_fee_rate = rng.triangular(
            assumptions.marketing_fee_rate * 0.8,
            assumptions.marketing_fee_rate * 1.35,
            assumptions.marketing_fee_rate,
        )

        working_capital_cost = landed_cost * working_capital_rate
        return_reserve = return_rate * return_cost_per_unit
        sellable_cost = landed_cost + working_capital_cost + return_reserve
        channel_fee = realized_sell_price * channel_fee_rate
        marketing_fee = realized_sell_price * marketing_fee_rate
        net_margin = realized_sell_price - channel_fee - marketing_fee - sellable_cost
        net_margin_rate = net_margin / realized_sell_price if realized_sell_price else 0.0
        denominator = 1 - channel_fee_rate - marketing_fee_rate
        break_even_price = sellable_cost / denominator if denominator > 0 else 0.0

        landed_costs.append(landed_cost)
        sellable_costs.append(sellable_cost)
        net_margins.append(net_margin)
        margin_rates.append(net_margin_rate)
        break_even_prices.append(break_even_price)

    loss_probability = sum(1 for value in net_margins if value < 0) / len(net_margins)
    margin_below_15_probability = sum(1 for value in margin_rates if value < 0.15) / len(margin_rates)

    return {
        "iterations": iterations,
        "seed": seed,
        "loss_probability": round(loss_probability, 4),
        "margin_below_15pct_probability": round(margin_below_15_probability, 4),
        "expected_net_margin": round(sum(net_margins) / len(net_margins), 2),
        "expected_net_margin_rate": round(sum(margin_rates) / len(margin_rates), 4),
        "percentile_bands": {
            "landed_cost": _band(landed_costs),
            "sellable_cost": _band(sellable_costs),
            "net_margin": _band(net_margins),
            "net_margin_rate": _band(margin_rates),
            "break_even_price": _band(break_even_prices),
        },
    }
