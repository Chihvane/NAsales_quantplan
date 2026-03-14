from __future__ import annotations

from .decision_summary import build_part5_decision_summary
from .models import Part5Assumptions, Part5Dataset
from .part5_audit import build_part5_audit_pack, summarize_part5_data_contract
from .part5_alerts import generate_operating_alerts
from .part5_metrics import (
    build_part5_channel_rows,
    compute_data_monitoring_metrics,
    compute_experiment_metrics,
    compute_growth_loop_metrics,
    compute_inventory_cash_metrics,
    compute_operating_goals_metrics,
    compute_pricing_profit_metrics,
    compute_risk_scale_metrics,
)
from .registry import PART5_METRICS
from .reporting import attach_decision_summary, attach_headline_metrics, build_standard_report, finalize_report_overview
from .uncertainty import build_part5_uncertainty_snapshot
from .validation import build_part5_methodology_validation


PART5_SECTION_STRUCTURE = {
    "5.1": {
        "title": "运营目标与门禁指标设计",
        "required_tables": ["kpi_daily_snapshots", "sold_transactions", "returns_claims"],
        "metric_ids": ["operating_goals_gates"],
        "quality_targets": {"kpi_daily_snapshots": 14, "sold_transactions": 10, "returns_claims": 6},
        "analysis_grain": "channel x day",
        "entity_grain": "channel",
        "time_grain": "day",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.sku", "mdm.price_metric"],
        "evidence_refs": ["evidence.kpi_daily_snapshots", "evidence.sold_transactions", "evidence.returns_claims"],
        "rule_refs": ["gate.contribution_margin_guardrail", "gate.return_dispute_band", "gate.scale_stop_exit"],
    },
    "5.2": {
        "title": "数据体系与持续监控机制",
        "required_tables": ["kpi_daily_snapshots", "marketing_spend", "traffic_sessions", "policy_change_log", "channel_rate_cards"],
        "metric_ids": ["data_monitoring_system"],
        "quality_targets": {"kpi_daily_snapshots": 14, "marketing_spend": 8, "traffic_sessions": 8, "policy_change_log": 2, "channel_rate_cards": 6},
        "analysis_grain": "channel x day / week",
        "entity_grain": "channel x fee version",
        "time_grain": "day / week",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.fee_version", "mdm.policy_version"],
        "evidence_refs": ["evidence.kpi_daily_snapshots", "evidence.channel_rate_cards", "evidence.policy_change_log"],
        "rule_refs": ["gate.data_contract", "gate.version_gate", "gate.monitoring_completeness"],
    },
    "5.3": {
        "title": "获客、转化与留存增长机制",
        "required_tables": ["traffic_sessions", "marketing_spend", "customer_cohorts", "kpi_daily_snapshots"],
        "metric_ids": ["growth_loop"],
        "quality_targets": {"traffic_sessions": 8, "marketing_spend": 8, "customer_cohorts": 4, "kpi_daily_snapshots": 14},
        "analysis_grain": "channel x source x cohort",
        "entity_grain": "channel x traffic source",
        "time_grain": "day / cohort month",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.customer_segment", "mdm.traffic_source"],
        "evidence_refs": ["evidence.traffic_sessions", "evidence.marketing_spend", "evidence.customer_cohorts"],
        "rule_refs": ["gate.growth_quality", "gate.payback_control"],
    },
    "5.4": {
        "title": "定价、促销与利润保护策略",
        "required_tables": ["pricing_actions", "sold_transactions", "kpi_daily_snapshots"],
        "metric_ids": ["pricing_profit_protection"],
        "quality_targets": {"pricing_actions": 6, "sold_transactions": 10, "kpi_daily_snapshots": 14},
        "analysis_grain": "sku x channel x pricing action",
        "entity_grain": "sku x channel",
        "time_grain": "pricing action date",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.sku", "mdm.channel", "mdm.price_metric"],
        "evidence_refs": ["evidence.pricing_actions", "evidence.sold_transactions", "evidence.kpi_daily_snapshots"],
        "rule_refs": ["gate.margin_protection", "gate.promo_dependency"],
    },
    "5.5": {
        "title": "履约、库存与现金周转管理",
        "required_tables": ["inventory_positions", "reorder_plan", "cash_flow_snapshots"],
        "metric_ids": ["inventory_cash_control"],
        "quality_targets": {"inventory_positions": 8, "reorder_plan": 4, "cash_flow_snapshots": 8},
        "analysis_grain": "sku x warehouse x day",
        "entity_grain": "sku x warehouse",
        "time_grain": "day",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.sku", "mdm.warehouse", "mdm.channel"],
        "evidence_refs": ["evidence.inventory_positions", "evidence.reorder_plan", "evidence.cash_flow_snapshots"],
        "rule_refs": ["gate.inventory_risk", "gate.cash_burn_control"],
    },
    "5.6": {
        "title": "增量实验与持续优化机制",
        "required_tables": ["experiment_registry", "experiment_assignments", "experiment_metrics", "traffic_sessions"],
        "metric_ids": ["experimentation_system"],
        "quality_targets": {"experiment_registry": 4, "experiment_assignments": 8, "experiment_metrics": 8, "traffic_sessions": 8},
        "analysis_grain": "experiment x variant x day",
        "entity_grain": "experiment",
        "time_grain": "experiment day",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.experiment_registry", "mdm.channel"],
        "evidence_refs": ["evidence.experiment_registry", "evidence.experiment_assignments", "evidence.experiment_metrics"],
        "rule_refs": ["gate.experiment_readiness", "gate.incrementality_control"],
    },
    "5.7": {
        "title": "风险监控、复盘机制与扩张节奏",
        "required_tables": ["policy_change_log", "kpi_daily_snapshots", "cash_flow_snapshots", "returns_claims"],
        "metric_ids": ["risk_scale_loop"],
        "quality_targets": {"policy_change_log": 2, "kpi_daily_snapshots": 14, "cash_flow_snapshots": 8, "returns_claims": 6},
        "analysis_grain": "channel x risk event",
        "entity_grain": "channel",
        "time_grain": "day / week",
        "channel_scope": ["DTC", "Amazon", "TikTok Shop", "eBay", "Walmart", "B2B"],
        "master_data_refs": ["mdm.channel", "mdm.policy_version"],
        "evidence_refs": ["evidence.policy_change_log", "evidence.kpi_daily_snapshots", "evidence.cash_flow_snapshots", "evidence.returns_claims"],
        "rule_refs": ["gate.scale_stop_exit", "gate.policy_blocker", "gate.rollback_runbook"],
        "gate_status_key": "expansion_gate_status",
    },
}


