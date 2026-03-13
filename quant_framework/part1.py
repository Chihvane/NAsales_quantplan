from .metrics import (
    compute_bottom_up_market_size,
    compute_channel_metrics,
    compute_customer_profile,
    compute_demand_metrics,
    compute_listed_price_metrics,
    compute_top_down_market_size,
    compute_transaction_metrics,
)
from .decision_summary import build_part1_decision_summary
from .models import MarketSizeAssumptions, Part1Dataset
from .reporting import (
    attach_decision_summary,
    attach_headline_metrics,
    build_standard_report,
    finalize_report_overview,
)
from .registry import PART1_METRICS
from .uncertainty import build_part1_uncertainty_snapshot
from .validation import build_methodology_validation


PART1_SECTION_STRUCTURE = {
    "1.1": {
        "title": "市场现状与需求概览",
        "required_tables": ["search_trends", "region_demand"],
        "metric_ids": [
            "demand_growth_rate",
            "seasonality_index",
            "regional_demand_share",
        ],
        "quality_targets": {"search_trends": 12, "region_demand": 5},
    },
    "1.2": {
        "title": "客户画像分析",
        "required_tables": ["customer_segments"],
        "metric_ids": ["customer_distribution"],
        "quality_targets": {"customer_segments": 12},
    },
    "1.3": {
        "title": "市场规模分析",
        "required_tables": ["listings"],
        "metric_ids": [
            "bottom_up_market_size",
            "top_down_market_size",
            "market_hhi",
        ],
        "quality_targets": {"listings": 8},
    },
    "1.4": {
        "title": "购买渠道分析",
        "required_tables": ["channels"],
        "metric_ids": [
            "channel_share",
            "channel_conversion_rate",
        ],
        "quality_targets": {"channels": 4},
    },
    "1.5": {
        "title": "货架商品价格分析",
        "required_tables": ["listings"],
        "metric_ids": [
            "listed_price_bands",
            "brand_premium",
        ],
        "quality_targets": {"listings": 8},
    },
    "1.6": {
        "title": "实际成交价格分析",
        "required_tables": ["transactions"],
        "metric_ids": [
            "average_transaction_price",
            "average_discount_rate",
            "price_elasticity",
        ],
        "quality_targets": {"transactions": 12},
    },
}


def build_part1_quant_report(
    dataset: Part1Dataset,
    assumptions: MarketSizeAssumptions,
) -> dict:
    top_down = compute_top_down_market_size(assumptions)
    bottom_up = compute_bottom_up_market_size(
        dataset.listings,
        assumptions.sample_coverage,
    )
    section_metrics = {
        "1.1": compute_demand_metrics(dataset.search_trends, dataset.region_demand),
        "1.2": compute_customer_profile(dataset.customer_segments),
        "1.3": {
            "top_down": top_down,
            "bottom_up": bottom_up,
            "triangulation": {
                "top_down_vs_bottom_up_gap_ratio": round(
                    abs(
                        bottom_up.get("estimated_annual_market_size", 0.0)
                        - top_down.get("sam", 0.0)
                    )
                    / top_down.get("sam", 1.0),
                    4,
                )
                if top_down.get("sam", 0.0)
                else 0.0,
            },
        },
        "1.4": compute_channel_metrics(dataset.channels),
        "1.5": compute_listed_price_metrics(dataset.listings),
        "1.6": compute_transaction_metrics(dataset.transactions),
    }
    report = build_standard_report(
        report_id="part1_quant_report",
        section_structure=PART1_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART1_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part1_uncertainty_snapshot(
        dataset.listings,
        dataset.transactions,
        assumptions,
    )
    report["validation"] = build_methodology_validation(report)
    report = attach_headline_metrics(
        report,
        [
            {"key": "sam", "label": "SAM", "value": round(top_down.get("sam", 0.0), 2), "unit": "USD"},
            {
                "key": "bottom_up_market_size",
                "label": "Bottom-Up 年化市场规模",
                "value": round(bottom_up.get("estimated_annual_market_size", 0.0), 2),
                "unit": "USD",
            },
            {
                "key": "triangulation_gap_ratio",
                "label": "双口径偏差",
                "value": section_metrics["1.3"]["triangulation"]["top_down_vs_bottom_up_gap_ratio"],
                "unit": "ratio",
            },
            {
                "key": "top_channel",
                "label": "主成交渠道",
                "value": (section_metrics["1.4"].get("channels", [{}])[0].get("channel") if section_metrics["1.4"].get("channels") else ""),
                "unit": "channel",
            },
            {
                "key": "average_actual_price",
                "label": "平均实际成交价",
                "value": round(section_metrics["1.6"].get("average_actual_price", 0.0), 2),
                "unit": "USD",
            },
        ],
    )
    report = attach_decision_summary(report, build_part1_decision_summary(section_metrics))
    return finalize_report_overview(report)
