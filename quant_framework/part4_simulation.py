from __future__ import annotations

from random import Random

from .models import Part4Assumptions
from .stats_utils import percentile_band as _band


def _compute_profit(row: dict[str, float], factors: dict[str, float]) -> tuple[float, float]:
    revenue = row.get("revenue", 0.0) * factors["revenue"]
    landed_cost = row.get("landed_cost_total", 0.0) * factors["landed"]
    channel_fee = row.get("channel_fees_total", 0.0) * factors["fee"]
    fulfillment_cost = row.get("fulfillment_cost_total", 0.0) * factors["fulfillment"]
    payment_cost = row.get("payment_cost_total", 0.0) * factors["fee"]
    storage_cost = row.get("storage_cost_total", 0.0) * factors["storage"]
    acquisition_cost = row.get("acquisition_cost_total", 0.0) * factors["spend"]
    refund_cost = row.get("refund_and_return_total", 0.0) * factors["refund"]
    contribution_profit = (
        revenue
        - landed_cost
        - channel_fee
        - fulfillment_cost
        - payment_cost
        - storage_cost
        - acquisition_cost
        - refund_cost
    )
    cost_base = (
        landed_cost
        + channel_fee
        + fulfillment_cost
        + payment_cost
        + storage_cost
        + acquisition_cost
        + refund_cost
    )
    roi = contribution_profit / cost_base if cost_base else 0.0
    margin_rate = contribution_profit / revenue if revenue else 0.0
    return roi, margin_rate


def _build_sensitivity(best_row: dict[str, float]) -> list[dict[str, float | str]]:
    if not best_row:
        return []

    base_factors = {
        "revenue": 1.0,
        "landed": 1.0,
        "fee": 1.0,
        "fulfillment": 1.0,
        "storage": 1.0,
        "spend": 1.0,
        "refund": 1.0,
    }
    base_roi, base_margin = _compute_profit(best_row, base_factors)
    driver_rows = [
        ("revenue", 0.9, 1.06),
        ("landed", 1.1, 0.95),
        ("spend", 1.18, 0.9),
        ("refund", 1.3, 0.85),
        ("fee", 1.08, 0.96),
    ]
    sensitivity = []
    for driver, downside, upside in driver_rows:
        downside_factors = dict(base_factors)
        downside_factors[driver] = downside
        downside_roi, downside_margin = _compute_profit(best_row, downside_factors)

        upside_factors = dict(base_factors)
        upside_factors[driver] = upside
        upside_roi, upside_margin = _compute_profit(best_row, upside_factors)

        sensitivity.append(
            {
                "driver": driver,
                "base_roi": round(base_roi, 4),
                "base_margin_rate": round(base_margin, 4),
                "downside_roi": round(downside_roi, 4),
                "downside_margin_rate": round(downside_margin, 4),
                "downside_impact": round(downside_margin - base_margin, 4),
                "upside_roi": round(upside_roi, 4),
                "upside_margin_rate": round(upside_margin, 4),
                "upside_impact": round(upside_margin - base_margin, 4),
            }
        )
    sensitivity.sort(key=lambda row: abs(row["downside_impact"]), reverse=True)
    return sensitivity


def run_part4_roi_monte_carlo(
    channel_rows: list[dict],
    assumptions: Part4Assumptions,
    iterations: int = 1200,
    seed: int = 42,
) -> dict:
    if not channel_rows:
        return {}

    rng = Random(seed)
    channel_samples: dict[str, dict[str, list[float]]] = {}
    total_profit_samples: list[float] = []
    total_cost_samples: list[float] = []
    total_revenue_samples: list[float] = []

    for row in channel_rows:
        channel_samples[row["channel"]] = {
            "roi": [],
            "contribution_margin_rate": [],
            "contribution_profit": [],
        }

    for _ in range(iterations):
        total_profit = 0.0
        total_cost = 0.0
        total_revenue = 0.0
        for row in channel_rows:
            factors = {
                "revenue": rng.triangular(0.88, 1.12, 1.0),
                "landed": rng.triangular(0.95, 1.12, 1.02),
                "fee": rng.triangular(0.96, 1.08, 1.01),
                "fulfillment": rng.triangular(0.92, 1.12, 1.0),
                "storage": rng.triangular(0.85, 1.2, 1.0),
                "spend": rng.triangular(0.82, 1.25, 1.03),
                "refund": rng.triangular(0.75, 1.45, 1.05),
            }
            roi, margin_rate = _compute_profit(row, factors)
            revenue = row.get("revenue", 0.0) * factors["revenue"]
            cost_base = (
                row.get("landed_cost_total", 0.0) * factors["landed"]
                + row.get("channel_fees_total", 0.0) * factors["fee"]
                + row.get("fulfillment_cost_total", 0.0) * factors["fulfillment"]
                + row.get("payment_cost_total", 0.0) * factors["fee"]
                + row.get("storage_cost_total", 0.0) * factors["storage"]
                + row.get("acquisition_cost_total", 0.0) * factors["spend"]
                + row.get("refund_and_return_total", 0.0) * factors["refund"]
            )
            profit = revenue * margin_rate

            bucket = channel_samples[row["channel"]]
            bucket["roi"].append(roi)
            bucket["contribution_margin_rate"].append(margin_rate)
            bucket["contribution_profit"].append(profit)

            total_profit += profit
            total_cost += cost_base
            total_revenue += revenue

        total_profit_samples.append(total_profit)
        total_cost_samples.append(total_cost)
        total_revenue_samples.append(total_revenue)

    channel_payload = {}
    weighted_loss_probability_numerator = 0.0
    total_revenue_weight = sum(row.get("revenue", 0.0) for row in channel_rows) or 1.0
    for row in channel_rows:
        bucket = channel_samples[row["channel"]]
        loss_probability = sum(1 for value in bucket["contribution_profit"] if value < 0) / iterations
        weighted_loss_probability_numerator += loss_probability * row.get("revenue", 0.0)
        channel_payload[row["channel"]] = {
            "roi": _band(bucket["roi"]),
            "contribution_margin_rate": _band(bucket["contribution_margin_rate"]),
            "contribution_profit": _band(bucket["contribution_profit"]),
            "loss_probability": round(loss_probability, 4),
            "base_margin_rate": round(row.get("contribution_margin_rate", 0.0), 4),
            "base_roi": round(row.get("roi", 0.0), 4),
        }

    overall_roi = [
        profit / cost if cost else 0.0
        for profit, cost in zip(total_profit_samples, total_cost_samples)
    ]
    overall_margin = [
        profit / revenue if revenue else 0.0
        for profit, revenue in zip(total_profit_samples, total_revenue_samples)
    ]
    overall_loss_probability = sum(1 for value in total_profit_samples if value < 0) / iterations

    best_row = max(channel_rows, key=lambda row: row.get("contribution_margin_rate", 0.0))
    overall = {
        "roi": _band(overall_roi),
        "contribution_margin_rate": _band(overall_margin),
        "contribution_profit": _band(total_profit_samples),
        "loss_probability": round(overall_loss_probability, 4),
        "loss_probability_weighted_channels": round(
            weighted_loss_probability_numerator / total_revenue_weight,
            4,
        ),
        "target_payback_months": assumptions.target_payback_months,
    }

    return {
        "iterations": iterations,
        "seed": seed,
        "overall": overall,
        "channels": channel_payload,
        "sensitivity": _build_sensitivity(best_row),
    }
