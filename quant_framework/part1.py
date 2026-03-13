from .metrics import (
    compute_bottom_up_market_size,
    compute_channel_metrics,
    compute_customer_profile,
    compute_demand_metrics,
    compute_listed_price_metrics,
    compute_top_down_market_size,
    compute_transaction_metrics,
)
from .models import MarketSizeAssumptions, Part1Dataset
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
    },
    "1.2": {
        "title": "客户画像分析",
        "required_tables": ["customer_segments"],
        "metric_ids": ["customer_distribution"],
    },
    "1.3": {
        "title": "市场规模分析",
        "required_tables": ["listings"],
        "metric_ids": [
            "bottom_up_market_size",
            "top_down_market_size",
            "market_hhi",
        ],
    },
    "1.4": {
        "title": "购买渠道分析",
        "required_tables": ["channels"],
        "metric_ids": [
            "channel_share",
            "channel_conversion_rate",
        ],
    },
    "1.5": {
        "title": "货架商品价格分析",
        "required_tables": ["listings"],
        "metric_ids": [
            "listed_price_bands",
            "brand_premium",
        ],
    },
    "1.6": {
        "title": "实际成交价格分析",
        "required_tables": ["transactions"],
        "metric_ids": [
            "average_transaction_price",
            "average_discount_rate",
            "price_elasticity",
        ],
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
    report = {
        "metadata": {
            "section_structure": PART1_SECTION_STRUCTURE,
            "metric_specs": [metric.__dict__ for metric in PART1_METRICS],
        },
        "sections": {
            "1.1": {
                "title": PART1_SECTION_STRUCTURE["1.1"]["title"],
                "metrics": compute_demand_metrics(dataset.search_trends, dataset.region_demand),
            },
            "1.2": {
                "title": PART1_SECTION_STRUCTURE["1.2"]["title"],
                "metrics": compute_customer_profile(dataset.customer_segments),
            },
            "1.3": {
                "title": PART1_SECTION_STRUCTURE["1.3"]["title"],
                "metrics": {
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
            },
            "1.4": {
                "title": PART1_SECTION_STRUCTURE["1.4"]["title"],
                "metrics": compute_channel_metrics(dataset.channels),
            },
            "1.5": {
                "title": PART1_SECTION_STRUCTURE["1.5"]["title"],
                "metrics": compute_listed_price_metrics(dataset.listings),
            },
            "1.6": {
                "title": PART1_SECTION_STRUCTURE["1.6"]["title"],
                "metrics": compute_transaction_metrics(dataset.transactions),
            },
        },
    }
    report["uncertainty"] = build_part1_uncertainty_snapshot(
        dataset.listings,
        dataset.transactions,
        assumptions,
    )
    report["validation"] = build_methodology_validation(report)
    return report
