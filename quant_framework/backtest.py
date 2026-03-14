from __future__ import annotations

import csv
from math import prod
from pathlib import Path
from random import Random
from statistics import mean, pstdev
from datetime import datetime

from .io_utils import read_csv_rows, write_csv_rows, write_json
from .loaders import load_listing_snapshots, load_product_catalog, load_reviews, load_sold_transactions
from .models import Part2Assumptions, Part2Dataset
from .part2_metrics import (
    compute_attribute_landscape,
    compute_review_analytics,
    compute_sku_market_structure,
    compute_transaction_price_analysis,
)


PANEL_FIELDS = [
    "month",
    "category",
    "demand_index",
    "active_listings",
    "price_realization_rate",
    "channel_roas",
    "hhi",
    "revenue_index",
]

PART2_PANEL_FIELDS = [
    "month",
    "category",
    "top_sku_share",
    "sweet_spot_share",
    "whitespace_score",
    "negative_review_rate",
    "median_lifetime_days",
    "exit_risk",
    "discount_depth",
    "gmv_index",
]

PART3_PANEL_FIELDS = [
    "month",
    "scenario",
    "quote_confidence",
    "margin_rate",
    "compliance_readiness",
    "logistics_reliability",
    "cost_advantage",
    "scenario_confidence",
    "realized_margin_index",
]

PART4_PANEL_FIELDS = [
    "month",
    "channel",
    "contribution_margin_rate",
    "repeat_rate",
    "payback_efficiency",
    "inventory_health",
    "loss_resilience",
    "traffic_efficiency",
    "realized_profit_index",
]

PART5_PANEL_FIELDS = [
    "month",
    "channel",
    "operating_health",
    "growth_leverage",
    "margin_protection",
    "inventory_readiness",
    "incrementality",
    "alert_relief",
    "realized_operating_index",
]


def _month_sequence(start_year: int, start_month: int, periods: int) -> list[str]:
    months = []
    year = start_year
    month = start_month
    for _ in range(periods):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _month_key(value: str) -> str:
    return value[:7]


def _parse_category_bucket(category_path: str, depth: int = 1) -> str:
    if not category_path:
        return "Unclassified"
    cleaned = category_path.strip()
    cleaned = cleaned.strip("[]")
    parts = []
    if '","' in cleaned or '", "' in cleaned or '"' in cleaned:
        parts = [
            segment.strip().strip('"')
            for segment in cleaned.split(",")
            if segment.strip().strip('"')
        ]
    elif ">" in cleaned:
        parts = [segment.strip() for segment in cleaned.split(">") if segment.strip()]
    else:
        parts = [segment.strip() for segment in cleaned.split("/") if segment.strip()]
    if not parts:
        parts = [cleaned.strip('" ')]
    return " > ".join(parts[:depth])


def _parse_optional_date(value: str) -> datetime.date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S.%f", "%B %d, %Y"):
        try:
            return datetime.strptime(value[:26], fmt).date()
        except ValueError:
            continue
    return None


def _seasonality(category: str, month: int) -> float:
    if category == "portable_generators":
        return {1: 10, 2: 8, 8: 14, 9: 16, 12: 7}.get(month, 0)
    if category == "camping_gear":
        return {4: 7, 5: 12, 6: 16, 7: 18, 8: 13, 9: 6}.get(month, 0)
    if category == "edc":
        return {11: 5, 12: 7}.get(month, 0)
    if category == "cigar_accessories":
        return {11: 6, 12: 8}.get(month, 0)
    if category == "car_parts":
        return {3: 3, 4: 5, 10: 4}.get(month, 0)
    return 0


def _part2_seasonality(category: str, month: int) -> float:
    if category == "portable_generators":
        return {8: 0.032, 9: 0.044, 10: 0.018}.get(month, 0.0)
    if category == "camping_gear":
        return {4: 0.018, 5: 0.034, 6: 0.041, 7: 0.046, 8: 0.028}.get(month, 0.0)
    if category == "edc":
        return {11: 0.016, 12: 0.018}.get(month, 0.0)
    if category == "cigar_accessories":
        return {11: 0.021, 12: 0.026}.get(month, 0.0)
    if category == "car_parts":
        return {3: 0.016, 4: 0.014, 10: 0.01}.get(month, 0.0)
    return 0.0


def generate_demo_backtest_panel(seed: int = 42) -> list[dict[str, str]]:
    rng = Random(seed)
    months = _month_sequence(2024, 1, 24)
    category_configs = {
        "portable_generators": {"demand_base": 72, "trend": 1.0, "roas": 5.6, "realization": 0.89, "hhi": 2850, "listings": 510, "revenue": 118},
        "camping_gear": {"demand_base": 68, "trend": 0.7, "roas": 5.1, "realization": 0.87, "hhi": 1680, "listings": 640, "revenue": 112},
        "edc": {"demand_base": 61, "trend": 1.2, "roas": 4.9, "realization": 0.91, "hhi": 1540, "listings": 420, "revenue": 108},
        "cigar_accessories": {"demand_base": 54, "trend": 0.2, "roas": 4.2, "realization": 0.86, "hhi": 1950, "listings": 300, "revenue": 104},
        "car_parts": {"demand_base": 64, "trend": 0.5, "roas": 4.6, "realization": 0.9, "hhi": 2400, "listings": 560, "revenue": 110},
    }

    feature_map: dict[str, list[dict[str, float]]] = {category: [] for category in category_configs}
    panel_rows: list[dict[str, str]] = []

    for category, config in category_configs.items():
        revenue_index = float(config["revenue"])
        prior_demand = config["demand_base"]
        prior_listings = config["listings"]

        for idx, month_label in enumerate(months):
            month_number = int(month_label[-2:])
            demand_index = (
                config["demand_base"]
                + config["trend"] * idx
                + _seasonality(category, month_number)
                + rng.uniform(-2.0, 2.0)
            )
            demand_momentum = (demand_index - prior_demand) / max(prior_demand, 1)
            price_realization = min(
                0.96,
                max(
                    0.78,
                    config["realization"]
                    + 0.0018 * demand_momentum * 100
                    + rng.uniform(-0.01, 0.01),
                ),
            )
            channel_roas = max(
                2.2,
                config["roas"]
                + 0.035 * demand_momentum * 100
                + _seasonality(category, month_number) * 0.03
                + rng.uniform(-0.2, 0.2),
            )
            active_listings = max(
                90,
                int(
                    config["listings"]
                    + idx * 6
                    + demand_index * 0.55
                    + rng.uniform(-15, 15)
                ),
            )
            supply_pressure = (active_listings - prior_listings) / max(prior_listings, 1)
            hhi = max(
                1100,
                min(
                    3200,
                    config["hhi"]
                    - demand_momentum * 120
                    + supply_pressure * 180
                    + rng.uniform(-45, 45),
                ),
            )

            if idx > 0:
                growth = (
                    0.012
                    + 0.34 * demand_momentum
                    + 0.018 * (channel_roas - config["roas"])
                    + 0.22 * (price_realization - 0.85)
                    - 0.08 * supply_pressure
                    - 0.000045 * (hhi - 1800)
                    + rng.uniform(-0.018, 0.018)
                )
                growth = max(-0.12, min(0.18, growth))
                revenue_index *= 1 + growth

            row = {
                "month": month_label,
                "category": category,
                "demand_index": f"{demand_index:.2f}",
                "active_listings": str(active_listings),
                "price_realization_rate": f"{price_realization:.4f}",
                "channel_roas": f"{channel_roas:.4f}",
                "hhi": f"{hhi:.2f}",
                "revenue_index": f"{revenue_index:.2f}",
            }
            panel_rows.append(row)
            feature_map[category].append(
                {
                    "demand_index": demand_index,
                    "active_listings": float(active_listings),
                    "price_realization_rate": price_realization,
                    "channel_roas": channel_roas,
                    "hhi": hhi,
                    "revenue_index": revenue_index,
                }
            )
            prior_demand = demand_index
            prior_listings = active_listings

    return sorted(panel_rows, key=lambda item: (item["month"], item["category"]))


