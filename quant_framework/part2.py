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
from .stats_utils import clip
from .uncertainty import build_part2_uncertainty_snapshot
from .validation import build_part2_methodology_validation


PART2_SECTION_STRUCTURE = {
    "2.1": {
        "title": "在售商品与成交结构",
        "required_tables": ["listing_snapshots", "sold_transactions", "part2_source_registry"],
        "metric_ids": ["sku_gmv_leaderboard"],
        "quality_targets": {"listing_snapshots": 20, "sold_transactions": 20, "part2_source_registry": 3},
        "analysis_grain": "listing x transaction",
        "entity_grain": "sku x platform",
        "time_grain": "listing snapshot / sold date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.channel"],
        "evidence_refs": ["evidence.listing_snapshots", "evidence.sold_transactions", "evidence.part2_source_registry"],
        "rule_refs": ["gate.competition_density"],
    },
    "2.2": {
        "title": "成交价格带与折扣深度",
        "required_tables": ["listing_snapshots", "sold_transactions", "part2_benchmark_registry", "part2_threshold_registry"],
        "metric_ids": ["realized_price_distribution"],
        "quality_targets": {
            "listing_snapshots": 20,
            "sold_transactions": 20,
            "part2_benchmark_registry": 2,
            "part2_threshold_registry": 2,
        },
        "analysis_grain": "transaction price event",
        "entity_grain": "sku x platform",
        "time_grain": "sold date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.listing_snapshots", "evidence.sold_transactions", "evidence.part2_benchmark_registry"],
        "rule_refs": ["gate.sweet_spot_fit", "gate.part2_threshold_registry"],
    },
    "2.3": {
        "title": "价格-评分价值矩阵",
        "required_tables": ["listing_snapshots", "sold_transactions", "part2_benchmark_registry"],
        "metric_ids": ["price_rating_matrix"],
        "quality_targets": {"listing_snapshots": 20, "sold_transactions": 20, "part2_benchmark_registry": 2},
        "analysis_grain": "price x rating bucket",
        "entity_grain": "sku x platform",
        "time_grain": "sold date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.listing_snapshots", "evidence.sold_transactions", "evidence.part2_benchmark_registry"],
        "rule_refs": ["gate.value_gap"],
    },
    "2.4": {
        "title": "属性画像与白空间机会",
        "required_tables": ["product_catalog", "sold_transactions", "part2_source_registry"],
        "metric_ids": ["attribute_outperformance"],
        "quality_targets": {"product_catalog": 8, "sold_transactions": 20, "part2_source_registry": 3},
        "analysis_grain": "attribute token x sold item",
        "entity_grain": "canonical sku x attribute",
        "time_grain": "sold date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.attribute_taxonomy"],
        "evidence_refs": ["evidence.product_catalog", "evidence.sold_transactions", "evidence.part2_source_registry"],
        "rule_refs": ["gate.whitespace_opportunity"],
    },
    "2.5": {
        "title": "评论情绪与痛点主题",
        "required_tables": ["reviews", "voc_event_registry", "part2_threshold_registry", "part2_source_registry"],
        "metric_ids": ["review_sentiment_topics"],
        "quality_targets": {
            "reviews": 16,
            "voc_event_registry": 2,
            "part2_threshold_registry": 2,
            "part2_source_registry": 3,
        },
        "analysis_grain": "review row",
        "entity_grain": "sku x review theme",
        "time_grain": "review date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku"],
        "evidence_refs": ["evidence.reviews", "evidence.voc_event_registry", "evidence.part2_source_registry"],
        "rule_refs": ["gate.voc_risk", "gate.part2_threshold_registry"],
    },
    "2.6": {
        "title": "货架动态与生存分析",
        "required_tables": ["listing_snapshots", "part2_threshold_registry", "part2_benchmark_registry"],
        "metric_ids": ["listing_survival_dynamics"],
        "quality_targets": {
            "listing_snapshots": 20,
            "part2_threshold_registry": 2,
            "part2_benchmark_registry": 2,
        },
        "analysis_grain": "listing survival event",
        "entity_grain": "listing x platform",
        "time_grain": "snapshot date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.channel"],
        "evidence_refs": ["evidence.listing_snapshots", "evidence.part2_benchmark_registry"],
        "rule_refs": ["gate.shelf_stability", "gate.part2_threshold_registry"],
    },
}


