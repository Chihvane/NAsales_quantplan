from __future__ import annotations

from .models import Part4Assumptions, Part4Dataset
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
from .part4_simulation import run_part4_roi_monte_carlo
from .reporting import attach_headline_metrics, build_standard_report, finalize_report_overview
from .registry import PART4_METRICS
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
    },
    "4.2": {
        "title": "平台电商模式可行性分析",
        "required_tables": ["sold_transactions", "traffic_sessions", "marketing_spend", "channel_rate_cards", "landed_cost_scenarios"],
        "metric_ids": ["platform_channel_fit"],
        "quality_targets": {
            "sold_transactions": 10,
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "channel_rate_cards": 10,
            "landed_cost_scenarios": 6,
        },
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
    },
    "4.4": {
        "title": "曝光、获客与流量结构分析",
        "required_tables": ["traffic_sessions", "marketing_spend"],
        "metric_ids": ["traffic_structure"],
        "quality_targets": {
            "traffic_sessions": 8,
            "marketing_spend": 8,
        },
    },
    "4.5": {
        "title": "转化效率与 ROI 模型分析",
        "required_tables": ["sold_transactions", "marketing_spend", "returns_claims", "inventory_positions", "landed_cost_scenarios", "channel_rate_cards"],
        "metric_ids": ["roi_unit_economics"],
        "quality_targets": {
            "sold_transactions": 10,
            "marketing_spend": 8,
            "returns_claims": 6,
            "inventory_positions": 8,
            "landed_cost_scenarios": 6,
            "channel_rate_cards": 10,
        },
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
    },
    "4.7": {
        "title": "推荐进入路径与 90 天销售执行方案",
        "required_tables": ["landed_cost_scenarios", "traffic_sessions", "marketing_spend", "b2b_accounts", "experiment_registry"],
        "metric_ids": ["entry_plan"],
        "quality_targets": {
            "landed_cost_scenarios": 6,
            "traffic_sessions": 8,
            "marketing_spend": 8,
            "b2b_accounts": 3,
            "experiment_registry": 4,
        },
    },
}


def build_part4_quant_report(
    dataset: Part4Dataset,
    assumptions: Part4Assumptions,
) -> dict:
    channel_rows = compute_channel_pnl_rows(dataset, assumptions)
    monte_carlo = run_part4_roi_monte_carlo(channel_rows, assumptions)
    dtc_metrics = compute_dtc_metrics(channel_rows, assumptions)
    platform_metrics = compute_platform_metrics(channel_rows, assumptions)
    b2b_metrics = compute_b2b_metrics(channel_rows, dataset.b2b_accounts)
    traffic_metrics = compute_traffic_metrics(dataset, channel_rows)
    roi_metrics = compute_roi_metrics(channel_rows, monte_carlo)
    team_metrics = compute_team_readiness_metrics(
        dataset,
        channel_rows,
        assumptions,
        traffic_metrics,
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

    section_metrics = {
        "4.1": dtc_metrics,
        "4.2": platform_metrics,
        "4.3": b2b_metrics,
        "4.4": traffic_metrics,
        "4.5": roi_metrics,
        "4.6": team_metrics,
        "4.7": entry_plan_metrics,
    }
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
        ],
    )
    return finalize_report_overview(report)