def generate_part2_demo_backtest_panel(seed: int = 42) -> list[dict[str, str]]:
    rng = Random(seed)
    months = _month_sequence(2024, 1, 24)
    category_configs = {
        "portable_generators": {
            "top_sku_share": 0.56,
            "sweet_spot_share": 0.38,
            "whitespace_score": 0.12,
            "negative_review_rate": 0.19,
            "median_lifetime_days": 96,
            "exit_risk": 0.18,
            "discount_depth": 0.09,
            "gmv": 122,
        },
        "camping_gear": {
            "top_sku_share": 0.44,
            "sweet_spot_share": 0.33,
            "whitespace_score": 0.09,
            "negative_review_rate": 0.16,
            "median_lifetime_days": 82,
            "exit_risk": 0.22,
            "discount_depth": 0.11,
            "gmv": 116,
        },
        "edc": {
            "top_sku_share": 0.48,
            "sweet_spot_share": 0.35,
            "whitespace_score": 0.11,
            "negative_review_rate": 0.14,
            "median_lifetime_days": 88,
            "exit_risk": 0.2,
            "discount_depth": 0.08,
            "gmv": 114,
        },
        "cigar_accessories": {
            "top_sku_share": 0.61,
            "sweet_spot_share": 0.28,
            "whitespace_score": 0.06,
            "negative_review_rate": 0.22,
            "median_lifetime_days": 74,
            "exit_risk": 0.24,
            "discount_depth": 0.12,
            "gmv": 108,
        },
        "car_parts": {
            "top_sku_share": 0.53,
            "sweet_spot_share": 0.31,
            "whitespace_score": 0.08,
            "negative_review_rate": 0.17,
            "median_lifetime_days": 86,
            "exit_risk": 0.19,
            "discount_depth": 0.1,
            "gmv": 111,
        },
    }

    panel_rows: list[dict[str, str]] = []
    for category, config in category_configs.items():
        gmv_index = float(config["gmv"])
        prior_whitespace = config["whitespace_score"]
        for idx, month_label in enumerate(months):
            month_number = int(month_label[-2:])
            top_sku_share = min(
                0.78,
                max(
                    0.32,
                    config["top_sku_share"]
                    + rng.uniform(-0.025, 0.025)
                    - idx * 0.0008,
                ),
            )
            sweet_spot_share = min(
                0.58,
                max(
                    0.18,
                    config["sweet_spot_share"]
                    + _part2_seasonality(category, month_number)
                    + rng.uniform(-0.018, 0.018),
                ),
            )
            whitespace_score = min(
                0.2,
                max(
                    0.02,
                    config["whitespace_score"]
                    + idx * 0.0015
                    + rng.uniform(-0.012, 0.012),
                ),
            )
            negative_review_rate = min(
                0.42,
                max(
                    0.08,
                    config["negative_review_rate"]
                    + 0.12 * max(top_sku_share - config["top_sku_share"], 0)
                    - 0.1 * max(whitespace_score - prior_whitespace, 0)
                    + rng.uniform(-0.015, 0.015),
                ),
            )
            median_lifetime_days = min(
                140,
                max(
                    28,
                    config["median_lifetime_days"]
                    + idx * 1.2
                    - 20 * max(negative_review_rate - config["negative_review_rate"], 0)
                    + rng.uniform(-5, 5),
                ),
            )
            exit_risk = min(
                0.45,
                max(
                    0.08,
                    config["exit_risk"]
                    + 0.18 * max(negative_review_rate - config["negative_review_rate"], 0)
                    - 0.12 * max(median_lifetime_days - config["median_lifetime_days"], 0) / 100
                    + rng.uniform(-0.01, 0.01),
                ),
            )
            discount_depth = min(
                0.24,
                max(
                    0.04,
                    config["discount_depth"]
                    + 0.05 * max(top_sku_share - 0.5, 0)
                    - 0.04 * max(sweet_spot_share - config["sweet_spot_share"], 0)
                    + rng.uniform(-0.01, 0.01),
                ),
            )

            if idx > 0:
                growth = (
                    0.008
                    + 0.14 * (sweet_spot_share - 0.28)
                    + 0.26 * whitespace_score
                    - 0.12 * negative_review_rate
                    + 0.00055 * (median_lifetime_days - 70)
                    - 0.08 * exit_risk
                    - 0.05 * max(top_sku_share - 0.55, 0)
                    - 0.02 * max(discount_depth - 0.14, 0)
                    + _part2_seasonality(category, month_number)
                    + rng.uniform(-0.012, 0.012)
                )
                growth = max(-0.07, min(0.11, growth))
                gmv_index *= 1 + growth

            panel_rows.append(
                {
                    "month": month_label,
                    "category": category,
                    "top_sku_share": f"{top_sku_share:.4f}",
                    "sweet_spot_share": f"{sweet_spot_share:.4f}",
                    "whitespace_score": f"{whitespace_score:.4f}",
                    "negative_review_rate": f"{negative_review_rate:.4f}",
                    "median_lifetime_days": f"{median_lifetime_days:.2f}",
                    "exit_risk": f"{exit_risk:.4f}",
                    "discount_depth": f"{discount_depth:.4f}",
                    "gmv_index": f"{gmv_index:.2f}",
                }
            )
            prior_whitespace = whitespace_score

    return sorted(panel_rows, key=lambda item: (item["month"], item["category"]))


def generate_part3_demo_backtest_panel(seed: int = 42) -> list[dict[str, str]]:
    rng = Random(seed)
    months = _month_sequence(2024, 1, 24)
    scenario_configs = {
        "S001_FOB_SEA": {
            "quote_confidence": 0.82,
            "margin_rate": 0.232,
            "compliance_readiness": 0.78,
            "logistics_reliability": 0.73,
            "cost_advantage": 0.18,
            "scenario_confidence": 0.81,
            "margin_index": 118,
        },
        "S002_DDP_FAST": {
            "quote_confidence": 0.76,
            "margin_rate": 0.214,
            "compliance_readiness": 0.74,
            "logistics_reliability": 0.79,
            "cost_advantage": 0.11,
            "scenario_confidence": 0.69,
            "margin_index": 114,
        },
        "S003_EXW_SEA": {
            "quote_confidence": 0.67,
            "margin_rate": 0.196,
            "compliance_readiness": 0.66,
            "logistics_reliability": 0.68,
            "cost_advantage": 0.08,
            "scenario_confidence": 0.61,
            "margin_index": 109,
        },
        "S004_FOB_AIR": {
            "quote_confidence": 0.74,
            "margin_rate": 0.181,
            "compliance_readiness": 0.71,
            "logistics_reliability": 0.84,
            "cost_advantage": 0.03,
            "scenario_confidence": 0.72,
            "margin_index": 105,
        },
    }

    panel_rows: list[dict[str, str]] = []
    for scenario, config in scenario_configs.items():
        margin_index = float(config["margin_index"])
        for idx, month_label in enumerate(months):
            month_number = int(month_label[-2:])
            quote_confidence = _clamp(config["quote_confidence"] + rng.uniform(-0.03, 0.03), 0.45, 0.95)
            margin_rate = _clamp(
                config["margin_rate"]
                + idx * 0.0012
                + (0.006 if month_number in {3, 4, 9, 10} else 0.0)
                + rng.uniform(-0.008, 0.008),
                0.08,
                0.34,
            )
            compliance_readiness = _clamp(
                config["compliance_readiness"] + idx * 0.002 + rng.uniform(-0.025, 0.025),
                0.4,
                0.96,
            )
            logistics_reliability = _clamp(
                config["logistics_reliability"]
                + (0.02 if month_number in {5, 6, 7} else 0.0)
                - (0.03 if month_number in {11, 12} else 0.0)
                + rng.uniform(-0.03, 0.03),
                0.42,
                0.96,
            )
            cost_advantage = _clamp(
                config["cost_advantage"] + idx * 0.001 + rng.uniform(-0.02, 0.02),
                -0.08,
                0.28,
            )
            scenario_confidence = _clamp(
                config["scenario_confidence"]
                + 0.4 * (quote_confidence - config["quote_confidence"])
                + 0.3 * (compliance_readiness - config["compliance_readiness"])
                + rng.uniform(-0.015, 0.015),
                0.4,
                0.95,
            )

            if idx > 0:
                growth = (
                    0.006
                    + 0.34 * (margin_rate - 0.18)
                    + 0.16 * (quote_confidence - 0.68)
                    + 0.18 * (compliance_readiness - 0.65)
                    + 0.12 * (logistics_reliability - 0.68)
                    + 0.20 * cost_advantage
                    + 0.10 * (scenario_confidence - 0.65)
                    + rng.uniform(-0.015, 0.015)
                )
                growth = _clamp(growth, -0.08, 0.14)
                margin_index *= 1 + growth

            panel_rows.append(
                {
                    "month": month_label,
                    "scenario": scenario,
                    "quote_confidence": f"{quote_confidence:.4f}",
                    "margin_rate": f"{margin_rate:.4f}",
                    "compliance_readiness": f"{compliance_readiness:.4f}",
                    "logistics_reliability": f"{logistics_reliability:.4f}",
                    "cost_advantage": f"{cost_advantage:.4f}",
                    "scenario_confidence": f"{scenario_confidence:.4f}",
                    "realized_margin_index": f"{margin_index:.2f}",
                }
            )

    return sorted(panel_rows, key=lambda item: (item["month"], item["scenario"]))


