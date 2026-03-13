from __future__ import annotations

from .models import Part2Assumptions, Part2Dataset
from .part2_metrics import (
    compute_attribute_landscape,
    compute_listing_dynamics,
    compute_review_analytics,
    compute_sku_market_structure,
    compute_transaction_price_analysis,
    compute_value_gap_analysis,
)
from .registry import PART2_METRICS
from .uncertainty import build_part2_uncertainty_snapshot
from .validation import build_part2_methodology_validation


PART2_SECTION_STRUCTURE = {
    "2.1": {
        "title": "在售商品与成交结构",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["sku_gmv_leaderboard"],
    },
    "2.2": {
        "title": "成交价格带与折扣深度",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["realized_price_distribution"],
    },
    "2.3": {
        "title": "价格-评分价值矩阵",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["price_rating_matrix"],
    },
    "2.4": {
        "title": "属性画像与白空间机会",
        "required_tables": ["product_catalog", "sold_transactions"],
        "metric_ids": ["attribute_outperformance"],
    },
    "2.5": {
        "title": "评论情绪与痛点主题",
        "required_tables": ["reviews"],
        "metric_ids": ["review_sentiment_topics"],
    },
    "2.6": {
        "title": "货架动态与生存分析",
        "required_tables": ["listing_snapshots"],
        "metric_ids": ["listing_survival_dynamics"],
    },
}


def build_part2_quant_report(
    dataset: Part2Dataset,
    assumptions: Part2Assumptions,
) -> dict:
    report = {
        "metadata": {
            "section_structure": PART2_SECTION_STRUCTURE,
            "metric_specs": [metric.__dict__ for metric in PART2_METRICS],
        },
        "sections": {
            "2.1": {
                "title": PART2_SECTION_STRUCTURE["2.1"]["title"],
                "metrics": compute_sku_market_structure(
                    dataset.listing_snapshots,
                    dataset.sold_transactions,
                    assumptions,
                ),
            },
            "2.2": {
                "title": PART2_SECTION_STRUCTURE["2.2"]["title"],
                "metrics": compute_transaction_price_analysis(
                    dataset.listing_snapshots,
                    dataset.sold_transactions,
                    assumptions,
                ),
            },
            "2.3": {
                "title": PART2_SECTION_STRUCTURE["2.3"]["title"],
                "metrics": compute_value_gap_analysis(
                    dataset.listing_snapshots,
                    dataset.sold_transactions,
                ),
            },
            "2.4": {
                "title": PART2_SECTION_STRUCTURE["2.4"]["title"],
                "metrics": compute_attribute_landscape(
                    dataset.product_catalog,
                    dataset.sold_transactions,
                    assumptions,
                ),
            },
            "2.5": {
                "title": PART2_SECTION_STRUCTURE["2.5"]["title"],
                "metrics": compute_review_analytics(
                    dataset.reviews,
                    assumptions,
                ),
            },
            "2.6": {
                "title": PART2_SECTION_STRUCTURE["2.6"]["title"],
                "metrics": compute_listing_dynamics(dataset.listing_snapshots),
            },
        },
    }
    report["uncertainty"] = build_part2_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part2_methodology_validation(report)
    return report
