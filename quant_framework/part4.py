from __future__ import annotations

from .decision_summary import build_part4_decision_summary
from .models import Part4Assumptions, Part4Dataset
from .part4_channel_performance_metrics import compute_part4_channel_performance_metrics
from .part4_metrics import (
    compute_b2b_metrics,
    compute_channel_pnl_rows,
    compute_dtc_metrics,
    compute_entry_plan_metrics,
    compute_platform_metrics,
    compute_roi_metrics,
    compute_team_readiness_metrics,
    compute_traffic_metrics,
)
from .part4_optimizer import compute_part4_optimizer
from .part4_simulation import run_part4_roi_monte_carlo
from .part4_stress_suite import compute_part4_stress_suite
from .reporting import attach_decision_summary, attach_headline_metrics, build_standard_report, finalize_report_overview
from .registry import PART4_METRICS
from .stats_utils import clip
from .uncertainty import build_part4_uncertainty_snapshot
from .validation import build_part4_methodology_validation


PART4_SECTION_STRUCTURE = {
    "4.1": {
        "title": "独立站模式可行性分析",
        "required_tables": ["traffic_sessions", "marketing_spend", "customer_cohorts", "landed_cost_scenarios"],
        "metric_ids": ["dtc_feasibility"],
        "quality_targets": {
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "customer_cohorts": 4,
            "landed_cost_scenarios": 6,
        },
        "analysis_grain": "channel x cohort window",
        "entity_grain": "DTC",
        "time_grain": "week / cohort month",
        "channel_scope": ["DTC"],
        "master_data_refs": ["mdm.channel", "mdm.customer_segment", "mdm.sku"],
        "evidence_refs": ["evidence.traffic_sessions", "evidence.marketing_spend", "evidence.customer_cohorts"],
        "rule_refs": ["gate.dtc_feasibility"],
    },
    "4.2": {
        "title": "平台电商模式可行性分析",
        "required_tables": [
            "sold_transactions",
            "traffic_sessions",
            "marketing_spend",
            "channel_rate_cards",
            "landed_cost_scenarios",
            "part4_source_registry",
            "part4_benchmark_registry",
        ],
        "metric_ids": ["platform_channel_fit"],
        "quality_targets": {
            "sold_transactions": 10,
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "channel_rate_cards": 10,
            "landed_cost_scenarios": 6,
            "part4_source_registry": 3,
            "part4_benchmark_registry": 3,
        },
        "analysis_grain": "channel x transaction window",
        "entity_grain": "platform channel",
        "time_grain": "week",
        "channel_scope": ["Amazon", "TikTok Shop", "eBay", "Walmart"],
        "master_data_refs": ["mdm.channel", "mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.sold_transactions", "evidence.channel_rate_cards", "evidence.marketing_spend", "evidence.part4_source_registry", "evidence.part4_benchmark_registry"],
        "rule_refs": ["gate.platform_selection", "gate.part4_threshold_registry"],
    },
    "4.3": {
        "title": "线下经销商与 ToB 模式分析",
        "required_tables": ["b2b_accounts", "landed_cost_scenarios", "sold_transactions"],
        "metric_ids": ["b2b_channel_viability"],
        "quality_targets": {
            "b2b_accounts": 3,
            "landed_cost_scenarios": 2,
            "sold_transactions": 10,
        },
        "analysis_grain": "account x transaction window",
        "entity_grain": "B2B account",
        "time_grain": "week / quarter",
        "channel_scope": ["B2B"],
        "master_data_refs": ["mdm.channel", "mdm.account", "mdm.sku"],
        "evidence_refs": ["evidence.b2b_accounts", "evidence.sold_transactions"],
        "rule_refs": ["gate.b2b_viability"],
    },
    "4.4": {
        "title": "曝光、获客与流量结构分析",
        "required_tables": ["traffic_sessions", "marketing_spend", "part4_source_registry"],
        "metric_ids": ["traffic_structure"],
        "quality_targets": {
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "part4_source_registry": 3,
        },
        "analysis_grain": "channel x source",
        "entity_grain": "channel x traffic source",
        "time_grain": "day / week",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.traffic_source"],
        "evidence_refs": ["evidence.traffic_sessions", "evidence.marketing_spend", "evidence.part4_source_registry"],
        "rule_refs": ["gate.traffic_efficiency"],
    },
    "4.5": {
        "title": "转化效率与 ROI 模型分析",
        "required_tables": [
            "sold_transactions",
            "marketing_spend",
            "returns_claims",
            "inventory_positions",
            "landed_cost_scenarios",
            "channel_rate_cards",
            "part4_threshold_registry",
            "part4_benchmark_registry",
            "part4_stress_registry",
        ],
        "metric_ids": ["roi_unit_economics"],
        "quality_targets": {
            "sold_transactions": 10,
            "marketing_spend": 8,
            "returns_claims": 6,
            "inventory_positions": 8,
            "landed_cost_scenarios": 6,
            "channel_rate_cards": 10,
            "part4_threshold_registry": 2,
            "part4_benchmark_registry": 3,
            "part4_stress_registry": 3,
        },
        "analysis_grain": "channel x roi scenario",
        "entity_grain": "channel",
        "time_grain": "week",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.price_metric", "mdm.sku"],
        "evidence_refs": ["evidence.sold_transactions", "evidence.channel_rate_cards", "evidence.returns_claims", "evidence.part4_benchmark_registry", "evidence.part4_stress_registry"],
        "rule_refs": ["gate.margin_gate", "gate.payback_gate", "gate.loss_gate", "gate.part4_threshold_registry"],
    },
    "4.6": {
        "title": "运营门槛与组织能力要求分析",
        "required_tables": ["experiment_registry", "returns_claims", "inventory_positions", "traffic_sessions"],
        "metric_ids": ["operating_readiness"],
        "quality_targets": {
            "experiment_registry": 4,
            "returns_claims": 6,
            "inventory_positions": 8,
            "traffic_sessions": 8,
        },
        "analysis_grain": "capability score",
        "entity_grain": "channel operating model",
        "time_grain": "planning window",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.experiment_registry"],
        "evidence_refs": ["evidence.experiment_registry", "evidence.inventory_positions", "evidence.returns_claims"],
        "rule_refs": ["gate.readiness_gate"],
    },
    "4.7": {
        "title": "推荐进入路径与 90 天销售执行方案",
        "required_tables": [
            "landed_cost_scenarios",
            "traffic_sessions",
            "marketing_spend",
            "b2b_accounts",
            "experiment_registry",
            "part4_threshold_registry",
            "part4_optimizer_registry",
            "part4_stress_registry",
        ],
        "metric_ids": ["entry_plan"],
        "quality_targets": {
            "landed_cost_scenarios": 6,
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "b2b_accounts": 3,
            "experiment_registry": 4,
            "part4_threshold_registry": 2,
            "part4_optimizer_registry": 1,
            "part4_stress_registry": 3,
        },
        "analysis_grain": "entry plan scenario",
        "entity_grain": "channel portfolio",
        "time_grain": "90-day plan",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.sku", "mdm.account"],
        "evidence_refs": ["evidence.landed_cost_scenarios", "evidence.traffic_sessions", "evidence.marketing_spend", "evidence.part4_optimizer_registry", "evidence.part4_stress_registry"],
        "rule_refs": ["gate.margin_gate", "gate.payback_gate", "gate.loss_gate", "gate.readiness_gate", "gate.part4_threshold_registry", "gate.part4_optimizer_registry"],
        "gate_status_key": "recommendation",
    },
}