def generate_part4_demo_backtest_panel(seed: int = 42) -> list[dict[str, str]]:
    rng = Random(seed)
    months = _month_sequence(2024, 1, 24)
    channel_configs = {
        "DTC": {
            "contribution_margin_rate": 0.17,
            "repeat_rate": 0.24,
            "payback_efficiency": 0.68,
            "inventory_health": 0.74,
            "loss_resilience": 0.76,
            "traffic_efficiency": 0.63,
            "profit_index": 112,
        },
        "Amazon": {
            "contribution_margin_rate": 0.16,
            "repeat_rate": 0.14,
            "payback_efficiency": 0.62,
            "inventory_health": 0.78,
            "loss_resilience": 0.72,
            "traffic_efficiency": 0.69,
            "profit_index": 118,
        },
        "TikTok Shop": {
            "contribution_margin_rate": 0.145,
            "repeat_rate": 0.11,
            "payback_efficiency": 0.72,
            "inventory_health": 0.69,
            "loss_resilience": 0.65,
            "traffic_efficiency": 0.76,
            "profit_index": 110,
        },
        "Walmart": {
            "contribution_margin_rate": 0.152,
            "repeat_rate": 0.13,
            "payback_efficiency": 0.64,
            "inventory_health": 0.73,
            "loss_resilience": 0.71,
            "traffic_efficiency": 0.58,
            "profit_index": 106,
        },
        "B2B": {
            "contribution_margin_rate": 0.19,
            "repeat_rate": 0.28,
            "payback_efficiency": 0.81,
            "inventory_health": 0.71,
            "loss_resilience": 0.83,
            "traffic_efficiency": 0.44,
            "profit_index": 115,
        },
    }
    panel_rows: list[dict[str, str]] = []
    for channel, config in channel_configs.items():
        profit_index = float(config["profit_index"])
        for idx, month_label in enumerate(months):
            month_number = int(month_label[-2:])
            contribution_margin_rate = _clamp(
                config["contribution_margin_rate"] + idx * 0.001 + rng.uniform(-0.01, 0.01),
                0.06,
                0.32,
            )
            repeat_rate = _clamp(
                config["repeat_rate"] + idx * 0.0015 + rng.uniform(-0.015, 0.015),
                0.04,
                0.42,
            )
            payback_efficiency = _clamp(
                config["payback_efficiency"] + (0.03 if month_number in {11, 12} else 0.0) + rng.uniform(-0.03, 0.03),
                0.2,
                0.95,
            )
            inventory_health = _clamp(
                config["inventory_health"] - (0.03 if month_number in {8, 9} else 0.0) + rng.uniform(-0.03, 0.03),
                0.3,
                0.95,
            )
            loss_resilience = _clamp(
                config["loss_resilience"] + 0.3 * (contribution_margin_rate - config["contribution_margin_rate"]) + rng.uniform(-0.02, 0.02),
                0.35,
                0.95,
            )
            traffic_efficiency = _clamp(
                config["traffic_efficiency"] + (0.04 if month_number in {5, 6, 7} and channel in {"DTC", "TikTok Shop"} else 0.0) + rng.uniform(-0.04, 0.04),
                0.2,
                0.95,
            )

            if idx > 0:
                growth = (
                    0.007
                    + 0.24 * (contribution_margin_rate - 0.12)
                    + 0.15 * (repeat_rate - 0.12)
                    + 0.16 * (payback_efficiency - 0.55)
                    + 0.14 * (inventory_health - 0.62)
                    + 0.18 * (loss_resilience - 0.6)
                    + 0.12 * (traffic_efficiency - 0.5)
                    + rng.uniform(-0.015, 0.015)
                )
                growth = _clamp(growth, -0.06, 0.12)
                profit_index *= 1 + growth

            panel_rows.append(
                {
                    "month": month_label,
                    "channel": channel,
                    "contribution_margin_rate": f"{contribution_margin_rate:.4f}",
                    "repeat_rate": f"{repeat_rate:.4f}",
                    "payback_efficiency": f"{payback_efficiency:.4f}",
                    "inventory_health": f"{inventory_health:.4f}",
                    "loss_resilience": f"{loss_resilience:.4f}",
                    "traffic_efficiency": f"{traffic_efficiency:.4f}",
                    "realized_profit_index": f"{profit_index:.2f}",
                }
            )
    return sorted(panel_rows, key=lambda item: (item["month"], item["channel"]))


def generate_part5_demo_backtest_panel(seed: int = 42) -> list[dict[str, str]]:
    rng = Random(seed)
    months = _month_sequence(2024, 1, 24)
    channel_configs = {
        "DTC": {
            "operating_health": 0.69,
            "growth_leverage": 0.66,
            "margin_protection": 0.72,
            "inventory_readiness": 0.74,
            "incrementality": 0.67,
            "alert_relief": 0.63,
            "operating_index": 113,
        },
        "Amazon": {
            "operating_health": 0.71,
            "growth_leverage": 0.59,
            "margin_protection": 0.75,
            "inventory_readiness": 0.78,
            "incrementality": 0.57,
            "alert_relief": 0.68,
            "operating_index": 116,
        },
        "TikTok Shop": {
            "operating_health": 0.61,
            "growth_leverage": 0.73,
            "margin_protection": 0.63,
            "inventory_readiness": 0.66,
            "incrementality": 0.76,
            "alert_relief": 0.54,
            "operating_index": 109,
        },
        "Walmart": {
            "operating_health": 0.64,
            "growth_leverage": 0.56,
            "margin_protection": 0.69,
            "inventory_readiness": 0.72,
            "incrementality": 0.61,
            "alert_relief": 0.67,
            "operating_index": 105,
        },
    }
    panel_rows: list[dict[str, str]] = []
    for channel, config in channel_configs.items():
        operating_index = float(config["operating_index"])
        for idx, month_label in enumerate(months):
            month_number = int(month_label[-2:])
            operating_health = _clamp(config["operating_health"] + idx * 0.001 + rng.uniform(-0.025, 0.025), 0.3, 0.95)
            growth_leverage = _clamp(
                config["growth_leverage"]
                + (0.03 if month_number in {4, 5, 11} else 0.0)
                + rng.uniform(-0.03, 0.03),
                0.2,
                0.95,
            )
            margin_protection = _clamp(config["margin_protection"] + rng.uniform(-0.03, 0.03), 0.25, 0.95)
            inventory_readiness = _clamp(
                config["inventory_readiness"] - (0.03 if month_number in {8, 9} else 0.0) + rng.uniform(-0.03, 0.03),
                0.2,
                0.95,
            )
            incrementality = _clamp(config["incrementality"] + idx * 0.002 + rng.uniform(-0.025, 0.025), 0.1, 0.95)
            alert_relief = _clamp(config["alert_relief"] + rng.uniform(-0.04, 0.04), 0.1, 0.95)

            if idx > 0:
                growth = (
                    0.005
                    + 0.22 * (operating_health - 0.55)
                    + 0.17 * (growth_leverage - 0.55)
                    + 0.16 * (margin_protection - 0.6)
                    + 0.13 * (inventory_readiness - 0.6)
                    + 0.20 * (incrementality - 0.55)
                    + 0.12 * (alert_relief - 0.5)
                    + rng.uniform(-0.014, 0.014)
                )
                growth = _clamp(growth, -0.07, 0.13)
                operating_index *= 1 + growth

            panel_rows.append(
                {
                    "month": month_label,
                    "channel": channel,
                    "operating_health": f"{operating_health:.4f}",
                    "growth_leverage": f"{growth_leverage:.4f}",
                    "margin_protection": f"{margin_protection:.4f}",
                    "inventory_readiness": f"{inventory_readiness:.4f}",
                    "incrementality": f"{incrementality:.4f}",
                    "alert_relief": f"{alert_relief:.4f}",
                    "realized_operating_index": f"{operating_index:.2f}",
                }
            )
    return sorted(panel_rows, key=lambda item: (item["month"], item["channel"]))


def write_demo_backtest_panel(output_csv: str | Path, seed: int = 42) -> Path:
    rows = generate_demo_backtest_panel(seed=seed)
    write_csv_rows(output_csv, PANEL_FIELDS, rows)
    return Path(output_csv)


def write_demo_part2_backtest_panel(output_csv: str | Path, seed: int = 42) -> Path:
    rows = generate_part2_demo_backtest_panel(seed=seed)
    write_csv_rows(output_csv, PART2_PANEL_FIELDS, rows)
    return Path(output_csv)


def write_demo_part3_backtest_panel(output_csv: str | Path, seed: int = 42) -> Path:
    rows = generate_part3_demo_backtest_panel(seed=seed)
    write_csv_rows(output_csv, PART3_PANEL_FIELDS, rows)
    return Path(output_csv)


def write_demo_part4_backtest_panel(output_csv: str | Path, seed: int = 42) -> Path:
    rows = generate_part4_demo_backtest_panel(seed=seed)
    write_csv_rows(output_csv, PART4_PANEL_FIELDS, rows)
    return Path(output_csv)


def write_demo_part5_backtest_panel(output_csv: str | Path, seed: int = 42) -> Path:
    rows = generate_part5_demo_backtest_panel(seed=seed)
    write_csv_rows(output_csv, PART5_PANEL_FIELDS, rows)
    return Path(output_csv)


def load_backtest_panel(path: str | Path) -> list[dict[str, float | str]]:
    rows = read_csv_rows(path)
    parsed_rows = []
    for row in rows:
        parsed_rows.append(
            {
                "month": row["month"],
                "category": row["category"],
                "demand_index": float(row["demand_index"]),
                "active_listings": int(row["active_listings"]),
                "price_realization_rate": float(row["price_realization_rate"]),
                "channel_roas": float(row["channel_roas"]),
                "hhi": float(row["hhi"]),
                "revenue_index": float(row["revenue_index"]),
            }
        )
    return parsed_rows


def load_part2_backtest_panel(path: str | Path) -> list[dict[str, float | str]]:
    rows = read_csv_rows(path)
    parsed_rows = []
    for row in rows:
        parsed_rows.append(
            {
                "month": row["month"],
                "category": row["category"],
                "top_sku_share": float(row["top_sku_share"]),
                "sweet_spot_share": float(row["sweet_spot_share"]),
                "whitespace_score": float(row["whitespace_score"]),
                "negative_review_rate": float(row["negative_review_rate"]),
                "median_lifetime_days": float(row["median_lifetime_days"]),
                "exit_risk": float(row["exit_risk"]),
                "discount_depth": float(row["discount_depth"]),
                "gmv_index": float(row["gmv_index"]),
            }
        )
    return parsed_rows


