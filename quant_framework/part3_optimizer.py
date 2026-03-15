from __future__ import annotations

from collections import Counter

from .models import Part3Assumptions, Part3OptimizerRecord
from .stats_utils import clip, safe_divide, score_level


def _default_optimizer(assumptions: Part3Assumptions) -> Part3OptimizerRecord:
    return Part3OptimizerRecord(
        optimizer_id="default_part3_optimizer",
        objective_name="maximize_margin_confidence",
        objective_type="constraint_rank",
        risk_measure="loss_probability",
        max_loss_probability=assumptions.max_loss_probability,
        min_net_margin_rate=assumptions.target_margin_floor,
        min_confidence_score=0.65,
        max_lead_time_days=35,
        max_landed_cost=assumptions.target_sell_price * 0.7,
        capital_limit=assumptions.target_sell_price * assumptions.target_order_units,
        active_flag=True,
    )


def compute_part3_optimizer(
    landed_cost_metrics: dict,
    part3_risk_metrics: dict,
    optimizer_registry: list[Part3OptimizerRecord],
    assumptions: Part3Assumptions,
) -> dict:
    scenario_table = landed_cost_metrics.get("scenario_table", [])
    if not scenario_table:
        return {}

    active_optimizer = next((row for row in optimizer_registry if row.active_flag), None) or _default_optimizer(assumptions)
    infeasible_reasons = Counter()
    feasible_rows = []

    for row in scenario_table:
        reasons = []
        if row.get("net_margin_rate", 0.0) < active_optimizer.min_net_margin_rate:
            reasons.append("margin_floor")
        if row.get("scenario_confidence_score", 0.0) < active_optimizer.min_confidence_score:
            reasons.append("confidence_floor")
        if active_optimizer.max_lead_time_days and row.get("lead_time_days", 0) > active_optimizer.max_lead_time_days:
            reasons.append("lead_time_limit")
        if active_optimizer.max_landed_cost and row.get("landed_cost", 0.0) > active_optimizer.max_landed_cost:
            reasons.append("landed_cost_limit")
        if active_optimizer.capital_limit and row.get("capital_required", 0.0) > active_optimizer.capital_limit:
            reasons.append("capital_limit")
        if row.get("scenario_loss_proxy", 0.0) > active_optimizer.max_loss_probability:
            reasons.append("loss_probability_limit")

        if reasons:
            infeasible_reasons.update(reasons)
            continue

        capital_penalty = safe_divide(row.get("capital_required", 0.0), max(active_optimizer.capital_limit, 1.0))
        score = clip(
            row.get("net_margin_rate", 0.0) * 0.45
            + row.get("scenario_confidence_score", 0.0) * 0.25
            + (1 - row.get("route_volatility_score", 0.0)) * 0.15
            + (1 - capital_penalty) * 0.1
            + (1 - safe_divide(row.get("lead_time_days", 0), max(active_optimizer.max_lead_time_days, 1))) * 0.05,
            0.0,
            1.0,
        )
        enriched = dict(row)
        enriched["optimizer_score"] = round(score, 4)
        feasible_rows.append(enriched)

    feasible_rows.sort(key=lambda item: (item["optimizer_score"], item.get("net_margin", 0.0)), reverse=True)
    best_feasible_scenario = feasible_rows[0] if feasible_rows else {}
    tail_risk_score = part3_risk_metrics.get("tail_risk_score", 1.0)
    optimizer_gate_result = "pass" if feasible_rows and tail_risk_score <= 0.75 else "fail"

    return {
        "optimizer_id": active_optimizer.optimizer_id,
        "objective_name": active_optimizer.objective_name,
        "objective_type": active_optimizer.objective_type,
        "risk_measure": active_optimizer.risk_measure,
        "active_constraints": {
            "max_loss_probability": active_optimizer.max_loss_probability,
            "min_net_margin_rate": active_optimizer.min_net_margin_rate,
            "min_confidence_score": active_optimizer.min_confidence_score,
            "max_lead_time_days": active_optimizer.max_lead_time_days,
            "max_landed_cost": active_optimizer.max_landed_cost,
            "capital_limit": active_optimizer.capital_limit,
        },
        "feasible_scenarios_count": len(feasible_rows),
        "scenario_count": len(scenario_table),
        "feasible_ratio": round(safe_divide(len(feasible_rows), len(scenario_table)), 4),
        "best_feasible_scenario": best_feasible_scenario,
        "ranked_feasible_scenarios": feasible_rows[:5],
        "infeasible_reason_mix": dict(infeasible_reasons),
        "optimizer_gate_result": optimizer_gate_result,
        "optimizer_confidence_level": score_level(
            best_feasible_scenario.get("optimizer_score", 0.0),
            high_threshold=0.72,
            medium_threshold=0.5,
        ),
    }
