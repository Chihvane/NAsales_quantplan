from __future__ import annotations

from .models import Part4StressRecord
from .stats_utils import safe_divide, score_level


def compute_part4_stress_suite(
    channel_rows: list[dict],
    stress_registry: list[Part4StressRecord],
) -> dict:
    if not channel_rows:
        return {}

    active_scenarios = [row for row in stress_registry if row.active_flag]
    if not active_scenarios:
        return {"scenario_count": 0, "scenario_rows": [], "robustness_score": 0.0}

    scenario_rows = []
    worst_margin = 1.0
    pass_count = 0
    baseline_profit = sum(row.get("contribution_profit", 0.0) for row in channel_rows)
    baseline_revenue = sum(row.get("revenue", 0.0) for row in channel_rows)
    baseline_margin_rate = safe_divide(baseline_profit, baseline_revenue)
    gate_flip_rows = []
    for scenario in active_scenarios:
        scoped_rows = [
            row for row in channel_rows
            if scenario.channel_scope in {"all", "", row["channel"], row["channel_family"]}
        ] or channel_rows

        stressed_profit = 0.0
        stressed_revenue = 0.0
        for row in scoped_rows:
            revenue = row.get("revenue", 0.0)
            landed_cost = row.get("landed_cost_total", 0.0)
            acquisition = row.get("acquisition_cost_total", 0.0)
            refunds = row.get("refund_and_return_total", 0.0)

            if scenario.shock_target == "landed_cost":
                landed_cost *= scenario.shock_multiplier
            elif scenario.shock_target == "acquisition_cost":
                acquisition *= scenario.shock_multiplier
            elif scenario.shock_target == "cac_slippage":
                acquisition *= scenario.shock_multiplier
            elif scenario.shock_target == "fee_jump":
                total_fee = (
                    row.get("channel_fees_total", 0.0)
                    + row.get("payment_cost_total", 0.0)
                    + row.get("fulfillment_cost_total", 0.0)
                ) * scenario.shock_multiplier
                landed_cost += 0.0
                acquisition += 0.0
                refunds += 0.0
                extra_fee = total_fee - (
                    row.get("channel_fees_total", 0.0)
                    + row.get("payment_cost_total", 0.0)
                    + row.get("fulfillment_cost_total", 0.0)
                )
                revenue += 0.0
                stressed_profit -= 0.0
            elif scenario.shock_target == "policy_jump":
                revenue *= max(0.0, 1 - (scenario.shock_multiplier - 1) * 0.25)
                refunds *= max(1.0, scenario.shock_multiplier)
            elif scenario.shock_target == "refund_and_return":
                refunds *= scenario.shock_multiplier
            elif scenario.shock_target == "turnover_penalty":
                inventory_penalty = max(row.get("inventory_days", 0.0) / 45.0, 0.0)
                acquisition += row.get("acquisition_cost_total", 0.0) * max(inventory_penalty - 1, 0.0) * (scenario.shock_multiplier - 1)
            elif scenario.shock_target == "revenue":
                revenue *= scenario.shock_multiplier

            total_cost = (
                landed_cost
                + row.get("channel_fees_total", 0.0)
                + row.get("fulfillment_cost_total", 0.0)
                + row.get("payment_cost_total", 0.0)
                + row.get("storage_cost_total", 0.0)
                + acquisition
                + refunds
            )
            if scenario.shock_target == "fee_jump":
                total_cost += extra_fee
            stressed_profit += revenue - total_cost
            stressed_revenue += revenue

        stressed_margin_rate = safe_divide(stressed_profit, stressed_revenue)
        scenario_pass = stressed_margin_rate >= 0
        gate_flip = scenario_pass != (baseline_margin_rate >= 0)
        if scenario_pass:
            pass_count += 1
        worst_margin = min(worst_margin, stressed_margin_rate)
        scenario_payload = {
            "scenario_id": scenario.scenario_id,
            "scenario_name": scenario.scenario_name,
            "shock_target": scenario.shock_target,
            "shock_multiplier": scenario.shock_multiplier,
            "severity": scenario.severity,
            "stressed_contribution_profit": round(stressed_profit, 2),
            "stressed_margin_rate": round(stressed_margin_rate, 4),
            "margin_delta": round(stressed_margin_rate - baseline_margin_rate, 4),
            "gate_result": "pass" if scenario_pass else "fail",
            "gate_flip": gate_flip,
        }
        scenario_rows.append(scenario_payload)
        if gate_flip:
            gate_flip_rows.append(
                {
                    "scenario_id": scenario.scenario_id,
                    "scenario_name": scenario.scenario_name,
                    "from": "pass" if baseline_margin_rate >= 0 else "fail",
                    "to": "pass" if scenario_pass else "fail",
                }
            )

    scenario_rows.sort(key=lambda row: row["stressed_margin_rate"])
    robustness_score = safe_divide(pass_count, len(active_scenarios))
    return {
        "scenario_count": len(active_scenarios),
        "scenario_rows": scenario_rows,
        "baseline_margin_rate": round(baseline_margin_rate, 4),
        "worst_case_margin_rate": round(worst_margin, 4),
        "robustness_score": round(robustness_score, 4),
        "robustness_level": score_level(robustness_score, high_threshold=0.75, medium_threshold=0.5),
        "optimizer_feasibility_report": {
            "pass_count": pass_count,
            "fail_count": len(active_scenarios) - pass_count,
            "pass_ratio": round(robustness_score, 4),
        },
        "gate_flip_report": {
            "baseline_gate_result": "pass" if baseline_margin_rate >= 0 else "fail",
            "flip_count": len(gate_flip_rows),
            "scenario_flips": gate_flip_rows,
        },
    }
