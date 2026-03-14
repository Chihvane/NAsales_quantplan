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
from .part3_simulation import run_landed_cost_monte_carlo
from .reporting import (
    attach_decision_summary,
    attach_headline_metrics,
    build_standard_report,
    finalize_report_overview,
)
from .registry import PART3_METRICS
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
        "required_tables": ["rfq_quotes", "suppliers"],
        "metric_ids": ["rfq_quote_structure"],
        "quality_targets": {"rfq_quotes": 10, "suppliers": 10},
        "analysis_grain": "supplier x quote",
        "entity_grain": "supplier x incoterm x moq tier",
        "time_grain": "quote date",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.sku"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.suppliers"],
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
        "required_tables": ["rfq_quotes", "logistics_quotes", "compliance_requirements", "tariff_tax"],
        "metric_ids": ["landed_cost_margin"],
        "quality_targets": {
            "rfq_quotes": 10,
            "logistics_quotes": 5,
            "compliance_requirements": 5,
            "tariff_tax": 2,
        },
        "analysis_grain": "scenario row",
        "entity_grain": "supplier x route x incoterm",
        "time_grain": "quote effective window",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.route", "mdm.price_metric"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.logistics_quotes", "evidence.tariff_tax"],
        "rule_refs": ["gate.margin_safety", "gate.landed_cost_control"],
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
        "required_tables": ["rfq_quotes", "logistics_quotes", "suppliers"],
        "metric_ids": ["entry_strategy"],
        "quality_targets": {"rfq_quotes": 10, "logistics_quotes": 5, "suppliers": 10},
        "analysis_grain": "entry scenario",
        "entity_grain": "supplier x route x incoterm",
        "time_grain": "launch batch",
        "channel_scope": ["supply_side"],
        "master_data_refs": ["mdm.supplier", "mdm.route", "mdm.sku"],
        "evidence_refs": ["evidence.rfq_quotes", "evidence.logistics_quotes", "evidence.suppliers"],
        "rule_refs": ["gate.supplier_readiness", "gate.margin_safety", "gate.risk_control"],
        "gate_status_key": "recommendation",
    },
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
    )
    landed_cost_metrics["monte_carlo"] = monte_carlo
    risk_metrics = compute_risk_matrix_metrics(
        dataset.suppliers,
        dataset.compliance_requirements,
        dataset.logistics_quotes,
        dataset.shipment_events,
        landed_cost_metrics,
        assumptions,
        supply_metrics=supply_metrics,
    )
    entry_strategy_metrics = compute_entry_strategy_metrics(
        landed_cost_metrics,
        risk_metrics,
        supply_metrics,
    )

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
    report = attach_decision_summary(report, build_part3_decision_summary(section_metrics))
    return finalize_report_overview(report)