def load_part3_backtest_panel(path: str | Path) -> list[dict[str, float | str]]:
    rows = read_csv_rows(path)
    return [
        {
            "month": row["month"],
            "scenario": row["scenario"],
            "quote_confidence": float(row["quote_confidence"]),
            "margin_rate": float(row["margin_rate"]),
            "compliance_readiness": float(row["compliance_readiness"]),
            "logistics_reliability": float(row["logistics_reliability"]),
            "cost_advantage": float(row["cost_advantage"]),
            "scenario_confidence": float(row["scenario_confidence"]),
            "realized_margin_index": float(row["realized_margin_index"]),
        }
        for row in rows
    ]


def load_part4_backtest_panel(path: str | Path) -> list[dict[str, float | str]]:
    rows = read_csv_rows(path)
    return [
        {
            "month": row["month"],
            "channel": row["channel"],
            "contribution_margin_rate": float(row["contribution_margin_rate"]),
            "repeat_rate": float(row["repeat_rate"]),
            "payback_efficiency": float(row["payback_efficiency"]),
            "inventory_health": float(row["inventory_health"]),
            "loss_resilience": float(row["loss_resilience"]),
            "traffic_efficiency": float(row["traffic_efficiency"]),
            "realized_profit_index": float(row["realized_profit_index"]),
        }
        for row in rows
    ]


def load_part5_backtest_panel(path: str | Path) -> list[dict[str, float | str]]:
    rows = read_csv_rows(path)
    return [
        {
            "month": row["month"],
            "channel": row["channel"],
            "operating_health": float(row["operating_health"]),
            "growth_leverage": float(row["growth_leverage"]),
            "margin_protection": float(row["margin_protection"]),
            "inventory_readiness": float(row["inventory_readiness"]),
            "incrementality": float(row["incrementality"]),
            "alert_relief": float(row["alert_relief"]),
            "realized_operating_index": float(row["realized_operating_index"]),
        }
        for row in rows
    ]


def build_part2_backtest_panel_from_dataset(
    dataset: Part2Dataset,
    category_depth: int = 1,
    min_categories_per_month: int = 3,
) -> list[dict[str, str]]:
    product_lookup = {record.canonical_sku: record for record in dataset.product_catalog}
    category_by_sku = {
        sku: _parse_category_bucket(record.category_path, depth=category_depth)
        for sku, record in product_lookup.items()
    }

    months = sorted({_month_key(record.captured_at) for record in dataset.listing_snapshots if record.captured_at})
    panel_rows: list[dict[str, str]] = []

    for month in months:
        listing_subset = [record for record in dataset.listing_snapshots if _month_key(record.captured_at) == month]
        sold_subset = [record for record in dataset.sold_transactions if _month_key(record.sold_at) == month]
        review_subset = [record for record in dataset.reviews if _month_key(record.review_date) == month]

        listings_by_category: dict[str, list] = {}
        for record in listing_subset:
            category = category_by_sku.get(record.canonical_sku, "Unclassified")
            listings_by_category.setdefault(category, []).append(record)

        valid_categories = [
            category
            for category, records in listings_by_category.items()
            if len(records) >= 2
        ]
        if len(valid_categories) < min_categories_per_month:
            continue

        for category in valid_categories:
            category_skus = {record.canonical_sku for record in listings_by_category[category]}
            category_listings = listings_by_category[category]
            category_sold = [record for record in sold_subset if record.canonical_sku in category_skus]
            category_reviews = [record for record in review_subset if record.canonical_sku in category_skus]
            category_products = [record for record in dataset.product_catalog if record.canonical_sku in category_skus]
            if not category_sold:
                continue

            market_structure = compute_sku_market_structure(
                category_listings,
                category_sold,
                Part2Assumptions(leaderboard_size=5),
            )
            price_analysis = compute_transaction_price_analysis(
                category_listings,
                category_sold,
                Part2Assumptions(leaderboard_size=5),
            )
            attribute_landscape = compute_attribute_landscape(
                category_products,
                category_sold,
                Part2Assumptions(leaderboard_size=5),
            )
            review_analytics = compute_review_analytics(
                category_reviews,
                Part2Assumptions(leaderboard_size=5),
            )

            age_days = []
            for sku in category_skus:
                product = product_lookup.get(sku)
                current_listing = next((record for record in category_listings if record.canonical_sku == sku), None)
                first_available = _parse_optional_date(
                    product.first_available_date if product else ""
                )
                captured_date = _parse_optional_date(current_listing.captured_at if current_listing else "")
                if first_available and captured_date:
                    age_days.append((captured_date - first_available).days)

            discount_rates = []
            for record in category_listings:
                list_price = float(record.list_price or 0)
                sale_price = float(record.sale_price or 0)
                if list_price > 0:
                    discount_rates.append(max(0.0, (list_price - sale_price) / list_price))

            whitespace_score = 0.0
            if attribute_landscape.get("whitespace_opportunities"):
                whitespace_score = max(
                    item.get("outperformance", 0.0)
                    for item in attribute_landscape["whitespace_opportunities"]
                )
            elif attribute_landscape.get("top_attributes"):
                whitespace_score = max(
                    item.get("outperformance", 0.0)
                    for item in attribute_landscape["top_attributes"]
                )

            exit_risk = sum(1 for record in category_listings if not record.active_flag) / len(category_listings)
            sweet_spot_share = price_analysis.get("sweet_spot_band", {}).get("share", 0.0)
            negative_review_rate = review_analytics.get("sentiment_mix", {}).get("negative", 0.0)
            median_lifetime_days = min(mean(age_days), 3650.0) if age_days else 30.0
            discount_depth = mean(discount_rates) if discount_rates else 0.0
            gmv_index = market_structure.get("total_gmv", 0.0) / max(len(category_listings), 1)

            panel_rows.append(
                {
                    "month": month,
                    "category": category,
                    "top_sku_share": f"{market_structure.get('top_sku_share', 0.0):.4f}",
                    "sweet_spot_share": f"{sweet_spot_share:.4f}",
                    "whitespace_score": f"{whitespace_score:.4f}",
                    "negative_review_rate": f"{negative_review_rate:.4f}",
                    "median_lifetime_days": f"{median_lifetime_days:.2f}",
                    "exit_risk": f"{exit_risk:.4f}",
                    "discount_depth": f"{discount_depth:.4f}",
                    "gmv_index": f"{gmv_index:.2f}",
                }
            )

    return sorted(panel_rows, key=lambda item: (item["month"], item["category"]))


def build_part2_backtest_panel_from_directory(
    data_dir: str | Path,
    output_csv: str | Path,
    category_depth: int = 1,
    min_categories_per_month: int = 3,
) -> Path:
    data_dir = Path(data_dir)
    dataset = Part2Dataset(
        listing_snapshots=load_listing_snapshots(data_dir / "listing_snapshots.csv"),
        sold_transactions=load_sold_transactions(data_dir / "sold_transactions.csv"),
        product_catalog=load_product_catalog(data_dir / "product_catalog.csv"),
        reviews=load_reviews(data_dir / "reviews.csv"),
    )
    panel_rows = build_part2_backtest_panel_from_dataset(
        dataset,
        category_depth=category_depth,
        min_categories_per_month=min_categories_per_month,
    )
    write_csv_rows(output_csv, PART2_PANEL_FIELDS, panel_rows)
    return Path(output_csv)


def _zscore_map(values: dict[str, float]) -> dict[str, float]:
    data = list(values.values())
    if not data:
        return {}
    avg = mean(data)
    sigma = pstdev(data)
    if sigma == 0:
        return {key: 0.0 for key in values}
    return {key: (value - avg) / sigma for key, value in values.items()}