def _confidence_band(dataset: Part2Dataset, section_metrics: dict[str, dict]) -> dict[str, str | float]:
    available_registry_count = sum(
        1
        for value in (
            dataset.part2_source_registry,
            dataset.part2_threshold_registry,
            dataset.part2_benchmark_registry,
            dataset.voc_event_registry,
        )
        if value
    )
    proxy_flags = []
    proxy_share = section_metrics.get("2.1", {}).get("data_quality", {}).get("proxy_transaction_share", 0.0)
    if proxy_share > 0.2:
        proxy_flags.append("proxy_transaction_share_high")
    proxy_flags.extend(section_metrics.get("2.5", {}).get("proxy_usage_flags", []))
    benchmark_coverage = section_metrics.get("2.2", {}).get("benchmark_coverage_ratio", 0.0)
    voc_event_coverage = section_metrics.get("2.5", {}).get("voc_event_coverage_ratio", 0.0)
    confidence_score = clip(
        available_registry_count / 4 * 0.35
        + (1 - min(proxy_share, 1.0)) * 0.25
        + benchmark_coverage * 0.2
        + max(voc_event_coverage, 0.5 if dataset.voc_event_registry else 0.0) * 0.2,
        0.0,
        1.0,
    )
    if confidence_score >= 0.75:
        label = "high"
    elif confidence_score >= 0.55:
        label = "medium"
    else:
        label = "low"
    return {
        "score": round(confidence_score, 4),
        "label": label,
        "proxy_usage_flags": sorted(set(proxy_flags)),
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
            benchmark_registry=dataset.part2_benchmark_registry,
            threshold_registry=dataset.part2_threshold_registry,
        ),
        "2.3": compute_value_gap_analysis(
            dataset.listing_snapshots,
            dataset.sold_transactions,
            benchmark_registry=dataset.part2_benchmark_registry,
        ),
        "2.4": compute_attribute_landscape(
            dataset.product_catalog,
            dataset.sold_transactions,
            assumptions,
        ),
        "2.5": compute_review_analytics(
            dataset.reviews,
            assumptions,
            voc_event_registry=dataset.voc_event_registry,
            threshold_registry=dataset.part2_threshold_registry,
            source_registry=dataset.part2_source_registry,
        ),
        "2.6": compute_listing_dynamics(dataset.listing_snapshots),
    }
    section_metrics["2.1"]["source_registry_count"] = len(dataset.part2_source_registry)
    section_metrics["2.2"]["benchmark_registry_count"] = len(dataset.part2_benchmark_registry)
    section_metrics["2.2"]["threshold_registry_count"] = len(dataset.part2_threshold_registry)
    section_metrics["2.5"]["voc_event_registry_count"] = len(dataset.voc_event_registry)
    section_metrics["2.5"]["source_registry_count"] = len(dataset.part2_source_registry)
    section_metrics["2.5"]["threshold_registry_count"] = len(dataset.part2_threshold_registry)
    section_metrics["2.6"]["threshold_registry_count"] = len(dataset.part2_threshold_registry)
    section_metrics["2.6"]["benchmark_registry_count"] = len(dataset.part2_benchmark_registry)
    decision_summary = build_part2_decision_summary(section_metrics)
    factor_snapshots = {
        "FAC-COMPETITION-HEADROOM": {
            "label": "竞争结构空间因子",
            "value": round(float(decision_summary.get("scorecard", {}).get("structure_headroom", {}).get("score", 0.0)), 4),
            "source_section": "2.1",
        },
        "FAC-PRICING-FIT": {
            "label": "定价甜区匹配因子",
            "value": round(float(decision_summary.get("scorecard", {}).get("pricing_fit", {}).get("score", 0.0)), 4),
            "source_section": "2.2",
        },
        "FAC-WHITESPACE-DEPTH": {
            "label": "白空间深度因子",
            "value": round(float(decision_summary.get("scorecard", {}).get("whitespace_depth", {}).get("score", 0.0)), 4),
            "source_section": "2.4",
        },
        "FAC-SHELF-STABILITY": {
            "label": "货架稳定性因子",
            "value": round(float(decision_summary.get("scorecard", {}).get("shelf_stability", {}).get("score", 0.0)), 4),
            "source_section": "2.6",
        },
        "FAC-VALUE-ADVANTAGE": {
            "label": "价值优势因子",
            "value": round(float(section_metrics["2.3"].get("value_advantage_score", 0.0)), 4),
            "source_section": "2.3",
        },
        "FAC-VOC-RISK": {
            "label": "VOC 风险因子",
            "value": round(float(1 - section_metrics["2.5"].get("voc_risk_score", 0.0)), 4),
            "source_section": "2.5",
        },
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
    report["factor_snapshots"] = factor_snapshots
    report["confidence_band"] = _confidence_band(dataset, section_metrics)
    report["proxy_usage_flags"] = report["confidence_band"]["proxy_usage_flags"]
    report["part2_registry_bindings"] = {
        "part2_source_registry_count": len(dataset.part2_source_registry),
        "part2_threshold_registry_count": len(dataset.part2_threshold_registry),
        "part2_benchmark_registry_count": len(dataset.part2_benchmark_registry),
        "voc_event_registry_count": len(dataset.voc_event_registry),
    }
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
            {
                "key": "competition_headroom_factor",
                "label": "竞争结构空间因子",
                "value": factor_snapshots["FAC-COMPETITION-HEADROOM"]["value"],
                "unit": "score",
            },
            {
                "key": "pricing_fit_factor",
                "label": "定价甜区匹配因子",
                "value": factor_snapshots["FAC-PRICING-FIT"]["value"],
                "unit": "score",
            },
        ],
    )
    report = attach_decision_summary(report, decision_summary)
    report["overview"]["factor_snapshot_count"] = len(factor_snapshots)
    report["overview"]["registry_binding_count"] = sum(report["part2_registry_bindings"].values())
    report["overview"]["confidence_band"] = report["confidence_band"]["label"]
    report["overview"]["proxy_usage_flag_count"] = len(report["proxy_usage_flags"])
    return finalize_report_overview(report)
