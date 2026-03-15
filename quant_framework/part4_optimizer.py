from __future__ import annotations

from collections import Counter

from .models import Part4Assumptions, Part4OptimizerRecord
from .stats_utils import clip, safe_divide, score_level


def _default_optimizer(assumptions: Part4Assumptions) -> Part4OptimizerRecord:
    return Part4OptimizerRecord(
        optimizer_id="default_part4_optimizer",
        objective_name="maximize_margin_under_risk_budget",
        objective_type="constraint_rank",
        risk_measure="loss_probability",
        max_loss_probability=assumptions.max_loss_probability,
        min_contribution_margin_rate=assumptions.min_contribution_margin_rate,
        min_priority_score=0.1,
        max_payback_months=assumptions.target_payback_months,
        max_paid_share=0.75,
        capital_limit=250000.0,
        active_flag=True,
    )


def compute_part4_optimizer(
    channel_rows: list[dict],
    monte_carlo: dict,
    traffic_metrics: dict,
    channel_performance_metrics: dict,
    optimizer_registry: list[Part4OptimizerRecord],
    assumptions: Part4Assumptions,
) -> dict:
    if not channel_rows:
        return {}

    optimizer = next((row for row in optimizer_registry if row.active_flag), None) or _default_optimizer(assumptions)
    paid_share = traffic_metrics.get("paid_vs_owned", {}).get("paid", 0.0)
    monte_carlo_channels = monte_carlo.get("channels", {})
    performance_lookup = {
        row["channel"]: row for row in channel_performance_metrics.get("channel_rows", [])
    }
    infeasible_reasons = Counter()
    feasible_rows = []
    optimizer_runs = []

    for row in channel_rows:
        monte_carlo_row = monte_carlo_channels.get(row["channel"], {})
        loss_probability = monte_carlo_row.get("loss_probability", 0.0)
        capital_required = (
            row.get("landed_cost_total", 0.0)
            + row.get("acquisition_cost_total", 0.0)
            + row.get("storage_cost_total", 0.0)
        )
        performance_row = performance_lookup.get(row["channel"], {})
        expected_profit = monte_carlo_row.get("contribution_profit", {}).get("p50", row.get("contribution_profit", 0.0))
        lower_profit = monte_carlo_row.get("contribution_profit", {}).get("p10", row.get("contribution_profit", 0.0))
        profit_variance_proxy = max(expected_profit - lower_profit, 0.0)
        turnover_penalty_score = performance_row.get("turnover_penalty_score", 0.0)
        execution_friction_score = performance_row.get("execution_friction_score", 0.0)
        risk_adjusted_profit = (
            expected_profit
            - optimizer.objective_lambda * profit_variance_proxy
            - optimizer.turnover_penalty_lambda * turnover_penalty_score * max(expected_profit, 0.0)
            - execution_friction_score * max(expected_profit, 0.0) * 0.2
        )
        reasons = []
        if row.get("contribution_margin_rate", 0.0) < optimizer.min_contribution_margin_rate:
            reasons.append("margin_floor")
        if row.get("payback_period_months", 999.0) > optimizer.max_payback_months:
            reasons.append("payback_limit")
        if loss_probability > optimizer.max_loss_probability:
            reasons.append("loss_probability_limit")
        if paid_share > optimizer.max_paid_share and row.get("channel_family") == "dtc":
            reasons.append("paid_share_limit")
        if capital_required > optimizer.capital_limit:
            reasons.append("capital_limit")
        if execution_friction_score > 0.55:
            reasons.append("execution_friction_limit")

        priority_score = clip(
            row.get("contribution_margin_rate", 0.0) * 0.4
            + row.get("roi", 0.0) * 0.2
            + (1 - min(loss_probability / max(optimizer.max_loss_probability, 0.01), 1.0)) * 0.2
            + (1 - min(row.get("payback_period_months", 999.0) / max(optimizer.max_payback_months, 1), 1.0)) * 0.1
            + row.get("repeat_rate", 0.0) * 0.1,
            0.0,
            1.0,
        )
        if priority_score < optimizer.min_priority_score:
            reasons.append("priority_floor")

        optimizer_runs.append(
            {
                "channel": row["channel"],
                "objective_name": optimizer.objective_name,
                "objective_type": optimizer.objective_type,
                "expected_profit": round(expected_profit, 2),
                "profit_variance_proxy": round(profit_variance_proxy, 2),
                "risk_adjusted_profit": round(risk_adjusted_profit, 2),
                "turnover_penalty_score": round(turnover_penalty_score, 4),
                "execution_friction_score": round(execution_friction_score, 4),
                "capital_required_proxy": round(capital_required, 2),
                "feasible": not reasons,
                "infeasible_reasons": reasons,
                "priority_score": round(priority_score, 4),
            }
        )
        if reasons:
            infeasible_reasons.update(reasons)
            continue

        enriched = dict(row)
        enriched["capital_required_proxy"] = round(capital_required, 2)
        enriched["loss_probability"] = round(loss_probability, 4)
        enriched["optimizer_priority_score"] = round(priority_score, 4)
        enriched["expected_profit"] = round(expected_profit, 2)
        enriched["risk_adjusted_profit"] = round(risk_adjusted_profit, 2)
        enriched["execution_friction_score"] = round(execution_friction_score, 4)
        feasible_rows.append(enriched)

    feasible_rows.sort(
        key=lambda item: (
            item.get("risk_adjusted_profit", 0.0),
            item["optimizer_priority_score"],
            item.get("contribution_profit", 0.0),
        ),
        reverse=True,
    )
    capital_limit = max(optimizer.capital_limit, 1.0)
    allocation_denominator = sum(max(row.get("risk_adjusted_profit", 0.0), 0.0) for row in feasible_rows) or 1.0
    recommended_allocation = {}
    consumed_capital = 0.0
    for row in feasible_rows[:5]:
        proposed_weight = min(
            max(row.get("risk_adjusted_profit", 0.0), 0.0) / allocation_denominator,
            optimizer.max_single_channel_weight,
        )
        proposed_amount = round(proposed_weight * capital_limit, 2)
        proposed_amount = min(proposed_amount, round(capital_limit - consumed_capital, 2))
        if proposed_amount <= 0:
            continue
        recommended_allocation[row["channel"]] = proposed_amount
        consumed_capital += proposed_amount
        if consumed_capital >= capital_limit:
            break

    best_channel = feasible_rows[0] if feasible_rows else {}
    total_risk_adjusted_profit = sum(row.get("risk_adjusted_profit", 0.0) for row in feasible_rows)
    return {
        "optimizer_id": optimizer.optimizer_id,
        "objective_name": optimizer.objective_name,
        "objective_type": optimizer.objective_type,
        "feasible_channels_count": len(feasible_rows),
        "channel_count": len(channel_rows),
        "feasible_ratio": round(safe_divide(len(feasible_rows), len(channel_rows)), 4),
        "best_channel": best_channel,
        "ranked_channels": feasible_rows[:5],
        "recommended_capital_allocation": recommended_allocation,
        "optimal_budget_mix": {
            channel: round(safe_divide(amount, capital_limit), 4)
            for channel, amount in recommended_allocation.items()
        },
        "risk_adjusted_profit": round(total_risk_adjusted_profit, 2),
        "portfolio_constraints": {
            "capital_limit": round(capital_limit, 2),
            "max_loss_probability": round(optimizer.max_loss_probability, 4),
            "min_contribution_margin_rate": round(optimizer.min_contribution_margin_rate, 4),
            "max_payback_months": round(optimizer.max_payback_months, 2),
            "max_paid_share": round(optimizer.max_paid_share, 4),
            "max_single_channel_weight": round(optimizer.max_single_channel_weight, 4),
            "objective_lambda": round(optimizer.objective_lambda, 4),
            "turnover_penalty_lambda": round(optimizer.turnover_penalty_lambda, 4),
        },
        "capital_fit_status": "pass" if consumed_capital <= capital_limit else "fail",
        "risk_budget_fit_status": "pass" if feasible_rows else "fail",
        "optimizer_runs": optimizer_runs,
        "infeasible_reason_mix": dict(infeasible_reasons),
        "optimizer_gate_result": "pass" if feasible_rows else "fail",
        "optimizer_confidence_level": score_level(best_channel.get("optimizer_priority_score", 0.0)),
    }
