from __future__ import annotations

from random import Random

from .models import Part3Assumptions
from .stats_utils import percentile_band as _band


def _compute_margin(
    procurement_cost: float,
    compliance_cost: float,
    logistics_cost: float,
    duty_cost: float,
    fees_cost: float,
    sell_price: float,
    channel_fee_rate: float,
    marketing_fee_rate: float,
    working_capital_rate: float,
    return_rate: float,
    return_cost_per_unit: float,
) -> tuple[float, float, float, float, float]:
    landed_cost = procurement_cost + compliance_cost + logistics_cost + duty_cost + fees_cost
    working_capital_cost = landed_cost * working_capital_rate
    return_reserve = return_rate * return_cost_per_unit
    sellable_cost = landed_cost + working_capital_cost + return_reserve
    channel_fee = sell_price * channel_fee_rate
    marketing_fee = sell_price * marketing_fee_rate
    net_margin = sell_price - channel_fee - marketing_fee - sellable_cost
    net_margin_rate = net_margin / sell_price if sell_price else 0.0
    denominator = 1 - channel_fee_rate - marketing_fee_rate
    break_even_price = sellable_cost / denominator if denominator > 0 else 0.0
    return landed_cost, sellable_cost, net_margin, (net_margin_rate if sell_price else 0.0), break_even_price


def _build_sensitivity(best_scenario: dict, assumptions: Part3Assumptions) -> list[dict[str, float | str]]:
    if not best_scenario:
        return []

    base_sell_price = assumptions.target_sell_price
    base_procurement = best_scenario.get("procurement_cost", 0.0)
    base_compliance = best_scenario.get("compliance_cost", 0.0)
    base_logistics = best_scenario.get("logistics_cost", 0.0)
    base_duty = best_scenario.get("duty_cost", 0.0)
    base_fees = best_scenario.get("fees_cost", 0.0)
    base_net_margin = best_scenario.get("net_margin", 0.0)
    base_margin_rate = best_scenario.get("net_margin_rate", 0.0)

    driver_rows = [
        ("procurement_cost", 1.08, 0.95),
        ("logistics_cost", 1.18, 0.92),
        ("duty_cost", 1.25, 0.9),
        ("sell_price", 0.95, 1.03),
        ("marketing_fee_rate", 1.25, 0.9),
        ("return_rate", 1.5, 0.8),
    ]
    sensitivity = []
    for driver_name, downside_factor, upside_factor in driver_rows:
        procurement_cost = base_procurement
        compliance_cost = base_compliance
        logistics_cost = base_logistics
        duty_cost = base_duty
        fees_cost = base_fees
        sell_price = base_sell_price
        marketing_fee_rate = assumptions.marketing_fee_rate
        return_rate = assumptions.return_rate

        if driver_name == "procurement_cost":
            procurement_cost *= downside_factor
        elif driver_name == "logistics_cost":
            logistics_cost *= downside_factor
        elif driver_name == "duty_cost":
            duty_cost *= downside_factor
        elif driver_name == "sell_price":
            sell_price *= downside_factor
        elif driver_name == "marketing_fee_rate":
            marketing_fee_rate *= downside_factor
        elif driver_name == "return_rate":
            return_rate *= downside_factor

        _, _, downside_margin, downside_margin_rate, _ = _compute_margin(
            procurement_cost,
            compliance_cost,
            logistics_cost,
            duty_cost,
            fees_cost,
            sell_price,
            assumptions.channel_fee_rate,
            marketing_fee_rate,
            assumptions.working_capital_rate,
            return_rate,
            assumptions.return_cost_per_unit,
        )

        procurement_cost = base_procurement
        logistics_cost = base_logistics
        duty_cost = base_duty
        sell_price = base_sell_price
        marketing_fee_rate = assumptions.marketing_fee_rate
        return_rate = assumptions.return_rate

        if driver_name == "procurement_cost":
            procurement_cost *= upside_factor
        elif driver_name == "logistics_cost":
            logistics_cost *= upside_factor
        elif driver_name == "duty_cost":
            duty_cost *= upside_factor
        elif driver_name == "sell_price":
            sell_price *= upside_factor
        elif driver_name == "marketing_fee_rate":
            marketing_fee_rate *= upside_factor
        elif driver_name == "return_rate":
            return_rate *= upside_factor

        _, _, upside_margin, upside_margin_rate, _ = _compute_margin(
            procurement_cost,
            compliance_cost,
            logistics_cost,
            duty_cost,
            fees_cost,
            sell_price,
            assumptions.channel_fee_rate,
            marketing_fee_rate,
            assumptions.working_capital_rate,
            return_rate,
            assumptions.return_cost_per_unit,
        )

        sensitivity.append(
            {
                "driver": driver_name,
                "base_net_margin": round(base_net_margin, 2),
                "base_net_margin_rate": round(base_margin_rate, 4),
                "downside_net_margin": round(downside_margin, 2),
                "downside_net_margin_rate": round(downside_margin_rate, 4),
                "downside_impact": round(downside_margin - base_net_margin, 2),
                "upside_net_margin": round(upside_margin, 2),
                "upside_net_margin_rate": round(upside_margin_rate, 4),
                "upside_impact": round(upside_margin - base_net_margin, 2),
            }
        )

    sensitivity.sort(key=lambda row: abs(row["downside_impact"]), reverse=True)
    return sensitivity


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
        logistics_low = max(0.72, 1 - route_volatility_score * 1.1)
        logistics_high = 1 + route_volatility_score * 2.1
        logistics_mode = 1 + route_volatility_score * 0.4
        logistics_cost = best_scenario.get("logistics_cost", 0.0) * rng.triangular(
            logistics_low,
            logistics_high,
            logistics_mode,
        )
        duty_cost = best_scenario.get("duty_cost", 0.0) * rng.triangular(0.9, 1.25, 1.03)
        fees_cost = best_scenario.get("fees_cost", 0.0) * rng.triangular(0.95, 1.18, 1.02)

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
            assumptions.target_sell_price * 0.93,
            assumptions.target_sell_price * 1.03,
            assumptions.target_sell_price * 0.99,
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

        landed_cost, sellable_cost, net_margin, net_margin_rate, break_even_price = _compute_margin(
            procurement_cost,
            compliance_cost,
            logistics_cost,
            duty_cost,
            fees_cost,
            realized_sell_price,
            channel_fee_rate,
            marketing_fee_rate,
            working_capital_rate,
            return_rate,
            return_cost_per_unit,
        )

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
        "sensitivity": _build_sensitivity(best_scenario, assumptions),
    }