def _build_part4_factor_snapshots(section_metrics: dict[str, dict]) -> dict[str, dict]:
    dtc = section_metrics.get("4.1", {})
    platform = section_metrics.get("4.2", {})
    traffic = section_metrics.get("4.4", {})
    roi = section_metrics.get("4.5", {})
    readiness = section_metrics.get("4.6", {})
    entry = section_metrics.get("4.7", {})
    channel_performance = roi.get("channel_performance_metrics", {})
    stress_suite = roi.get("stress_suite", {})
    optimizer = entry.get("optimizer", {})
    monte_carlo = roi.get("monte_carlo", {}).get("overall", {})
    return {
        "FAC-CHANNEL-FIT": {
            "label": "渠道适配因子",
            "value": round(
                max(
                    dtc.get("dtc_fit_score", 0.0),
                    platform.get("best_platform_fit_score", 0.0),
                    entry.get("optimizer", {}).get("best_channel", {}).get("optimizer_priority_score", 0.0),
                ),
                4,
            ),
            "source_section": "4.1-4.3",
        },
        "FAC-TRAFFIC-EFFICIENCY": {
            "label": "流量效率因子",
            "value": round(
                clip(
                    traffic.get("funnel", {}).get("checkout_completion_rate", 0.0) / 0.45 * 0.45
                    + (1 - traffic.get("paid_vs_owned", {}).get("paid", 1.0)) * 0.35
                    + (1 - min(channel_performance.get("average_cac_slippage_ratio", 0.0), 1.0)) * 0.2,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "4.4",
        },
        "FAC-UNIT-ECONOMICS": {
            "label": "单位经济因子",
            "value": round(
                clip(
                    roi.get("blended", {}).get("contribution_margin_rate", 0.0) / 0.18 * 0.45
                    + (1 - min(monte_carlo.get("loss_probability", 1.0) / 0.25, 1.0)) * 0.35
                    + min(optimizer.get("risk_adjusted_profit", 0.0) / 100000.0, 1.0) * 0.2,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "4.5",
        },
        "FAC-PORTFOLIO-RESILIENCE": {
            "label": "组合韧性因子",
            "value": round(
                clip(
                    stress_suite.get("robustness_score", 0.0) * 0.45
                    + (1 - min(monte_carlo.get("loss_probability", 1.0), 1.0)) * 0.3
                    + clip(monte_carlo.get("risk_adjusted", {}).get("margin_rate_tail_ratio", 0.0) / 2.0, 0.0, 1.0) * 0.25,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "4.5",
        },
        "FAC-EXECUTION-FRICTION": {
            "label": "执行摩擦因子",
            "value": round(1 - channel_performance.get("average_execution_friction_score", 0.0), 4),
            "source_section": "4.5-4.6",
        },
        "FAC-SCALE-READINESS": {
            "label": "放量承接因子",
            "value": round(
                clip(
                    readiness.get("readiness_score", 0.0) * 0.7
                    + (1 - min(len(entry.get("top_risks", [])) / 5.0, 1.0)) * 0.3,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "4.6-4.7",
        },
    }


def _part4_confidence_band(dataset: Part4Dataset, section_metrics: dict[str, dict]) -> dict[str, str | float | list[str]]:
    available_registry_count = sum(
        1
        for value in (
            dataset.part4_source_registry,
            dataset.part4_threshold_registry,
            dataset.part4_benchmark_registry,
            dataset.part4_optimizer_registry,
            dataset.part4_stress_registry,
        )
        if value
    )
    channel_performance = section_metrics.get("4.5", {}).get("channel_performance_metrics", {})
    stress_suite = section_metrics.get("4.5", {}).get("stress_suite", {})
    proxy_usage_flags = []
    if not dataset.part4_source_registry:
        proxy_usage_flags.append("missing_part4_source_registry")
    if not dataset.part4_benchmark_registry:
        proxy_usage_flags.append("missing_part4_benchmark_registry")
    if not dataset.part4_optimizer_registry:
        proxy_usage_flags.append("missing_part4_optimizer_registry")
    if not dataset.part4_stress_registry:
        proxy_usage_flags.append("missing_part4_stress_registry")
    if channel_performance.get("benchmark_coverage_ratio", 0.0) < 0.6:
        proxy_usage_flags.append("low_benchmark_coverage")
    if channel_performance.get("source_health", {}).get("health_score", 0.0) < 0.55:
        proxy_usage_flags.append("source_health_weak")
    if stress_suite.get("scenario_count", 0) < 3:
        proxy_usage_flags.append("stress_suite_thin")

    confidence_score = clip(
        available_registry_count / 5 * 0.35
        + channel_performance.get("source_health", {}).get("health_score", 0.0) * 0.2
        + channel_performance.get("benchmark_coverage_ratio", 0.0) * 0.15
        + channel_performance.get("threshold_coverage_ratio", 0.0) * 0.1
        + stress_suite.get("robustness_score", 0.0) * 0.1
        + min(section_metrics.get("4.7", {}).get("optimizer", {}).get("feasible_ratio", 0.0), 1.0) * 0.1,
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
        "proxy_usage_flags": sorted(set(proxy_usage_flags)),
    }


def build_part4_quant_report(
    dataset: Part4Dataset,
    assumptions: Part4Assumptions,
) -> dict:
    channel_rows = compute_channel_pnl_rows(dataset, assumptions)
    monte_carlo = run_part4_roi_monte_carlo(channel_rows, assumptions)
    traffic_metrics = compute_traffic_metrics(dataset, channel_rows)
    channel_performance_metrics = compute_part4_channel_performance_metrics(
        channel_rows,
        dataset.part4_benchmark_registry,
        dataset.part4_threshold_registry,
        dataset.part4_source_registry,
    )
    dtc_metrics = compute_dtc_metrics(channel_rows, assumptions)
    platform_metrics = compute_platform_metrics(channel_rows, assumptions)
    b2b_metrics = compute_b2b_metrics(channel_rows, dataset.b2b_accounts)
    roi_metrics = compute_roi_metrics(channel_rows, monte_carlo)
    roi_metrics["channel_performance_metrics"] = channel_performance_metrics
    stress_suite = compute_part4_stress_suite(channel_rows, dataset.part4_stress_registry)
    roi_metrics["stress_suite"] = stress_suite
    team_metrics = compute_team_readiness_metrics(
        dataset,
        channel_rows,
        assumptions,
        traffic_metrics,
    )
    optimizer_metrics = compute_part4_optimizer(
        channel_rows,
        monte_carlo,
        traffic_metrics,
        channel_performance_metrics,
        dataset.part4_optimizer_registry,
        assumptions,
    )
    entry_plan_metrics = compute_entry_plan_metrics(
        channel_rows,
        dtc_metrics,
        platform_metrics,
        b2b_metrics,
        traffic_metrics,
        roi_metrics,
        team_metrics,
        assumptions,
    )
    entry_plan_metrics["optimizer"] = optimizer_metrics
    if optimizer_metrics.get("best_channel"):
        entry_plan_metrics["optimized_primary_channel"] = optimizer_metrics["best_channel"].get("channel", "")
        entry_plan_metrics["optimizer_capital_allocation"] = optimizer_metrics.get(
            "recommended_capital_allocation",
            {},
        )

    section_metrics = {
        "4.1": dtc_metrics,
        "4.2": platform_metrics,
        "4.3": b2b_metrics,
        "4.4": traffic_metrics,
        "4.5": roi_metrics,
        "4.6": team_metrics,
        "4.7": entry_plan_metrics,
    }
    factor_snapshots = _build_part4_factor_snapshots(section_metrics)
    report = build_standard_report(
        report_id="part4_quant_report",
        section_structure=PART4_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART4_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part4_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part4_methodology_validation(report)
    report["factor_snapshots"] = factor_snapshots
    report["confidence_band"] = _part4_confidence_band(dataset, section_metrics)
    report["proxy_usage_flags"] = report["confidence_band"]["proxy_usage_flags"]
    report["execution_friction_flags"] = channel_performance_metrics.get("execution_friction_flags", [])
    report["part4_optimizer_runs"] = optimizer_metrics.get("optimizer_runs", [])
    report = attach_decision_summary(report, build_part4_decision_summary(section_metrics))
    report = attach_headline_metrics(
        report,
        [
            {
                "key": "recommendation",
                "label": "进入建议",
                "value": entry_plan_metrics.get("recommendation", ""),
                "unit": "enum",
            },
            {
                "key": "primary_channel",
                "label": "主攻渠道",
                "value": entry_plan_metrics.get("primary_channel", ""),
                "unit": "channel",
            },
            {
                "key": "best_platform",
                "label": "最佳平台",
                "value": platform_metrics.get("best_platform", ""),
                "unit": "channel",
            },
            {
                "key": "blended_margin_rate",
                "label": "综合贡献毛利率",
                "value": round(roi_metrics.get("blended", {}).get("contribution_margin_rate", 0.0), 4),
                "unit": "ratio",
            },
            {
                "key": "loss_probability",
                "label": "总体亏损概率",
                "value": round(roi_metrics.get("monte_carlo", {}).get("overall", {}).get("loss_probability", 0.0), 4),
                "unit": "ratio",
            },
            {
                "key": "readiness_score",
                "label": "组织承接分",
                "value": round(team_metrics.get("readiness_score", 0.0), 4),
                "unit": "score",
            },
            {
                "key": "portfolio_resilience_factor",
                "label": "组合韧性因子",
                "value": factor_snapshots["FAC-PORTFOLIO-RESILIENCE"]["value"],
                "unit": "score",
            },
            {
                "key": "execution_friction_factor",
                "label": "执行摩擦因子",
                "value": factor_snapshots["FAC-EXECUTION-FRICTION"]["value"],
                "unit": "score",
            },
        ],
    )
    report["overview"]["factor_snapshot_count"] = len(factor_snapshots)
    report["overview"]["confidence_band"] = report["confidence_band"]["label"]
    report["overview"]["proxy_usage_flag_count"] = len(report["proxy_usage_flags"])
    report["overview"]["execution_friction_flag_count"] = len(report["execution_friction_flags"])
    report["overview"]["optimizer_run_count"] = len(report["part4_optimizer_runs"])
    return finalize_report_overview(report)
