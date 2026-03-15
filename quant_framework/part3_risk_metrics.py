from __future__ import annotations

from .models import GateThresholdRecord, Part3Assumptions, Part3ScenarioRecord
from .risk_metrics import expected_shortfall, sharpe_like, sortino_like, tail_ratio, value_at_risk
from .stats_utils import clip, safe_divide


def _resolve_margin_floor(
    thresholds: list[GateThresholdRecord],
    assumptions: Part3Assumptions,
) -> float:
    for row in thresholds:
        if row.metric_name in {"net_margin_rate", "margin_safety_floor", "min_net_margin_rate"}:
            return row.threshold_value
    return assumptions.target_margin_floor


def _scenario_stress_table(
    best_scenario: dict,
    scenarios: list[Part3ScenarioRecord],
    assumptions: Part3Assumptions,
    margin_floor: float,
) -> list[dict]:
    if not best_scenario:
        return []

    base_sell_price = assumptions.target_sell_price
    base_procurement = best_scenario.get("procurement_cost", 0.0)
    base_logistics = best_scenario.get("logistics_cost", 0.0)
    base_duty = best_scenario.get("duty_cost", 0.0)
    base_fees = best_scenario.get("fees_cost", 0.0)
    base_compliance = best_scenario.get("compliance_cost", 0.0)
    base_margin = best_scenario.get("net_margin", 0.0)
    rows = []

    for scenario in scenarios:
        if not scenario.active_flag:
            continue
        procurement = base_procurement
        logistics = base_logistics
        duty = base_duty
        fees = base_fees
        sell_price = base_sell_price
        if scenario.shock_target == "procurement_cost":
            procurement *= scenario.shock_multiplier
        elif scenario.shock_target == "logistics_cost":
            logistics *= scenario.shock_multiplier
        elif scenario.shock_target == "duty_cost":
            duty *= scenario.shock_multiplier
        elif scenario.shock_target == "fees_cost":
            fees *= scenario.shock_multiplier
        elif scenario.shock_target == "sell_price":
            sell_price *= scenario.shock_multiplier
        elif scenario.shock_target == "landed_cost":
            procurement *= scenario.shock_multiplier
            logistics *= scenario.shock_multiplier
            duty *= scenario.shock_multiplier
            fees *= scenario.shock_multiplier

        landed_cost = procurement + logistics + duty + fees + base_compliance
        working_capital_cost = landed_cost * assumptions.working_capital_rate
        return_reserve = assumptions.return_rate * assumptions.return_cost_per_unit
        sellable_cost = landed_cost + working_capital_cost + return_reserve
        channel_fee = sell_price * assumptions.channel_fee_rate
        marketing_fee = sell_price * assumptions.marketing_fee_rate
        net_margin = sell_price - channel_fee - marketing_fee - sellable_cost
        net_margin_rate = safe_divide(net_margin, sell_price)
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.scenario_name,
                "shock_target": scenario.shock_target,
                "shock_multiplier": scenario.shock_multiplier,
                "severity": scenario.severity,
                "stressed_net_margin": round(net_margin, 2),
                "stressed_net_margin_rate": round(net_margin_rate, 4),
                "margin_delta": round(net_margin - base_margin, 2),
                "gate_result": "pass" if net_margin_rate >= margin_floor else "fail",
            }
        )
    rows.sort(key=lambda row: row["stressed_net_margin_rate"])
    return rows


def compute_part3_risk_metrics(
    landed_cost_metrics: dict,
    monte_carlo: dict,
    assumptions: Part3Assumptions,
    threshold_registry: list[GateThresholdRecord],
    scenario_registry: list[Part3ScenarioRecord],
) -> dict:
    best_scenario = landed_cost_metrics.get("best_scenario", {})
    scenario_table = landed_cost_metrics.get("scenario_table", [])
    margin_floor = _resolve_margin_floor(threshold_registry, assumptions)

    raw_samples = monte_carlo.get("raw_samples", {})
    net_margin_samples = raw_samples.get("net_margin", [])
    margin_rate_samples = raw_samples.get("net_margin_rate", [])

    if not net_margin_samples:
        net_margin_samples = [row.get("net_margin", 0.0) for row in scenario_table]
    if not margin_rate_samples:
        margin_rate_samples = [row.get("net_margin_rate", 0.0) for row in scenario_table]

    value_at_risk_95 = value_at_risk(net_margin_samples, 0.95)
    value_at_risk_99 = value_at_risk(net_margin_samples, 0.99)
    expected_shortfall_95 = expected_shortfall(net_margin_samples, 0.95)
    expected_shortfall_99 = expected_shortfall(net_margin_samples, 0.99)
    margin_rate_var_95 = value_at_risk(margin_rate_samples, 0.95)
    margin_rate_es_95 = expected_shortfall(margin_rate_samples, 0.95)
    loss_probability = safe_divide(sum(1 for value in net_margin_samples if value < 0), len(net_margin_samples))
    margin_floor_breach_probability = safe_divide(
        sum(1 for value in margin_rate_samples if value < margin_floor),
        len(margin_rate_samples),
    )
    tail_shortfall_probability = safe_divide(
        sum(1 for value in net_margin_samples if value <= expected_shortfall_95),
        len(net_margin_samples),
    )
    confidence_gap = max(0.0, 1 - best_scenario.get("scenario_confidence_score", 0.0))
    tail_risk_score = clip(
        loss_probability * 0.35
        + margin_floor_breach_probability * 0.35
        + confidence_gap * 0.2
        + best_scenario.get("route_volatility_score", 0.0) * 0.1,
        0.0,
        1.0,
    )

    if tail_risk_score >= 0.7:
        tail_risk_level = "high"
    elif tail_risk_score >= 0.45:
        tail_risk_level = "medium"
    else:
        tail_risk_level = "low"

    return {
        "value_at_risk_95": round(value_at_risk_95, 2),
        "value_at_risk_99": round(value_at_risk_99, 2),
        "expected_shortfall_95": round(expected_shortfall_95, 2),
        "expected_shortfall_99": round(expected_shortfall_99, 2),
        "margin_rate_var_95": round(margin_rate_var_95, 4),
        "margin_rate_es_95": round(margin_rate_es_95, 4),
        "loss_probability": round(loss_probability, 4),
        "margin_floor": round(margin_floor, 4),
        "margin_floor_breach_probability": round(margin_floor_breach_probability, 4),
        "tail_shortfall_probability": round(tail_shortfall_probability, 4),
        "margin_rate_sharpe_like": round(sharpe_like(margin_rate_samples, hurdle_rate=margin_floor), 4),
        "margin_rate_sortino_like": round(sortino_like(margin_rate_samples, hurdle_rate=margin_floor), 4),
        "margin_rate_tail_ratio": round(tail_ratio(margin_rate_samples), 4),
        "worst_shortfall_vs_floor": round(max(margin_floor - margin_rate_var_95, 0.0), 4),
        "tail_risk_score": round(tail_risk_score, 4),
        "tail_risk_level": tail_risk_level,
        "threshold_registry_count": len(threshold_registry),
        "stress_scenarios_active": sum(1 for row in scenario_registry if row.active_flag),
        "scenario_stress_table": _scenario_stress_table(
            best_scenario,
            scenario_registry,
            assumptions,
            margin_floor,
        ),
    }