def build_part5_quant_report(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
) -> dict:
    channel_rows = build_part5_channel_rows(dataset, assumptions)
    alert_payload = generate_operating_alerts(dataset, channel_rows, assumptions)
    operating_metrics = compute_operating_goals_metrics(dataset, assumptions, channel_rows, alert_payload)
    data_metrics = compute_data_monitoring_metrics(dataset, channel_rows, assumptions)
    growth_metrics = compute_growth_loop_metrics(dataset, channel_rows)
    pricing_metrics = compute_pricing_profit_metrics(dataset, channel_rows)
    inventory_metrics = compute_inventory_cash_metrics(dataset, assumptions, channel_rows)
    experiment_metrics = compute_experiment_metrics(dataset, assumptions)
    risk_scale_metrics = compute_risk_scale_metrics(
        dataset,
        assumptions,
        channel_rows,
        alert_payload,
        operating_metrics,
        inventory_metrics,
        experiment_metrics,
    )
    risk_scale_metrics["alerts"] = alert_payload

    section_metrics = {
        "5.1": operating_metrics,
        "5.2": data_metrics,
        "5.3": growth_metrics,
        "5.4": pricing_metrics,
        "5.5": inventory_metrics,
        "5.6": experiment_metrics,
        "5.7": risk_scale_metrics,
    }
    report = build_standard_report(
        report_id="part5_quant_report",
        section_structure=PART5_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART5_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part5_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part5_methodology_validation(report)
    report["audit_pack"] = build_part5_audit_pack(dataset)
    report.setdefault("overview", {})["data_contract"] = summarize_part5_data_contract(dataset)
    report = attach_decision_summary(report, build_part5_decision_summary(section_metrics))
    report = attach_headline_metrics(
        report,
        [
            {"key": "operating_health_score", "label": "经营健康分", "value": operating_metrics.get("operating_health_score", 0.0), "unit": "score"},
            {"key": "growth_leverage_score", "label": "增长杠杆分", "value": growth_metrics.get("growth_leverage_score", 0.0), "unit": "score"},
            {"key": "margin_protection_score", "label": "利润保护分", "value": pricing_metrics.get("margin_protection_score", 0.0), "unit": "score"},
            {"key": "scale_readiness_score", "label": "扩张准备度", "value": risk_scale_metrics.get("scale_readiness_score", 0.0), "unit": "score"},
            {"key": "expansion_gate_status", "label": "扩张状态", "value": risk_scale_metrics.get("expansion_gate_status", ""), "unit": "enum"},
        ],
    )
    return finalize_report_overview(report)
