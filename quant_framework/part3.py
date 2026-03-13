from __future__ import annotations

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
from .registry import PART3_METRICS
from .uncertainty import build_part3_uncertainty_snapshot
from .validation import build_part3_methodology_validation


PART3_SECTION_STRUCTURE = {
    "3.1": {
        "title": "中国供应端结构分析",
        "required_tables": ["suppliers"],
        "metric_ids": ["supply_structure"],
    },
    "3.2": {
        "title": "国内采购与报价策略分析",
        "required_tables": ["rfq_quotes", "suppliers"],
        "metric_ids": ["rfq_quote_structure"],
    },
    "3.3": {
        "title": "合规、认证与准入门槛分析",
        "required_tables": ["compliance_requirements"],
        "metric_ids": ["compliance_gating"],
    },
    "3.4": {
        "title": "出口路径与物流履约分析",
        "required_tables": ["logistics_quotes", "shipment_events"],
        "metric_ids": ["logistics_route_efficiency"],
    },
    "3.5": {
        "title": "到岸成本与利润安全边际分析",
        "required_tables": ["rfq_quotes", "logistics_quotes", "compliance_requirements", "tariff_tax"],
        "metric_ids": ["landed_cost_margin"],
    },
    "3.6": {
        "title": "风险矩阵与应对策略",
        "required_tables": ["suppliers", "compliance_requirements", "logistics_quotes", "shipment_events"],
        "metric_ids": ["risk_matrix"],
    },
    "3.7": {
        "title": "推荐进入路径与首批执行方案",
        "required_tables": ["rfq_quotes", "logistics_quotes", "suppliers"],
        "metric_ids": ["entry_strategy"],
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
    )
    entry_strategy_metrics = compute_entry_strategy_metrics(
        landed_cost_metrics,
        risk_metrics,
        supply_metrics,
    )

    report = {
        "metadata": {
            "section_structure": PART3_SECTION_STRUCTURE,
            "metric_specs": [metric.__dict__ for metric in PART3_METRICS],
            "assumptions": assumptions.__dict__,
        },
        "sections": {
            "3.1": {
                "title": PART3_SECTION_STRUCTURE["3.1"]["title"],
                "metrics": supply_metrics,
            },
            "3.2": {
                "title": PART3_SECTION_STRUCTURE["3.2"]["title"],
                "metrics": quote_metrics,
            },
            "3.3": {
                "title": PART3_SECTION_STRUCTURE["3.3"]["title"],
                "metrics": compliance_metrics,
            },
            "3.4": {
                "title": PART3_SECTION_STRUCTURE["3.4"]["title"],
                "metrics": logistics_metrics,
            },
            "3.5": {
                "title": PART3_SECTION_STRUCTURE["3.5"]["title"],
                "metrics": landed_cost_metrics,
            },
            "3.6": {
                "title": PART3_SECTION_STRUCTURE["3.6"]["title"],
                "metrics": risk_metrics,
            },
            "3.7": {
                "title": PART3_SECTION_STRUCTURE["3.7"]["title"],
                "metrics": entry_strategy_metrics,
            },
        },
    }
    report["uncertainty"] = build_part3_uncertainty_snapshot(dataset, assumptions)
    report["validation"] = build_part3_methodology_validation(report)
    return report