def _cumulative_return(returns: list[float]) -> float:
    if not returns:
        return 0.0
    return prod(1 + value for value in returns) - 1


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def run_market_opportunity_backtest(
    panel_rows: list[dict[str, float | str]],
    lookback: int = 3,
    top_n: int = 2,
    weights: dict[str, float] | None = None,
) -> dict:
    weights = weights or {
        "demand_momentum": 0.35,
        "channel_roas": 0.25,
        "price_realization_rate": 0.20,
        "supply_pressure": -0.10,
        "hhi": -0.10,
    }
    rows_by_category: dict[str, list[dict[str, float | str]]] = {}
    for row in panel_rows:
        rows_by_category.setdefault(str(row["category"]), []).append(row)

    for rows in rows_by_category.values():
        rows.sort(key=lambda item: str(item["month"]))

    months = sorted({str(row["month"]) for row in panel_rows})
    monthly_records = []

    for month_index in range(lookback, len(months) - 1):
        current_month = months[month_index]
        next_month = months[month_index + 1]

        demand_momentum: dict[str, float] = {}
        supply_pressure: dict[str, float] = {}
        price_realization: dict[str, float] = {}
        channel_roas: dict[str, float] = {}
        concentration_penalty: dict[str, float] = {}
        next_returns: dict[str, float] = {}

        for category, rows in rows_by_category.items():
            current_row = next((row for row in rows if row["month"] == current_month), None)
            next_row = next((row for row in rows if row["month"] == next_month), None)
            history = [row for row in rows if row["month"] < current_month][-lookback:]
            if not current_row or not next_row or len(history) < lookback:
                continue

            demand_baseline = mean(float(row["demand_index"]) for row in history)
            listings_baseline = mean(float(row["active_listings"]) for row in history)

            demand_momentum[category] = (
                float(current_row["demand_index"]) / max(demand_baseline, 1e-9) - 1
            )
            supply_pressure[category] = (
                float(current_row["active_listings"]) / max(listings_baseline, 1e-9) - 1
            )
            price_realization[category] = float(current_row["price_realization_rate"])
            channel_roas[category] = float(current_row["channel_roas"])
            concentration_penalty[category] = float(current_row["hhi"])
            next_returns[category] = (
                float(next_row["revenue_index"]) / max(float(current_row["revenue_index"]), 1e-9) - 1
            )

        if len(next_returns) <= top_n:
            continue

        demand_z = _zscore_map(demand_momentum)
        supply_z = _zscore_map(supply_pressure)
        realization_z = _zscore_map(price_realization)
        roas_z = _zscore_map(channel_roas)
        concentration_z = _zscore_map(concentration_penalty)

        scores = {}
        for category in next_returns:
            scores[category] = (
                weights["demand_momentum"] * demand_z[category]
                + weights["channel_roas"] * roas_z[category]
                + weights["price_realization_rate"] * realization_z[category]
                + weights["supply_pressure"] * supply_z[category]
                + weights["hhi"] * concentration_z[category]
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = ranked[:top_n]
        selected_categories = [category for category, _ in selected]
        strategy_return = mean(next_returns[category] for category in selected_categories)
        benchmark_return = mean(next_returns.values())
        monthly_records.append(
            {
                "month": current_month,
                "next_month": next_month,
                "selected_categories": selected_categories,
                "selected_scores": {category: round(score, 4) for category, score in selected},
                "strategy_return": round(strategy_return, 4),
                "benchmark_return": round(benchmark_return, 4),
                "excess_return": round(strategy_return - benchmark_return, 4),
            }
        )

    strategy_returns = [record["strategy_return"] for record in monthly_records]
    benchmark_returns = [record["benchmark_return"] for record in monthly_records]
    excess_returns = [record["excess_return"] for record in monthly_records]

    return {
        "config": {
            "lookback_months": lookback,
            "top_n": top_n,
            "signal_weights": weights,
        },
        "summary": {
            "periods": len(monthly_records),
            "avg_strategy_return": round(mean(strategy_returns), 4) if strategy_returns else 0.0,
            "avg_benchmark_return": round(mean(benchmark_returns), 4) if benchmark_returns else 0.0,
            "avg_excess_return": round(mean(excess_returns), 4) if excess_returns else 0.0,
            "hit_rate": round(
                sum(1 for value in excess_returns if value > 0) / len(excess_returns),
                4,
            )
            if excess_returns
            else 0.0,
            "cumulative_strategy_return": round(_cumulative_return(strategy_returns), 4),
            "cumulative_benchmark_return": round(_cumulative_return(benchmark_returns), 4),
            "cumulative_excess_return": round(
                _cumulative_return(strategy_returns) - _cumulative_return(benchmark_returns),
                4,
            ),
        },
        "monthly_records": monthly_records,
    }


def run_part2_competition_backtest(
    panel_rows: list[dict[str, float | str]],
    lookback: int = 3,
    top_n: int = 2,
    weights: dict[str, float] | None = None,
) -> dict:
    weights = weights or {
        "top_sku_share_improvement": 0.15,
        "sweet_spot_share": 0.25,
        "whitespace_score_delta": 0.25,
        "negative_review_rate": 0.15,
        "median_lifetime_days": 0.12,
        "exit_risk": 0.05,
        "discount_efficiency": 0.03,
    }
    rows_by_category: dict[str, list[dict[str, float | str]]] = {}
    for row in panel_rows:
        rows_by_category.setdefault(str(row["category"]), []).append(row)

    for rows in rows_by_category.values():
        rows.sort(key=lambda item: str(item["month"]))

    months = sorted({str(row["month"]) for row in panel_rows})
    monthly_records = []

    for month_index in range(lookback, len(months) - 1):
        current_month = months[month_index]
        next_month = months[month_index + 1]

        top_sku_share: dict[str, float] = {}
        sweet_spot_share: dict[str, float] = {}
        whitespace_score: dict[str, float] = {}
        negative_review_rate: dict[str, float] = {}
        median_lifetime_days: dict[str, float] = {}
        exit_risk: dict[str, float] = {}
        discount_depth: dict[str, float] = {}
        next_returns: dict[str, float] = {}

        for category, rows in rows_by_category.items():
            current_row = next((row for row in rows if row["month"] == current_month), None)
            next_row = next((row for row in rows if row["month"] == next_month), None)
            history = [row for row in rows if row["month"] < current_month][-lookback:]
            if not current_row or not next_row or len(history) < lookback:
                continue

            top_sku_baseline = mean(float(row["top_sku_share"]) for row in history)
            whitespace_baseline = mean(float(row["whitespace_score"]) for row in history)

            top_sku_share[category] = top_sku_baseline - float(current_row["top_sku_share"])
            sweet_spot_share[category] = float(current_row["sweet_spot_share"])
            whitespace_score[category] = float(current_row["whitespace_score"]) - whitespace_baseline
            negative_review_rate[category] = -float(current_row["negative_review_rate"])
            median_lifetime_days[category] = float(current_row["median_lifetime_days"])
            exit_risk[category] = -float(current_row["exit_risk"])
            discount_depth[category] = -abs(float(current_row["discount_depth"]) - 0.12)
            next_returns[category] = (
                float(next_row["gmv_index"]) / max(float(current_row["gmv_index"]), 1e-9) - 1
            )
            next_returns[category] = _clamp(next_returns[category], -0.8, 1.5)

        if len(next_returns) <= top_n:
            continue

        top_sku_z = _zscore_map(top_sku_share)
        sweet_spot_z = _zscore_map(sweet_spot_share)
        whitespace_z = _zscore_map(whitespace_score)
        negative_review_z = _zscore_map(negative_review_rate)
        lifetime_z = _zscore_map(median_lifetime_days)
        exit_risk_z = _zscore_map(exit_risk)
        discount_z = _zscore_map(discount_depth)

        scores = {}
        for category in next_returns:
            scores[category] = (
                weights["top_sku_share_improvement"] * top_sku_z[category]
                + weights["sweet_spot_share"] * sweet_spot_z[category]
                + weights["whitespace_score_delta"] * whitespace_z[category]
                + weights["negative_review_rate"] * negative_review_z[category]
                + weights["median_lifetime_days"] * lifetime_z[category]
                + weights["exit_risk"] * exit_risk_z[category]
                + weights["discount_efficiency"] * discount_z[category]
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = ranked[:top_n]
        selected_categories = [category for category, _ in selected]
        strategy_return = mean(next_returns[category] for category in selected_categories)
        benchmark_return = mean(next_returns.values())
        monthly_records.append(
            {
                "month": current_month,
                "next_month": next_month,
                "selected_categories": selected_categories,
                "selected_scores": {category: round(score, 4) for category, score in selected},
                "strategy_return": round(strategy_return, 4),
                "benchmark_return": round(benchmark_return, 4),
                "excess_return": round(strategy_return - benchmark_return, 4),
            }
        )

    strategy_returns = [record["strategy_return"] for record in monthly_records]
    benchmark_returns = [record["benchmark_return"] for record in monthly_records]
    excess_returns = [record["excess_return"] for record in monthly_records]

    return {
        "config": {
            "lookback_months": lookback,
            "top_n": top_n,
            "signal_weights": weights,
            "target_normalization": "gmv_per_listing",
            "return_winsorization": [-0.8, 1.5],
        },
        "summary": {
            "periods": len(monthly_records),
            "avg_strategy_return": round(mean(strategy_returns), 4) if strategy_returns else 0.0,
            "avg_benchmark_return": round(mean(benchmark_returns), 4) if benchmark_returns else 0.0,
            "avg_excess_return": round(mean(excess_returns), 4) if excess_returns else 0.0,
            "hit_rate": round(
                sum(1 for value in excess_returns if value > 0) / len(excess_returns),
                4,
            )
            if excess_returns
            else 0.0,
            "cumulative_strategy_return": round(_cumulative_return(strategy_returns), 4),
            "cumulative_benchmark_return": round(_cumulative_return(benchmark_returns), 4),
            "cumulative_excess_return": round(
                _cumulative_return(strategy_returns) - _cumulative_return(benchmark_returns),
                4,
            ),
        },
        "monthly_records": monthly_records,
    }


def run_part3_supply_backtest(
    panel_rows: list[dict[str, float | str]],
    lookback: int = 3,
    top_n: int = 1,
    weights: dict[str, float] | None = None,
) -> dict:
    weights = weights or {
        "quote_confidence": 0.18,
        "margin_rate": 0.28,
        "compliance_readiness": 0.18,
        "logistics_reliability": 0.16,
        "cost_advantage": 0.10,
        "scenario_confidence": 0.10,
    }
    rows_by_item: dict[str, list[dict[str, float | str]]] = {}
    for row in panel_rows:
        rows_by_item.setdefault(str(row["scenario"]), []).append(row)
    for rows in rows_by_item.values():
        rows.sort(key=lambda item: str(item["month"]))

    months = sorted({str(row["month"]) for row in panel_rows})
    monthly_records = []
    for month_index in range(lookback, len(months) - 1):
        current_month = months[month_index]
        next_month = months[month_index + 1]

        quote_confidence: dict[str, float] = {}
        margin_rate: dict[str, float] = {}
        compliance_readiness: dict[str, float] = {}
        logistics_reliability: dict[str, float] = {}
        cost_advantage: dict[str, float] = {}
        scenario_confidence: dict[str, float] = {}
        next_returns: dict[str, float] = {}

        for item, rows in rows_by_item.items():
            current_row = next((row for row in rows if row["month"] == current_month), None)
            next_row = next((row for row in rows if row["month"] == next_month), None)
            history = [row for row in rows if row["month"] < current_month][-lookback:]
            if not current_row or not next_row or len(history) < lookback:
                continue
            margin_baseline = mean(float(row["margin_rate"]) for row in history)
            logistics_baseline = mean(float(row["logistics_reliability"]) for row in history)
            quote_confidence[item] = float(current_row["quote_confidence"])
            margin_rate[item] = float(current_row["margin_rate"]) - margin_baseline
            compliance_readiness[item] = float(current_row["compliance_readiness"])
            logistics_reliability[item] = float(current_row["logistics_reliability"]) - logistics_baseline
            cost_advantage[item] = float(current_row["cost_advantage"])
            scenario_confidence[item] = float(current_row["scenario_confidence"])
            next_returns[item] = (
                float(next_row["realized_margin_index"]) / max(float(current_row["realized_margin_index"]), 1e-9) - 1
            )

        if len(next_returns) <= top_n:
            continue

        quote_z = _zscore_map(quote_confidence)
        margin_z = _zscore_map(margin_rate)
        compliance_z = _zscore_map(compliance_readiness)
        logistics_z = _zscore_map(logistics_reliability)
        cost_z = _zscore_map(cost_advantage)
        scenario_z = _zscore_map(scenario_confidence)

        scores = {}
        for item in next_returns:
            scores[item] = (
                weights["quote_confidence"] * quote_z[item]
                + weights["margin_rate"] * margin_z[item]
                + weights["compliance_readiness"] * compliance_z[item]
                + weights["logistics_reliability"] * logistics_z[item]
                + weights["cost_advantage"] * cost_z[item]
                + weights["scenario_confidence"] * scenario_z[item]
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = ranked[:top_n]
        selected_items = [item for item, _ in selected]
        strategy_return = mean(next_returns[item] for item in selected_items)
        benchmark_return = mean(next_returns.values())
        monthly_records.append(
            {
                "month": current_month,
                "next_month": next_month,
                "selected_items": selected_items,
                "selected_scores": {item: round(score, 4) for item, score in selected},
                "strategy_return": round(strategy_return, 4),
                "benchmark_return": round(benchmark_return, 4),
                "excess_return": round(strategy_return - benchmark_return, 4),
            }
        )

    strategy_returns = [record["strategy_return"] for record in monthly_records]
    benchmark_returns = [record["benchmark_return"] for record in monthly_records]
    excess_returns = [record["excess_return"] for record in monthly_records]
    return {
        "config": {
            "lookback_months": lookback,
            "top_n": top_n,
            "signal_weights": weights,
        },
        "summary": {
            "periods": len(monthly_records),
            "avg_strategy_return": round(mean(strategy_returns), 4) if strategy_returns else 0.0,
            "avg_benchmark_return": round(mean(benchmark_returns), 4) if benchmark_returns else 0.0,
            "avg_excess_return": round(mean(excess_returns), 4) if excess_returns else 0.0,
            "hit_rate": round(sum(1 for value in excess_returns if value > 0) / len(excess_returns), 4) if excess_returns else 0.0,
            "cumulative_strategy_return": round(_cumulative_return(strategy_returns), 4),
            "cumulative_benchmark_return": round(_cumulative_return(benchmark_returns), 4),
            "cumulative_excess_return": round(_cumulative_return(strategy_returns) - _cumulative_return(benchmark_returns), 4),
        },
        "monthly_records": monthly_records,
    }


def run_part4_channel_backtest(
    panel_rows: list[dict[str, float | str]],
    lookback: int = 3,
    top_n: int = 2,
    weights: dict[str, float] | None = None,
) -> dict:
    weights = weights or {
        "contribution_margin_rate": 0.24,
        "repeat_rate": 0.18,
        "payback_efficiency": 0.18,
        "inventory_health": 0.12,
        "loss_resilience": 0.16,
        "traffic_efficiency": 0.12,
    }
    rows_by_item: dict[str, list[dict[str, float | str]]] = {}
    for row in panel_rows:
        rows_by_item.setdefault(str(row["channel"]), []).append(row)
    for rows in rows_by_item.values():
        rows.sort(key=lambda item: str(item["month"]))

    months = sorted({str(row["month"]) for row in panel_rows})
    monthly_records = []
    for month_index in range(lookback, len(months) - 1):
        current_month = months[month_index]
        next_month = months[month_index + 1]

        contribution_margin_rate: dict[str, float] = {}
        repeat_rate: dict[str, float] = {}
        payback_efficiency: dict[str, float] = {}
        inventory_health: dict[str, float] = {}
        loss_resilience: dict[str, float] = {}
        traffic_efficiency: dict[str, float] = {}
        next_returns: dict[str, float] = {}
        for item, rows in rows_by_item.items():
            current_row = next((row for row in rows if row["month"] == current_month), None)
            next_row = next((row for row in rows if row["month"] == next_month), None)
            history = [row for row in rows if row["month"] < current_month][-lookback:]
            if not current_row or not next_row or len(history) < lookback:
                continue
            contribution_margin_rate[item] = float(current_row["contribution_margin_rate"]) - mean(float(row["contribution_margin_rate"]) for row in history)
            repeat_rate[item] = float(current_row["repeat_rate"])
            payback_efficiency[item] = float(current_row["payback_efficiency"])
            inventory_health[item] = float(current_row["inventory_health"])
            loss_resilience[item] = float(current_row["loss_resilience"])
            traffic_efficiency[item] = float(current_row["traffic_efficiency"])
            next_returns[item] = (
                float(next_row["realized_profit_index"]) / max(float(current_row["realized_profit_index"]), 1e-9) - 1
            )

        if len(next_returns) <= top_n:
            continue

        margin_z = _zscore_map(contribution_margin_rate)
        repeat_z = _zscore_map(repeat_rate)
        payback_z = _zscore_map(payback_efficiency)
        inventory_z = _zscore_map(inventory_health)
        loss_z = _zscore_map(loss_resilience)
        traffic_z = _zscore_map(traffic_efficiency)
        scores = {}
        for item in next_returns:
            scores[item] = (
                weights["contribution_margin_rate"] * margin_z[item]
                + weights["repeat_rate"] * repeat_z[item]
                + weights["payback_efficiency"] * payback_z[item]
                + weights["inventory_health"] * inventory_z[item]
                + weights["loss_resilience"] * loss_z[item]
                + weights["traffic_efficiency"] * traffic_z[item]
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = ranked[:top_n]
        selected_items = [item for item, _ in selected]
        strategy_return = mean(next_returns[item] for item in selected_items)
        benchmark_return = mean(next_returns.values())
        monthly_records.append(
            {
                "month": current_month,
                "next_month": next_month,
                "selected_items": selected_items,
                "selected_scores": {item: round(score, 4) for item, score in selected},
                "strategy_return": round(strategy_return, 4),
                "benchmark_return": round(benchmark_return, 4),
                "excess_return": round(strategy_return - benchmark_return, 4),
            }
        )

    strategy_returns = [record["strategy_return"] for record in monthly_records]
    benchmark_returns = [record["benchmark_return"] for record in monthly_records]
    excess_returns = [record["excess_return"] for record in monthly_records]
    return {
        "config": {
            "lookback_months": lookback,
            "top_n": top_n,
            "signal_weights": weights,
        },
        "summary": {
            "periods": len(monthly_records),
            "avg_strategy_return": round(mean(strategy_returns), 4) if strategy_returns else 0.0,
            "avg_benchmark_return": round(mean(benchmark_returns), 4) if benchmark_returns else 0.0,
            "avg_excess_return": round(mean(excess_returns), 4) if excess_returns else 0.0,
            "hit_rate": round(sum(1 for value in excess_returns if value > 0) / len(excess_returns), 4) if excess_returns else 0.0,
            "cumulative_strategy_return": round(_cumulative_return(strategy_returns), 4),
            "cumulative_benchmark_return": round(_cumulative_return(benchmark_returns), 4),
            "cumulative_excess_return": round(_cumulative_return(strategy_returns) - _cumulative_return(benchmark_returns), 4),
        },
        "monthly_records": monthly_records,
    }


def run_part5_operating_backtest(
    panel_rows: list[dict[str, float | str]],
    lookback: int = 3,
    top_n: int = 2,
    weights: dict[str, float] | None = None,
) -> dict:
    weights = weights or {
        "operating_health": 0.22,
        "growth_leverage": 0.18,
        "margin_protection": 0.18,
        "inventory_readiness": 0.14,
        "incrementality": 0.16,
        "alert_relief": 0.12,
    }
    rows_by_item: dict[str, list[dict[str, float | str]]] = {}
    for row in panel_rows:
        rows_by_item.setdefault(str(row["channel"]), []).append(row)
    for rows in rows_by_item.values():
        rows.sort(key=lambda item: str(item["month"]))

    months = sorted({str(row["month"]) for row in panel_rows})
    monthly_records = []
    for month_index in range(lookback, len(months) - 1):
        current_month = months[month_index]
        next_month = months[month_index + 1]
        operating_health: dict[str, float] = {}
        growth_leverage: dict[str, float] = {}
        margin_protection: dict[str, float] = {}
        inventory_readiness: dict[str, float] = {}
        incrementality: dict[str, float] = {}
        alert_relief: dict[str, float] = {}
        next_returns: dict[str, float] = {}
        for item, rows in rows_by_item.items():
            current_row = next((row for row in rows if row["month"] == current_month), None)
            next_row = next((row for row in rows if row["month"] == next_month), None)
            history = [row for row in rows if row["month"] < current_month][-lookback:]
            if not current_row or not next_row or len(history) < lookback:
                continue
            operating_health[item] = float(current_row["operating_health"]) - mean(float(row["operating_health"]) for row in history)
            growth_leverage[item] = float(current_row["growth_leverage"])
            margin_protection[item] = float(current_row["margin_protection"])
            inventory_readiness[item] = float(current_row["inventory_readiness"])
            incrementality[item] = float(current_row["incrementality"])
            alert_relief[item] = float(current_row["alert_relief"])
            next_returns[item] = (
                float(next_row["realized_operating_index"]) / max(float(current_row["realized_operating_index"]), 1e-9) - 1
            )

        if len(next_returns) <= top_n:
            continue

        health_z = _zscore_map(operating_health)
        growth_z = _zscore_map(growth_leverage)
        protection_z = _zscore_map(margin_protection)
        inventory_z = _zscore_map(inventory_readiness)
        incrementality_z = _zscore_map(incrementality)
        alert_z = _zscore_map(alert_relief)
        scores = {}
        for item in next_returns:
            scores[item] = (
                weights["operating_health"] * health_z[item]
                + weights["growth_leverage"] * growth_z[item]
                + weights["margin_protection"] * protection_z[item]
                + weights["inventory_readiness"] * inventory_z[item]
                + weights["incrementality"] * incrementality_z[item]
                + weights["alert_relief"] * alert_z[item]
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = ranked[:top_n]
        selected_items = [item for item, _ in selected]
        strategy_return = mean(next_returns[item] for item in selected_items)
        benchmark_return = mean(next_returns.values())
        monthly_records.append(
            {
                "month": current_month,
                "next_month": next_month,
                "selected_items": selected_items,
                "selected_scores": {item: round(score, 4) for item, score in selected},
                "strategy_return": round(strategy_return, 4),
                "benchmark_return": round(benchmark_return, 4),
                "excess_return": round(strategy_return - benchmark_return, 4),
            }
        )

    strategy_returns = [record["strategy_return"] for record in monthly_records]
    benchmark_returns = [record["benchmark_return"] for record in monthly_records]
    excess_returns = [record["excess_return"] for record in monthly_records]
    return {
        "config": {
            "lookback_months": lookback,
            "top_n": top_n,
            "signal_weights": weights,
        },
        "summary": {
            "periods": len(monthly_records),
            "avg_strategy_return": round(mean(strategy_returns), 4) if strategy_returns else 0.0,
            "avg_benchmark_return": round(mean(benchmark_returns), 4) if benchmark_returns else 0.0,
            "avg_excess_return": round(mean(excess_returns), 4) if excess_returns else 0.0,
            "hit_rate": round(sum(1 for value in excess_returns if value > 0) / len(excess_returns), 4) if excess_returns else 0.0,
            "cumulative_strategy_return": round(_cumulative_return(strategy_returns), 4),
            "cumulative_benchmark_return": round(_cumulative_return(benchmark_returns), 4),
            "cumulative_excess_return": round(_cumulative_return(strategy_returns) - _cumulative_return(benchmark_returns), 4),
        },
        "monthly_records": monthly_records,
    }


def _optimization_objective(result: dict) -> float:
    summary = result.get("summary", {})
    avg_excess = float(summary.get("avg_excess_return", 0.0))
    hit_rate = float(summary.get("hit_rate", 0.0))
    periods = float(summary.get("periods", 0.0))
    cumulative_excess = float(summary.get("cumulative_excess_return", 0.0))
    return avg_excess * 0.55 + hit_rate * 0.25 + cumulative_excess * 0.2 + min(periods / 20.0, 1.0) * 0.02


def _panel_train_test_split(
    panel_rows: list[dict[str, float | str]],
    lookback: int,
    train_ratio: float,
) -> tuple[list[dict[str, float | str]], list[dict[str, float | str]], str]:
    months = sorted({str(row["month"]) for row in panel_rows})
    split_index = max(lookback + 1, min(len(months) - 2, int(len(months) * train_ratio)))
    split_month = months[split_index]
    history_months = set(months[: split_index + 1])
    test_months = set(months[max(0, split_index - lookback) :])
    train_rows = [row for row in panel_rows if str(row["month"]) in history_months]
    test_rows = [row for row in panel_rows if str(row["month"]) in test_months]
    return train_rows, test_rows, split_month


def optimize_backtest_weights(
    panel_rows: list[dict[str, float | str]],
    runner,
    base_weights: dict[str, float],
    lookback: int = 3,
    top_n: int = 2,
    train_ratio: float = 0.65,
    multipliers: tuple[float, ...] = (0.75, 1.0, 1.25),
) -> dict:
    train_rows, test_rows, split_month = _panel_train_test_split(panel_rows, lookback, train_ratio)
    weight_keys = list(base_weights.keys())
    best_weights = dict(base_weights)
    best_train_result = runner(train_rows, lookback=lookback, top_n=top_n, weights=best_weights)
    best_objective = _optimization_objective(best_train_result)

    candidates = 1
    for _ in weight_keys:
        candidates *= len(multipliers)

    stack = [({}, 0)]
    while stack:
        partial, index = stack.pop()
        if index == len(weight_keys):
            weights = {
                key: round(base_weights[key] * partial[key], 6)
                for key in weight_keys
            }
            train_result = runner(train_rows, lookback=lookback, top_n=top_n, weights=weights)
            objective = _optimization_objective(train_result)
            if objective > best_objective:
                best_objective = objective
                best_weights = weights
                best_train_result = train_result
            continue
        key = weight_keys[index]
        for multiplier in multipliers:
            next_partial = dict(partial)
            next_partial[key] = multiplier
            stack.append((next_partial, index + 1))

    baseline_train = runner(train_rows, lookback=lookback, top_n=top_n, weights=base_weights)
    baseline_test = runner(test_rows, lookback=lookback, top_n=top_n, weights=base_weights)
    optimized_test = runner(test_rows, lookback=lookback, top_n=top_n, weights=best_weights)
    optimized_full = runner(panel_rows, lookback=lookback, top_n=top_n, weights=best_weights)
    return {
        "split_month": split_month,
        "candidate_count": candidates,
        "base_weights": base_weights,
        "optimized_weights": best_weights,
        "baseline_train": baseline_train,
        "baseline_test": baseline_test,
        "optimized_train": best_train_result,
        "optimized_test": optimized_test,
        "optimized_full": optimized_full,
        "improvement": {
            "train_avg_excess_delta": round(
                best_train_result["summary"]["avg_excess_return"] - baseline_train["summary"]["avg_excess_return"],
                4,
            ) if baseline_train["summary"]["periods"] else 0.0,
            "test_avg_excess_delta": round(
                optimized_test["summary"]["avg_excess_return"] - baseline_test["summary"]["avg_excess_return"],
                4,
            ) if baseline_test["summary"]["periods"] else 0.0,
            "test_hit_rate_delta": round(
                optimized_test["summary"]["hit_rate"] - baseline_test["summary"]["hit_rate"],
                4,
            ) if baseline_test["summary"]["periods"] else 0.0,
        },
    }


def write_backtest_curve_svg(result: dict, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = result.get("monthly_records", [])
    if not records:
        output_path.write_text("", encoding="utf-8")
        return output_path

    width = 960
    height = 540
    left = 80
    right = 40
    top = 60
    bottom = 70
    plot_width = width - left - right
    plot_height = height - top - bottom

    strategy_curve = []
    benchmark_curve = []
    strategy_value = 1.0
    benchmark_value = 1.0
    for record in records:
        strategy_value *= 1 + record["strategy_return"]
        benchmark_value *= 1 + record["benchmark_return"]
        strategy_curve.append(strategy_value)
        benchmark_curve.append(benchmark_value)

    y_max = max(max(strategy_curve), max(benchmark_curve)) * 1.05
    step_x = plot_width / max(len(records) - 1, 1)

    def to_points(curve: list[float]) -> str:
        points = []
        for idx, value in enumerate(curve):
            x = left + idx * step_x
            y = top + plot_height - (value / y_max) * plot_height
            points.append(f"{x:.1f},{y:.1f}")
        return " ".join(points)

    x_labels = []
    for idx, record in enumerate(records):
        x = left + idx * step_x
        x_labels.append(
            f'<text x="{x:.1f}" y="{height - 25}" text-anchor="middle" font-size="12" fill="#5f6b7a">{record["month"]}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{left}" y="32" font-size="24" font-family="Arial, sans-serif" fill="#102a43">Backtest Cumulative Return</text>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  <polyline fill="none" stroke="#1f77b4" stroke-width="3" points="{to_points(strategy_curve)}" />
  <polyline fill="none" stroke="#ef8354" stroke-width="3" points="{to_points(benchmark_curve)}" />
  <text x="{width - 190}" y="{top + 20}" font-size="12" fill="#1f77b4">Strategy</text>
  <text x="{width - 190}" y="{top + 40}" font-size="12" fill="#ef8354">Benchmark</text>
  {''.join(x_labels)}
</svg>"""
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def write_backtest_monthly_csv(result: dict, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in result.get("monthly_records", []):
        selected = record.get("selected_categories") or record.get("selected_items") or []
        rows.append(
            {
                "month": record["month"],
                "next_month": record["next_month"],
                "selected_categories": "|".join(selected),
                "strategy_return": str(record["strategy_return"]),
                "benchmark_return": str(record["benchmark_return"]),
                "excess_return": str(record["excess_return"]),
            }
        )
    write_csv_rows(
        output_path,
        [
            "month",
            "next_month",
            "selected_categories",
            "strategy_return",
            "benchmark_return",
            "excess_return",
        ],
        rows,
    )
    return output_path


def run_backtest_demo(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = write_demo_backtest_panel(output_dir / "market_opportunity_panel.csv", seed=seed)
    panel_rows = load_backtest_panel(panel_path)
    result = run_market_opportunity_backtest(panel_rows)
    summary_path = write_json(output_dir / "backtest_summary.json", result)
    chart_path = write_backtest_curve_svg(result, output_dir / "backtest_curve.svg")
    monthly_csv_path = write_backtest_monthly_csv(result, output_dir / "backtest_monthly_returns.csv")
    return {
        "panel_csv": str(panel_path),
        "summary_json": str(summary_path),
        "curve_svg": str(chart_path),
        "monthly_csv": str(monthly_csv_path),
        "summary": result["summary"],
    }


def run_part2_backtest_demo(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = write_demo_part2_backtest_panel(output_dir / "part2_competition_panel.csv", seed=seed)
    panel_rows = load_part2_backtest_panel(panel_path)
    result = run_part2_competition_backtest(panel_rows)
    summary_path = write_json(output_dir / "part2_backtest_summary.json", result)
    chart_path = write_backtest_curve_svg(result, output_dir / "part2_backtest_curve.svg")
    monthly_csv_path = write_backtest_monthly_csv(result, output_dir / "part2_backtest_monthly_returns.csv")
    return {
        "panel_csv": str(panel_path),
        "summary_json": str(summary_path),
        "curve_svg": str(chart_path),
        "monthly_csv": str(monthly_csv_path),
        "summary": result["summary"],
    }


def run_part3_backtest_demo(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = write_demo_part3_backtest_panel(output_dir / "part3_supply_panel.csv", seed=seed)
    panel_rows = load_part3_backtest_panel(panel_path)
    result = run_part3_supply_backtest(panel_rows)
    summary_path = write_json(output_dir / "part3_backtest_summary.json", result)
    chart_path = write_backtest_curve_svg(result, output_dir / "part3_backtest_curve.svg")
    monthly_csv_path = write_backtest_monthly_csv(result, output_dir / "part3_backtest_monthly_returns.csv")
    return {
        "panel_csv": str(panel_path),
        "summary_json": str(summary_path),
        "curve_svg": str(chart_path),
        "monthly_csv": str(monthly_csv_path),
        "summary": result["summary"],
    }


def run_part4_backtest_demo(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = write_demo_part4_backtest_panel(output_dir / "part4_channel_panel.csv", seed=seed)
    panel_rows = load_part4_backtest_panel(panel_path)
    result = run_part4_channel_backtest(panel_rows)
    summary_path = write_json(output_dir / "part4_backtest_summary.json", result)
    chart_path = write_backtest_curve_svg(result, output_dir / "part4_backtest_curve.svg")
    monthly_csv_path = write_backtest_monthly_csv(result, output_dir / "part4_backtest_monthly_returns.csv")
    return {
        "panel_csv": str(panel_path),
        "summary_json": str(summary_path),
        "curve_svg": str(chart_path),
        "monthly_csv": str(monthly_csv_path),
        "summary": result["summary"],
    }


def run_part5_backtest_demo(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    panel_path = write_demo_part5_backtest_panel(output_dir / "part5_operating_panel.csv", seed=seed)
    panel_rows = load_part5_backtest_panel(panel_path)
    result = run_part5_operating_backtest(panel_rows)
    summary_path = write_json(output_dir / "part5_backtest_summary.json", result)
    chart_path = write_backtest_curve_svg(result, output_dir / "part5_backtest_curve.svg")
    monthly_csv_path = write_backtest_monthly_csv(result, output_dir / "part5_backtest_monthly_returns.csv")
    return {
        "panel_csv": str(panel_path),
        "summary_json": str(summary_path),
        "curve_svg": str(chart_path),
        "monthly_csv": str(monthly_csv_path),
        "summary": result["summary"],
    }


def run_full_backtest_suite(output_dir: str | Path, seed: int = 42) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    part1_panel = load_backtest_panel(write_demo_backtest_panel(output_dir / "part1_panel.csv", seed=seed))
    part2_panel = load_part2_backtest_panel(write_demo_part2_backtest_panel(output_dir / "part2_panel.csv", seed=seed))
    part3_panel = load_part3_backtest_panel(write_demo_part3_backtest_panel(output_dir / "part3_panel.csv", seed=seed))
    part4_panel = load_part4_backtest_panel(write_demo_part4_backtest_panel(output_dir / "part4_panel.csv", seed=seed))
    part5_panel = load_part5_backtest_panel(write_demo_part5_backtest_panel(output_dir / "part5_panel.csv", seed=seed))

    suite = {
        "part1": {
            "name": "Market Opportunity",
            "optimization": optimize_backtest_weights(
                part1_panel,
                run_market_opportunity_backtest,
                {
                    "demand_momentum": 0.35,
                    "channel_roas": 0.25,
                    "price_realization_rate": 0.20,
                    "supply_pressure": -0.10,
                    "hhi": -0.10,
                },
            ),
        },
        "part2": {
            "name": "Competition Structure",
            "optimization": optimize_backtest_weights(
                part2_panel,
                run_part2_competition_backtest,
                {
                    "top_sku_share_improvement": 0.15,
                    "sweet_spot_share": 0.25,
                    "whitespace_score_delta": 0.25,
                    "negative_review_rate": 0.15,
                    "median_lifetime_days": 0.12,
                    "exit_risk": 0.05,
                    "discount_efficiency": 0.03,
                },
            ),
        },
        "part3": {
            "name": "Supply Path",
            "optimization": optimize_backtest_weights(
                part3_panel,
                run_part3_supply_backtest,
                {
                    "quote_confidence": 0.18,
                    "margin_rate": 0.28,
                    "compliance_readiness": 0.18,
                    "logistics_reliability": 0.16,
                    "cost_advantage": 0.10,
                    "scenario_confidence": 0.10,
                },
                top_n=1,
            ),
        },
        "part4": {
            "name": "Channel Selection",
            "optimization": optimize_backtest_weights(
                part4_panel,
                run_part4_channel_backtest,
                {
                    "contribution_margin_rate": 0.24,
                    "repeat_rate": 0.18,
                    "payback_efficiency": 0.18,
                    "inventory_health": 0.12,
                    "loss_resilience": 0.16,
                    "traffic_efficiency": 0.12,
                },
            ),
        },
        "part5": {
            "name": "Operating Scale",
            "optimization": optimize_backtest_weights(
                part5_panel,
                run_part5_operating_backtest,
                {
                    "operating_health": 0.22,
                    "growth_leverage": 0.18,
                    "margin_protection": 0.18,
                    "inventory_readiness": 0.14,
                    "incrementality": 0.16,
                    "alert_relief": 0.12,
                },
            ),
        },
    }

    summary_rows = []
    for part_key, payload in suite.items():
        optimized_full = payload["optimization"]["optimized_full"]
        baseline_test = payload["optimization"]["baseline_test"]
        optimized_test = payload["optimization"]["optimized_test"]
        curve_path = write_backtest_curve_svg(optimized_full, output_dir / f"{part_key}_optimized_curve.svg")
        monthly_path = write_backtest_monthly_csv(optimized_full, output_dir / f"{part_key}_optimized_monthly.csv")
        payload["optimization_json"] = str(write_json(output_dir / f"{part_key}_optimization.json", payload["optimization"]))
        payload["curve_svg"] = str(curve_path)
        payload["monthly_csv"] = str(monthly_path)
        summary_rows.append(
            {
                "part": part_key,
                "name": payload["name"],
                "baseline_test_avg_excess_return": baseline_test["summary"]["avg_excess_return"],
                "optimized_test_avg_excess_return": optimized_test["summary"]["avg_excess_return"],
                "optimized_test_hit_rate": optimized_test["summary"]["hit_rate"],
                "optimized_full_cumulative_excess_return": optimized_full["summary"]["cumulative_excess_return"],
            }
        )

    suite_summary = {
        "seed": seed,
        "parts": summary_rows,
    }
    summary_json = write_json(output_dir / "suite_summary.json", suite_summary)
    return {
        "output_dir": str(output_dir),
        "suite_summary_json": str(summary_json),
        "parts": suite,
    }
