from .metrics import (
    compute_bottom_up_market_size,
    compute_channel_metrics,
    compute_customer_profile,
    compute_demand_metrics,
    compute_listed_price_metrics,
    compute_market_size_input_panel,
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
        "required_tables": ["search_trends", "region_demand", "event_library"],
        "metric_ids": [
            "demand_growth_rate",
            "market_heat_coefficient",
            "seasonality_index",
            "regional_demand_share",
            "demand_sales_lag_signal",
        ],
        "quality_targets": {"search_trends": 12, "region_demand": 5, "event_library": 3},
        "analysis_grain": "month x keyword / region",
        "entity_grain": "keyword / region",
        "time_grain": "month",
        "channel_scope": ["marketwide"],
        "master_data_refs": ["mdm.calendar", "mdm.region"],
        "evidence_refs": ["evidence.search_trends", "evidence.region_demand", "evidence.event_library"],
        "rule_refs": ["gate.market_entry", "gate.demand_stability", "gate.event_sensitivity"],
    },
    "1.2": {
        "title": "客户画像分析",
        "required_tables": ["customer_segments"],
        "metric_ids": ["customer_distribution"],
        "quality_targets": {"customer_segments": 12},
        "analysis_grain": "segment bucket",
        "entity_grain": "customer segment",
        "time_grain": "study window",
        "channel_scope": ["marketwide"],
        "master_data_refs": ["mdm.customer_segment"],
        "evidence_refs": ["evidence.customer_segments"],
        "rule_refs": ["gate.customer_fit"],
    },
    "1.3": {
        "title": "市场规模分析",
        "required_tables": ["listings", "market_size_inputs"],
        "metric_ids": [
            "bottom_up_market_size",
            "top_down_market_size",
            "market_size_reference_panel",
            "market_hhi",
        ],
        "quality_targets": {"listings": 8, "market_size_inputs": 2},
        "analysis_grain": "listing sample / market panel row",
        "entity_grain": "market segment",
        "time_grain": "annualized window",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.listings", "evidence.market_size_inputs"],
        "rule_refs": ["gate.market_entry", "gate.market_scale"],
    },
    "1.4": {
        "title": "购买渠道分析",
        "required_tables": ["channels", "channel_benchmarks"],
        "metric_ids": [
            "channel_share",
            "channel_conversion_rate",
            "channel_benchmark_gap",
        ],
        "quality_targets": {"channels": 4, "channel_benchmarks": 3},
        "analysis_grain": "channel",
        "entity_grain": "channel",
        "time_grain": "analysis window",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel"],
        "evidence_refs": ["evidence.channel_metrics", "evidence.channel_benchmarks"],
        "rule_refs": ["gate.channel_selection"],
    },
    "1.5": {
        "title": "货架商品价格分析",
        "required_tables": ["listings"],
        "metric_ids": [
            "listed_price_bands",
            "brand_premium",
        ],
        "quality_targets": {"listings": 8},
        "analysis_grain": "listing",
        "entity_grain": "sku x platform",
        "time_grain": "snapshot window",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.listings"],
        "rule_refs": ["gate.price_band_fit"],
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
        "analysis_grain": "transaction row",
        "entity_grain": "sku x platform",
        "time_grain": "transaction date",
        "channel_scope": ["Amazon", "eBay", "TikTok Shop", "Walmart"],
        "master_data_refs": ["mdm.sku", "mdm.price_metric", "mdm.channel"],
        "evidence_refs": ["evidence.transactions"],
        "rule_refs": ["gate.price_realization"],
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
    market_size_input_panel = compute_market_size_input_panel(
        dataset.market_size_inputs,
        assumptions,
    )
    section_metrics = {
        "1.1": compute_demand_metrics(
            dataset.search_trends,
            dataset.region_demand,
            dataset.transactions,
        ),
        "1.2": compute_customer_profile(dataset.customer_segments),
        "1.3": {
            "top_down": top_down,
            "bottom_up": bottom_up,
            "market_size_inputs": market_size_input_panel,
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
        "1.4": compute_channel_metrics(dataset.channels, dataset.channel_benchmarks),
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
                "key": "heat_volatility_coefficient",
                "label": "市场热度波动系数",
                "value": round(section_metrics["1.1"].get("trend", {}).get("heat_volatility_coefficient", 0.0), 4),
                "unit": "ratio",
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
