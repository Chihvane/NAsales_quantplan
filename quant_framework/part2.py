from __future__ import annotations

from .decision_summary import build_part2_decision_summary
from .models import Part2Assumptions, Part2Dataset
from .part2_metrics import (
    compute_attribute_landscape,
    compute_listing_dynamics,
    compute_review_analytics,
    compute_sku_market_structure,
    compute_transaction_price_analysis,
    compute_value_gap_analysis,
)
from .reporting import (
    attach_decision_summary,
    attach_headline_metrics,
    build_standard_report,
    finalize_report_overview,
)
from .registry import PART2_METRICS
from .uncertainty import build_part2_uncertainty_snapshot
from .validation import build_part2_methodology_validation


PART2_SECTION_STRUCTURE = {
    "2.1": {
        "title": "在售商品与成交结构",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["sku_gmv_leaderboard"],
        "quality_targets": {"listing_snapshots": 20, "sold_transactions": 20},
    },
    "2.2": {
        "title": "成交价格带与折扣深度",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["realized_price_distribution"],
        "quality_targets": {"listing_snapshots": 20, "sold_transactions": 20},
    },
    "2.3": {
        "title": "价格-评分价值矩阵",
        "required_tables": ["listing_snapshots", "sold_transactions"],
        "metric_ids": ["price_rating_matrix"],
        "quality_targets": {"listing_snapshots": 20, "sold_transactions": 20},
    },
    "2.4": {
        "title": "属性画像与白空间机会",
        "required_tables": ["product_catalog", "sold_transactions"],
        "metric_ids": ["attribute_outperformance"],
        "quality_targets": {"product_catalog": 8, "sold_transactions": 20},
    },
    "2.5": {
        "title": "评论情绪与痛点主题",
        "required_tables": ["reviews"],
        "metric_ids": ["review_sentiment_topics"],
        "quality_targets": {"reviews": 16},
    },
    "2.6": {
        "title": "货架动态与生存分析",
        "required_tables": ["listing_snapshots"],
        "metric_ids": ["listing_survival_dynamics"],
        "quality_targets": {"listing_snapshots": 20},
    },
}


def build_part2_quant_report(
    dataset: Part2Dataset,
    assumptions: Part2Assumptions,
) -> dict:
    section_metrics = {
        "2.1": compute_sku_market_structure(
            dataset.listing_snapshots,
            dataset.sold_transactions,
            assumptions,
        ),
        "2.2": compute_transaction_price_analysis(
            dataset.listing_snapshots,
            dataset.sold_transactions,
            assumptions,
        ),
        "2.3": compute_value_gap_analysis(
            dataset.listing_snapshots,
            dataset.sold_transactions,
        ),
        "2.4": compute_attribute_landscape(
            dataset.product_catalog,
            dataset.sold_transactions,
            assumptions,
        ),
        "2.5": compute_review_analytics(
            dataset.reviews,
            assumptions,
        ),
        "2.6": compute_listing_dynamics(dataset.listing_snapshots),
    }
    report = build_standard_report(
        report_id="part2_quant_report",
        section_structure=PART2_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART2_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part2_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part2_methodology_validation(report)
    report = attach_headline_metrics(
        report,
        [
            {
                "key": "total_gmv",
                "label": "总 GMV",
                "value": round(section_metrics["2.1"].get("total_gmv", 0.0), 2),
                "unit": "USD",
            },
            {
                "key": "top_sku_share",
                "label": "Top SKU 份额",
                "value": round(section_metrics["2.1"].get("top_sku_share", 0.0), 4),
                "unit": "ratio",
            },
            {
                "key": "sweet_spot_band",
                "label": "成交甜蜜带",
                "value": section_metrics["2.2"].get("sweet_spot_band", {}).get("label", ""),
                "unit": "band",
            },
            {
                "key": "negative_review_rate",
                "label": "负评占比",
                "value": round(section_metrics["2.5"].get("sentiment_mix", {}).get("negative", 0.0), 4),
                "unit": "ratio",
            },
            {
                "key": "median_lifetime_days",
                "label": "货架中位生存期",
                "value": section_metrics["2.6"].get("median_lifetime_days", 0),
                "unit": "days",
            },
        ],
    )
    report = attach_decision_summary(report, build_part2_decision_summary(section_metrics))
    return finalize_report_overview(report)
