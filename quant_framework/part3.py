from __future__ import annotations

from .decision_summary import build_part3_decision_summary
from .models import Part3Assumptions, Part3Dataset
from .part3_metrics import (
    compute_compliance_metrics,
    compute_entry_strategy_metrics,
    compute_landed_cost_metrics,
    compute_logistics_metrics,
    compute_quote_strategy_metrics,
    compute_risk_matrix_metrics,
    compute_supply_structure_metrics,
)
from .part3_optimizer import compute_part3_optimizer
from .part3_risk_metrics import compute_part3_risk_metrics
from .part3_simulation import run_landed_cost_monte_carlo
from .reporting import (
    attach_decision_summary,
    attach_headline_metrics,
    build_standard_report,
    finalize_report_overview,
)
from .registry import PART3_METRICS
from .stats_utils import clip
from .uncertainty import build_part3_uncertainty_snapshot
from .validation import build_part3_methodology_validation


PART3_SECTION_STRUCTURE = {
    "3.1": {
        "title": "中国供应端结构分析",
        "required_tables": ["suppliers"],
        "metric_ids": ["supply_structure"],
        "quality_targets": {"suppliers": 10},
        "analysis_grain": "supplier",
        "entity_grain": "supplier",
        "time_grain": "supplier profile version",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier"],
        "evidence_refs": ["evidence.suppliers"],
        "rule_refs": ["gate.supplier_readiness"],
    },
    "3.2": {
        "title": "国内采购与报价策略分析",
        "required_tables": ["rfq_quotes", "suppliers", "part3_source_registry"],
        "metric_ids": ["rfq_quote_structure"],
        "quality_targets": {"rfq_quotes": 10, "suppliers": 10, "part3_source_registry": 3},
        "analysis_grain": "supplier x quote",
        "entity_grain": "supplier x incoterm x moq tier",
        "time_grain": "quote date",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.sku"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.suppliers", "evidence.part3_source_registry"],
        "rule_refs": ["gate.procurement_feasibility"],
    },
    "3.3": {
        "title": "合规、认证与准入门槛分析",
        "required_tables": ["compliance_requirements"],
        "metric_ids": ["compliance_gating"],
        "quality_targets": {"compliance_requirements": 5},
        "analysis_grain": "compliance item",
        "entity_grain": "regulation x product class",
        "time_grain": "effective window",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.compliance_class"],
        "evidence_refs": ["evidence.compliance_requirements"],
        "rule_refs": ["gate.compliance_blocker"],
    },
    "3.4": {
        "title": "出口路径与物流履约分析",
        "required_tables": ["logistics_quotes", "shipment_events"],
        "metric_ids": ["logistics_route_efficiency"],
        "quality_targets": {"logistics_quotes": 5, "shipment_events": 5},
        "analysis_grain": "route quote / shipment event",
        "entity_grain": "route x mode",
        "time_grain": "shipment event date",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.route", "mdm.port"],
        "evidence_refs": ["evidence.logistics_quotes", "evidence.shipment_events"],
        "rule_refs": ["gate.route_feasibility"],
    },
    "3.5": {
        "title": "到岸成本与利润安全边际分析",
        "required_tables": [
            "rfq_quotes",
            "logistics_quotes",
            "compliance_requirements",
            "tariff_tax",
            "part3_threshold_registry",
            "part3_scenario_registry",
        ],
        "metric_ids": ["landed_cost_margin"],
        "quality_targets": {
            "rfq_quotes": 10,
            "logistics_quotes": 5,
            "compliance_requirements": 5,
            "tariff_tax": 2,
            "part3_threshold_registry": 2,
            "part3_scenario_registry": 3,
        },
        "analysis_grain": "scenario row",
        "entity_grain": "supplier x route x incoterm",
        "time_grain": "quote effective window",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.route", "mdm.price_metric"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.logistics_quotes", "evidence.tariff_tax", "evidence.part3_scenario_registry"],
        "rule_refs": ["gate.margin_safety", "gate.landed_cost_control", "gate.part3_threshold_registry"],
    },
    "3.6": {
        "title": "风险矩阵与应对策略",
        "required_tables": ["suppliers", "compliance_requirements", "logistics_quotes", "shipment_events"],
        "metric_ids": ["risk_matrix"],
        "quality_targets": {
            "suppliers": 10,
            "compliance_requirements": 5,
            "logistics_quotes": 5,
            "shipment_events": 5,
        },
        "analysis_grain": "risk row",
        "entity_grain": "supplier x route x risk family",
        "time_grain": "risk review window",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.route"],
        "evidence_refs": ["evidence.suppliers", "evidence.shipment_events", "evidence.compliance_requirements"],
        "rule_refs": ["gate.risk_control"],
    },
    "3.7": {
        "title": "推荐进入路径与首批执行方案",
        "required_tables": [
            "rfq_quotes",
            "logistics_quotes",
            "suppliers",
            "part3_threshold_registry",
            "part3_scenario_registry",
            "part3_optimizer_registry",
        ],
        "metric_ids": ["entry_strategy"],
        "quality_targets": {
            "rfq_quotes": 10,
            "logistics_quotes": 5,
            "suppliers": 10,
            "part3_threshold_registry": 2,
            "part3_scenario_registry": 3,
            "part3_optimizer_registry": 1,
        },
        "analysis_grain": "entry scenario",
        "entity_grain": "supplier x route x incoterm",
        "time_grain": "launch batch",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.route", "mdm.sku"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.logistics_quotes", "evidence.suppliers", "evidence.part3_optimizer_registry"],
        "rule_refs": ["gate.supplier_readiness", "gate.margin_safety", "gate.risk_control", "gate.part3_optimizer_registry"],
        "gate_status_key": "recommendation",
    },
}


def _build_part3_factor_snapshots(section_metrics: dict[str, dict]) -> dict[str, dict]:
    supply = section_metrics.get("3.1", {})
    quote = section_metrics.get("3.2", {})
    compliance = section_metrics.get("3.3", {})
    logistics = section_metrics.get("3.4", {})
    landed = section_metrics.get("3.5", {})
    risk = section_metrics.get("3.6", {})
    entry = section_metrics.get("3.7", {})
    risk_tail = landed.get("part3_risk_metrics", {})
    quote_quality = quote.get("quote_quality", {})
    supplier_coverage = quote.get("sampled_supplier_coverage", {}).get("coverage_ratio", 0.0)
    mandatory_days = float(compliance.get("mandatory_estimated_days", 0.0))
    mandatory_cost_per_unit = float(compliance.get("mandatory_cost_per_unit", 0.0))
    best_scenario = landed.get("best_scenario", {})
    margin_floor = max(float(risk_tail.get("margin_floor", 0.15)), 0.01)
    margin_rate = float(best_scenario.get("net_margin_rate", 0.0))
    logistics_reliability = clip(
        float(logistics.get("on_time_rate", 0.0)) * 0.5
        + float(logistics.get("event_coverage_score", 0.0)) * 0.2
        + max(0.0, 1 - float(logistics.get("delay_rate", 0.0))) * 0.3,
        0.0,
        1.0,
    )
    compliance_readiness = clip(
        max(0.0, 1 - mandatory_days / 120.0) * 0.35
        + max(0.0, 1 - mandatory_cost_per_unit / 100.0) * 0.25
        + max(0.0, 1 - float(compliance.get("high_risk_mandatory_share", 1.0))) * 0.4,
        0.0,
        1.0,
    )
    margin_safety = clip(
        min(margin_rate / margin_floor, 1.5) / 1.5 * 0.55
        + max(0.0, 1 - float(risk_tail.get("margin_floor_breach_probability", 1.0))) * 0.3
        + max(0.0, 1 - float(risk_tail.get("tail_risk_score", 1.0))) * 0.15,
        0.0,
        1.0,
    )
    execution_risk_control = clip(
        float(entry.get("execution_confidence_score", 0.0)) * 0.55
        + float(entry.get("optimizer", {}).get("feasible_ratio", 0.0)) * 0.3
        + max(0.0, 1 - float(risk.get("overall_risk_score", 1.0))) * 0.15,
        0.0,
        1.0,
    )
    return {
        "FAC-SUPPLY-ROBUSTNESS": {
            "label": "供应链韧性因子",
            "value": round(
                clip(
                    float(supply.get("supply_maturity_score", 0.0)) * 0.6
                    + max(0.0, 1 - float(risk.get("overall_risk_score", 1.0))) * 0.4,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "3.1-3.6",
        },
        "FAC-QUOTE-QUALITY": {
            "label": "报价质量因子",
            "value": round(
                clip(
                    float(quote_quality.get("average_quote_confidence", 0.0)) * 0.75
                    + float(supplier_coverage) * 0.25,
                    0.0,
                    1.0,
                ),
                4,
            ),
            "source_section": "3.2",
        },
        "FAC-COMPLIANCE-READINESS": {
            "label": "合规准备度因子",
            "value": round(compliance_readiness, 4),
            "source_section": "3.3",
        },
        "FAC-LOGISTICS-RELIABILITY": {
            "label": "物流可靠性因子",
            "value": round(logistics_reliability, 4),
            "source_section": "3.4",
        },
        "FAC-MARGIN-SAFETY": {
            "label": "利润安全边际因子",
            "value": round(margin_safety, 4),
            "source_section": "3.5",
        },
        "FAC-EXECUTION-RISK": {
            "label": "执行风险控制因子",
            "value": round(execution_risk_control, 4),
            "source_section": "3.6-3.7",
        },
    }


def _part3_confidence_band(dataset: Part3Dataset, section_metrics: dict[str, dict]) -> dict[str, str | float | list[str]]:
    available_registry_count = sum(
        1
        for value in (
            dataset.part3_source_registry,
            dataset.part3_threshold_registry,
            dataset.part3_scenario_registry,
            dataset.part3_optimizer_registry,
        )
        if value
    )
    supply = section_metrics.get("3.1", {})
    quote_quality = section_metrics.get("3.2", {}).get("quote_quality", {})
    logistics = section_metrics.get("3.4", {})
    risk_tail = section_metrics.get("3.5", {}).get("part3_risk_metrics", {})
    optimizer = section_metrics.get("3.7", {}).get("optimizer", {})
    proxy_usage_flags: list[str] = []
    if not dataset.part3_source_registry:
        proxy_usage_flags.append("missing_part3_source_registry")
    if not dataset.part3_threshold_registry:
        proxy_usage_flags.append("missing_part3_threshold_registry")
    if not dataset.part3_scenario_registry:
        proxy_usage_flags.append("missing_part3_scenario_registry")
    if not dataset.part3_optimizer_registry:
        proxy_usage_flags.append("missing_part3_optimizer_registry")
    if float(supply.get("sample_confidence_score", 0.0)) < 0.6:
        proxy_usage_flags.append("supplier_sample_confidence_weak")
    if float(quote_quality.get("average_quote_confidence", 0.0)) < 0.75:
        proxy_usage_flags.append("quote_confidence_weak")
    if float(logistics.get("event_coverage_score", 0.0)) < 0.6:
        proxy_usage_flags.append("shipment_event_coverage_thin")
    if float(risk_tail.get("tail_risk_score", 0.0)) > 0.45:
        proxy_usage_flags.append("tail_risk_elevated")
    if float(optimizer.get("feasible_ratio", 0.0)) < 0.25:
        proxy_usage_flags.append("optimizer_feasible_ratio_thin")
    confidence_score = clip(
        available_registry_count / 4 * 0.3
        + float(supply.get("sample_confidence_score", 0.0)) * 0.2
        + float(quote_quality.get("average_quote_confidence", 0.0)) * 0.15
        + float(logistics.get("event_coverage_score", 0.0)) * 0.1
        + max(0.0, 1 - float(risk_tail.get("tail_risk_score", 1.0))) * 0.1
        + float(optimizer.get("feasible_ratio", 0.0)) * 0.1
        + float(section_metrics.get("3.7", {}).get("execution_confidence_score", 0.0)) * 0.05,
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


def build_part3_quant_report(
    dataset: Part3Dataset,
    assumptions: Part3Assumptions,
) -> dict:
    supply_metrics = compute_supply_structure_metrics(dataset.suppliers)
    quote_metrics = compute_quote_strategy_metrics(dataset.rfq_quotes, dataset.suppliers)
    compliance_metrics = compute_compliance_metrics(
        dataset.compliance_requirements,
        assumptions,
    )
    logistics_metrics = compute_logistics_metrics(
        dataset.logistics_quotes,
        dataset.shipment_events,
    )
    landed_cost_metrics = compute_landed_cost_metrics(
        dataset.rfq_quotes,
        dataset.logistics_quotes,
        dataset.compliance_requirements,
        dataset.tariff_tax,
        assumptions,
        dataset.suppliers,
    )
    best_route_lookup = {
        row["route_id"]: row
        for row in logistics_metrics.get("best_routes", [])
    }
    monte_carlo = run_landed_cost_monte_carlo(
        landed_cost_metrics.get("best_scenario", {}),
        assumptions,
        route_volatility_score=best_route_lookup.get(
            landed_cost_metrics.get("best_scenario", {}).get("route_id", ""),
            {},
        ).get("volatility_score", 0.2),
        return_raw_samples=True,
    )
    part3_risk_metrics = compute_part3_risk_metrics(
        landed_cost_metrics,
        monte_carlo,
        assumptions,
        dataset.part3_threshold_registry,
        dataset.part3_scenario_registry,
    )
    landed_cost_metrics["monte_carlo"] = monte_carlo
    landed_cost_metrics["part3_risk_metrics"] = part3_risk_metrics
    risk_metrics = compute_risk_matrix_metrics(
        dataset.suppliers,
        dataset.compliance_requirements,
        dataset.logistics_quotes,
        dataset.shipment_events,
        landed_cost_metrics,
        assumptions,
        supply_metrics=supply_metrics,
    )
    risk_metrics["tail_risk"] = part3_risk_metrics
    optimizer_metrics = compute_part3_optimizer(
        landed_cost_metrics,
        part3_risk_metrics,
        dataset.part3_optimizer_registry,
        assumptions,
    )
    entry_strategy_metrics = compute_entry_strategy_metrics(
        landed_cost_metrics,
        risk_metrics,
        supply_metrics,
        optimizer_metrics=optimizer_metrics,
    )
    entry_strategy_metrics["optimizer"] = optimizer_metrics
    if "raw_samples" in landed_cost_metrics["monte_carlo"]:
        landed_cost_metrics["monte_carlo"].pop("raw_samples")

    section_metrics = {
        "3.1": supply_metrics,
        "3.2": quote_metrics,
        "3.3": compliance_metrics,
        "3.4": logistics_metrics,
        "3.5": landed_cost_metrics,
        "3.6": risk_metrics,
        "3.7": entry_strategy_metrics,
    }
    report = build_standard_report(
        report_id="part3_quant_report",
        section_structure=PART3_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART3_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part3_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part3_methodology_validation(report)
    report = attach_headline_metrics(
        report,
        [
            {
                "key": "recommendation",
                "label": "进入建议",
                "value": entry_strategy_metrics.get("recommendation", ""),
                "unit": "enum",
            },
            {
                "key": "best_landed_cost",
                "label": "最佳到岸成本",
                "value": round(landed_cost_metrics.get("best_scenario", {}).get("landed_cost", 0.0), 2),
                "unit": "USD",
            },
            {
                "key": "best_net_margin_rate",
                "label": "最佳净利率",
                "value": round(landed_cost_metrics.get("best_scenario", {}).get("net_margin_rate", 0.0), 4),
                "unit": "ratio",
            },
            {
                "key": "overall_risk_level",
                "label": "总体风险等级",
                "value": risk_metrics.get("overall_risk_level", ""),
                "unit": "level",
            },
            {
                "key": "recommended_path",
                "label": "推荐路径",
                "value": (
                    f"{entry_strategy_metrics.get('recommended_supplier', {}).get('supplier_id', '')}"
                    f" / {entry_strategy_metrics.get('recommended_path', {}).get('incoterm', '')}"
                    f" / {entry_strategy_metrics.get('recommended_path', {}).get('shipping_mode', '')}"
                ).strip(" /"),
                "unit": "path",
            },
        ],
    )
    factor_snapshots = _build_part3_factor_snapshots(section_metrics)
    report["factor_snapshots"] = factor_snapshots
    report["confidence_band"] = _part3_confidence_band(dataset, section_metrics)
    report["proxy_usage_flags"] = report["confidence_band"]["proxy_usage_flags"]
    report = attach_decision_summary(report, build_part3_decision_summary(section_metrics))
    report = finalize_report_overview(report)
    report["overview"]["factor_snapshot_count"] = len(factor_snapshots)
    report["overview"]["confidence_band"] = report["confidence_band"]["label"]
    report["overview"]["proxy_usage_flag_count"] = len(report["proxy_usage_flags"])
    return report
