from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from statistics import mean, median

from .models import (
    ComplianceRequirementRecord,
    LogisticsQuoteRecord,
    Part3Assumptions,
    RFQQuoteRecord,
    ShipmentEventRecord,
    SupplierRecord,
    TariffTaxRecord,
)


def _safe_divide(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def _normalized_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 1.0
    return 1 - ((value - min_value) / (max_value - min_value))


def _level_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _days_between(start: str, end: str) -> int:
    return (_parse_date(end) - _parse_date(start)).days


def _quoted_unit_cost(record: RFQQuoteRecord) -> float:
    return (
        record.unit_price
        + record.packaging_cost
        + record.customization_cost
        + _safe_divide(record.sample_fee, record.moq_tier)
        + _safe_divide(record.tooling_fee, record.moq_tier)
    )


def _select_tariff_row(
    tariff_tax: list[TariffTaxRecord],
    target_market: str,
) -> TariffTaxRecord | None:
    for row in tariff_tax:
        if row.market == target_market:
            return row
    return tariff_tax[0] if tariff_tax else None


def compute_supply_structure_metrics(suppliers: list[SupplierRecord]) -> dict:
    if not suppliers:
        return {}

    supplier_count = len(suppliers)
    supplier_type_counts = Counter(record.supplier_type for record in suppliers)
    region_counts = Counter(record.region for record in suppliers)
    factory_share = _safe_divide(
        sum(1 for record in suppliers if record.factory_flag),
        supplier_count,
    )
    oem_share = _safe_divide(sum(1 for record in suppliers if record.oem_flag), supplier_count)
    odm_share = _safe_divide(sum(1 for record in suppliers if record.odm_flag), supplier_count)
    average_capacity = mean(record.capacity_score for record in suppliers)
    average_compliance = mean(record.compliance_support_score for record in suppliers)
    maturity_score = (
        average_capacity * 0.35
        + average_compliance * 0.35
        + min(supplier_count / 6, 1) * 5 * 0.15
        + factory_share * 5 * 0.15
    ) / 5

    supplier_type_share = {
        supplier_type: round(_safe_divide(count, supplier_count), 4)
        for supplier_type, count in supplier_type_counts.most_common()
    }
    regional_share = {
        region: round(_safe_divide(count, supplier_count), 4)
        for region, count in region_counts.most_common()
    }

    return {
        "supplier_count": supplier_count,
        "supplier_type_share": supplier_type_share,
        "regional_share": regional_share,
        "factory_share": round(factory_share, 4),
        "oem_share": round(oem_share, 4),
        "odm_share": round(odm_share, 4),
        "average_moq": round(mean(record.moq for record in suppliers), 2),
        "median_sample_days": round(median(record.sample_days for record in suppliers), 2),
        "median_production_days": round(median(record.production_days for record in suppliers), 2),
        "average_capacity_score": round(average_capacity, 2),
        "average_compliance_support_score": round(average_compliance, 2),
        "supply_maturity_score": round(maturity_score, 4),
        "supply_maturity_level": _level_from_score(maturity_score),
    }


def compute_quote_strategy_metrics(
    quotes: list[RFQQuoteRecord],
    suppliers: list[SupplierRecord],
) -> dict:
    if not quotes:
        return {}

    supplier_lookup = {record.supplier_id: record for record in suppliers}
    incoterm_costs: dict[str, list[float]] = defaultdict(list)
    moq_costs: dict[int, list[float]] = defaultdict(list)
    supplier_type_costs: dict[str, list[float]] = defaultdict(list)
    quote_rows = []

    for record in quotes:
        quoted_cost = _quoted_unit_cost(record)
        incoterm_costs[record.incoterm].append(quoted_cost)
        moq_costs[record.moq_tier].append(quoted_cost)
        supplier = supplier_lookup.get(record.supplier_id)
        if supplier is not None:
            supplier_type_costs[supplier.supplier_type].append(quoted_cost)
        quote_rows.append(
            {
                "supplier_id": record.supplier_id,
                "supplier_name": supplier.supplier_name if supplier else record.supplier_id,
                "supplier_type": supplier.supplier_type if supplier else "unknown",
                "incoterm": record.incoterm,
                "moq_tier": record.moq_tier,
                "quoted_unit_cost": round(quoted_cost, 2),
            }
        )

    ordered_costs = sorted(row["quoted_unit_cost"] for row in quote_rows)
    low_cost = ordered_costs[0]
    high_cost = ordered_costs[-1]
    price_dispersion = _safe_divide(high_cost - low_cost, low_cost)
    supplier_type_median_cost = {
        supplier_type: round(median(values), 2)
        for supplier_type, values in supplier_type_costs.items()
    }
    factory_vs_trade_gap = None
    if supplier_type_median_cost.get("trader") and supplier_type_median_cost.get("factory"):
        factory_vs_trade_gap = round(
            _safe_divide(
                supplier_type_median_cost["trader"] - supplier_type_median_cost["factory"],
                supplier_type_median_cost["factory"],
            ),
            4,
        )

    moq_curve = [
        {
            "moq_tier": moq,
            "average_quoted_unit_cost": round(mean(values), 2),
        }
        for moq, values in sorted(moq_costs.items())
    ]

    quote_rows.sort(key=lambda row: row["quoted_unit_cost"])
    return {
        "incoterm_median_quoted_cost": {
            incoterm: round(median(values), 2)
            for incoterm, values in sorted(incoterm_costs.items())
        },
        "supplier_type_median_quoted_cost": supplier_type_median_cost,
        "factory_vs_trade_cost_gap": factory_vs_trade_gap,
        "price_dispersion_ratio": round(price_dispersion, 4),
        "best_quotes": quote_rows[:5],
        "moq_curve": moq_curve,
    }


def compute_compliance_metrics(
    requirements: list[ComplianceRequirementRecord],
    assumptions: Part3Assumptions,
) -> dict:
    filtered = [
        record for record in requirements if record.market == assumptions.target_market
    ]
    if not filtered:
        filtered = requirements
    if not filtered:
        return {}

    mandatory = [record for record in filtered if record.mandatory_flag]
    risk_distribution = Counter(record.risk_level for record in filtered)
    total_requirements = len(filtered)
    mandatory_cost = sum(record.estimated_cost for record in mandatory)
    mandatory_days = max((record.estimated_days for record in mandatory), default=0)
    high_risk_count = sum(1 for record in mandatory if record.risk_level == "high")

    return {
        "target_market": assumptions.target_market,
        "requirement_count": total_requirements,
        "mandatory_requirement_count": len(mandatory),
        "mandatory_estimated_cost": round(mandatory_cost, 2),
        "mandatory_estimated_days": mandatory_days,
        "mandatory_cost_per_unit": round(_safe_divide(mandatory_cost, assumptions.target_order_units), 2),
        "high_risk_mandatory_share": round(_safe_divide(high_risk_count, max(len(mandatory), 1)), 4),
        "risk_distribution": {
            level: round(_safe_divide(count, total_requirements), 4)
            for level, count in risk_distribution.items()
        },
        "gating_requirements": [
            {
                "requirement_name": record.requirement_name,
                "requirement_type": record.requirement_type,
                "estimated_cost": round(record.estimated_cost, 2),
                "estimated_days": record.estimated_days,
                "risk_level": record.risk_level,
            }
            for record in sorted(
                mandatory,
                key=lambda item: (item.risk_level != "high", -item.estimated_cost),
            )[:6]
        ],
    }


def compute_logistics_metrics(
    logistics_quotes: list[LogisticsQuoteRecord],
    shipment_events: list[ShipmentEventRecord],
) -> dict:
    if not logistics_quotes:
        return {}

    cost_values = [record.cost_value for record in logistics_quotes]
    lead_values = [record.lead_time_days for record in logistics_quotes]
    vol_values = [record.volatility_score for record in logistics_quotes]
    best_routes = []
    for record in logistics_quotes:
        route_score = (
            _normalized_score(record.cost_value, min(cost_values), max(cost_values)) * 0.45
            + _normalized_score(record.lead_time_days, min(lead_values), max(lead_values)) * 0.35
            + _normalized_score(record.volatility_score, min(vol_values), max(vol_values)) * 0.20
        )
        best_routes.append(
            {
                "route_id": record.route_id,
                "origin": record.origin,
                "destination": record.destination,
                "shipping_mode": record.shipping_mode,
                "incoterm": record.incoterm,
                "cost_value": round(record.cost_value, 2),
                "lead_time_days": record.lead_time_days,
                "volatility_score": round(record.volatility_score, 4),
                "route_score": round(route_score, 4),
            }
        )
    best_routes.sort(key=lambda row: row["route_score"], reverse=True)

    shipping_mode_mix = Counter(record.shipping_mode for record in logistics_quotes)
    mode_count = len(logistics_quotes)

    actual_lead_days = []
    customs_delay_count = 0
    on_time_count = 0
    for record in shipment_events:
        actual_lead_days.append(_days_between(record.etd, record.sellable_date))
        customs_days = _days_between(record.eta, record.customs_release_date)
        if customs_days > 2 or record.issue_type == "customs_delay":
            customs_delay_count += 1
        if record.delay_days <= 0:
            on_time_count += 1

    shipment_count = len(shipment_events)
    return {
        "route_count": len(logistics_quotes),
        "shipping_mode_mix": {
            mode: round(_safe_divide(count, mode_count), 4)
            for mode, count in shipping_mode_mix.items()
        },
        "best_routes": best_routes[:5],
        "average_actual_lead_time_days": round(mean(actual_lead_days), 2) if actual_lead_days else 0.0,
        "median_actual_lead_time_days": round(median(actual_lead_days), 2) if actual_lead_days else 0.0,
        "delay_rate": round(
            _safe_divide(sum(1 for record in shipment_events if record.delay_days > 0), shipment_count),
            4,
        ) if shipment_count else 0.0,
        "on_time_rate": round(_safe_divide(on_time_count, shipment_count), 4) if shipment_count else 0.0,
        "customs_delay_rate": round(_safe_divide(customs_delay_count, shipment_count), 4) if shipment_count else 0.0,
    }


def compute_landed_cost_metrics(
    quotes: list[RFQQuoteRecord],
    logistics_quotes: list[LogisticsQuoteRecord],
    requirements: list[ComplianceRequirementRecord],
    tariff_tax: list[TariffTaxRecord],
    assumptions: Part3Assumptions,
    suppliers: list[SupplierRecord],
) -> dict:
    if not quotes:
        return {}

    supplier_lookup = {record.supplier_id: record for record in suppliers}
    compliance_cost_per_unit = _safe_divide(
        sum(
            record.estimated_cost
            for record in requirements
            if record.market == assumptions.target_market and record.mandatory_flag
        ),
        assumptions.target_order_units,
    )
    tariff_row = _select_tariff_row(tariff_tax, assumptions.target_market)
    tariff_rate = (
        (tariff_row.base_duty_rate + tariff_row.additional_duty_rate)
        if tariff_row is not None
        else 0.0
    )
    ddp_risk_premium_rate = 0.08
    brokerage_fee = tariff_row.brokerage_fee if tariff_row is not None else 0.0
    port_fee = tariff_row.port_fee if tariff_row is not None else 0.0

    scenarios = []
    for quote in quotes:
        procurement_cost = _quoted_unit_cost(quote)
        if quote.incoterm == "DDP":
            logistics_candidates = [None]
        else:
            logistics_candidates = [
                record for record in logistics_quotes if record.incoterm == quote.incoterm
            ]
        if not logistics_candidates:
            continue

        for route in logistics_candidates:
            logistics_cost = 0.0 if route is None else route.cost_value
            duty_cost = 0.0 if quote.incoterm == "DDP" else procurement_cost * tariff_rate
            if quote.incoterm == "DDP":
                fees_cost = procurement_cost * ddp_risk_premium_rate
            else:
                fees_cost = brokerage_fee + port_fee
            landed_cost = procurement_cost + compliance_cost_per_unit + logistics_cost + duty_cost + fees_cost
            working_capital_cost = landed_cost * assumptions.working_capital_rate
            return_reserve = assumptions.return_rate * assumptions.return_cost_per_unit
            sellable_cost = landed_cost + working_capital_cost + return_reserve
            channel_fee = assumptions.target_sell_price * assumptions.channel_fee_rate
            marketing_fee = assumptions.target_sell_price * assumptions.marketing_fee_rate
            net_margin = assumptions.target_sell_price - channel_fee - marketing_fee - sellable_cost
            net_margin_rate = _safe_divide(net_margin, assumptions.target_sell_price)
            break_even_price = _safe_divide(
                sellable_cost,
                1 - assumptions.channel_fee_rate - assumptions.marketing_fee_rate,
            )
            supplier = supplier_lookup.get(quote.supplier_id)
            scenarios.append(
                {
                    "supplier_id": quote.supplier_id,
                    "supplier_name": supplier.supplier_name if supplier else quote.supplier_id,
                    "supplier_type": supplier.supplier_type if supplier else "unknown",
                    "incoterm": quote.incoterm,
                    "shipping_mode": route.shipping_mode if route is not None else "included_in_quote",
                    "route_id": route.route_id if route is not None else "included",
                    "moq_tier": quote.moq_tier,
                    "procurement_cost": round(procurement_cost, 2),
                    "compliance_cost": round(compliance_cost_per_unit, 2),
                    "logistics_cost": round(logistics_cost, 2),
                    "duty_cost": round(duty_cost, 2),
                    "fees_cost": round(fees_cost, 2),
                    "landed_cost": round(landed_cost, 2),
                    "working_capital_cost": round(working_capital_cost, 2),
                    "return_reserve": round(return_reserve, 2),
                    "sellable_cost": round(sellable_cost, 2),
                    "channel_fee": round(channel_fee, 2),
                    "marketing_fee": round(marketing_fee, 2),
                    "net_margin": round(net_margin, 2),
                    "net_margin_rate": round(net_margin_rate, 4),
                    "break_even_price": round(break_even_price, 2),
                }
            )

    scenarios.sort(key=lambda row: row["net_margin"], reverse=True)
    best_scenario = scenarios[0] if scenarios else {}
    margin_safety_score = best_scenario.get("net_margin_rate", 0.0)
    return {
        "target_sell_price": assumptions.target_sell_price,
        "target_order_units": assumptions.target_order_units,
        "tariff_total_rate": round(tariff_rate, 4),
        "scenarios_evaluated": len(scenarios),
        "best_scenario": best_scenario,
        "top_scenarios": scenarios[:5],
        "margin_safety_level": _level_from_score(max(margin_safety_score, 0.0)),
        "cost_breakdown": {
            "procurement_cost": best_scenario.get("procurement_cost", 0.0),
            "compliance_cost": best_scenario.get("compliance_cost", 0.0),
            "logistics_cost": best_scenario.get("logistics_cost", 0.0),
            "duty_cost": best_scenario.get("duty_cost", 0.0),
            "fees_cost": best_scenario.get("fees_cost", 0.0),
            "working_capital_cost": best_scenario.get("working_capital_cost", 0.0),
            "return_reserve": best_scenario.get("return_reserve", 0.0),
        },
        "break_even_price": best_scenario.get("break_even_price", 0.0),
    }


def compute_risk_matrix_metrics(
    suppliers: list[SupplierRecord],
    requirements: list[ComplianceRequirementRecord],
    logistics_quotes: list[LogisticsQuoteRecord],
    shipment_events: list[ShipmentEventRecord],
    landed_cost_metrics: dict,
    assumptions: Part3Assumptions,
) -> dict:
    if not suppliers:
        return {}

    supplier_risk = 1 - (
        (
            mean(record.capacity_score for record in suppliers)
            + mean(record.compliance_support_score for record in suppliers)
        )
        / 10
    )
    mandatory = [
        record for record in requirements
        if record.market == assumptions.target_market and record.mandatory_flag
    ] or [record for record in requirements if record.mandatory_flag]
    compliance_risk = min(
        1.0,
        _safe_divide(sum(1 for record in mandatory if record.risk_level == "high"), max(len(mandatory), 1))
        * 0.6
        + _safe_divide(max((record.estimated_days for record in mandatory), default=0), 90) * 0.4,
    )
    logistics_risk = min(
        1.0,
        (
            mean(record.volatility_score for record in logistics_quotes) * 0.5
            + _safe_divide(sum(1 for record in shipment_events if record.delay_days > 0), max(len(shipment_events), 1)) * 0.5
        ),
    ) if logistics_quotes else 0.0
    tariff_risk = min(1.0, landed_cost_metrics.get("tariff_total_rate", 0.0) * 4)
    margin_risk = min(
        1.0,
        max(0.0, 0.25 - landed_cost_metrics.get("best_scenario", {}).get("net_margin_rate", 0.0)) / 0.25,
    )

    risk_rows = [
        {
            "risk_name": "供应商执行风险",
            "severity_score": round(supplier_risk, 4),
            "risk_level": _risk_level(supplier_risk),
            "mitigation": "优先选择工厂直采并保留至少两家可替代供应商。",
        },
        {
            "risk_name": "合规与认证风险",
            "severity_score": round(compliance_risk, 4),
            "risk_level": _risk_level(compliance_risk),
            "mitigation": "先锁定必需认证路径，再决定首批试单节奏。",
        },
        {
            "risk_name": "物流交付风险",
            "severity_score": round(logistics_risk, 4),
            "risk_level": _risk_level(logistics_risk),
            "mitigation": "试单期保留安全库存并同步准备备选航线。",
        },
        {
            "risk_name": "关税政策风险",
            "severity_score": round(tariff_risk, 4),
            "risk_level": _risk_level(tariff_risk),
            "mitigation": "将税率变化纳入月度复核并保留 DDP 备选方案。",
        },
        {
            "risk_name": "利润安全边际风险",
            "severity_score": round(margin_risk, 4),
            "risk_level": _risk_level(margin_risk),
            "mitigation": "先以小批量验证实际转化和退货，再放大备货规模。",
        },
    ]
    risk_rows.sort(key=lambda row: row["severity_score"], reverse=True)
    overall_risk_score = mean(row["severity_score"] for row in risk_rows)

    return {
        "overall_risk_score": round(overall_risk_score, 4),
        "overall_risk_level": _risk_level(overall_risk_score),
        "priority_risks": risk_rows,
    }


def compute_entry_strategy_metrics(
    landed_cost_metrics: dict,
    risk_metrics: dict,
    supply_metrics: dict,
) -> dict:
    best_scenario = landed_cost_metrics.get("best_scenario", {})
    if not best_scenario:
        return {}

    margin_rate = best_scenario.get("net_margin_rate", 0.0)
    risk_score = risk_metrics.get("overall_risk_score", 1.0)
    supply_level = supply_metrics.get("supply_maturity_level", "low")

    if margin_rate >= 0.2 and risk_score <= 0.45 and supply_level == "high":
        recommendation = "recommended_entry"
    elif margin_rate > 0 and risk_score <= 0.7:
        recommendation = "pilot_first"
    else:
        recommendation = "hold"

    return {
        "recommendation": recommendation,
        "recommended_supplier": {
            "supplier_id": best_scenario.get("supplier_id"),
            "supplier_name": best_scenario.get("supplier_name"),
            "supplier_type": best_scenario.get("supplier_type"),
        },
        "recommended_path": {
            "incoterm": best_scenario.get("incoterm"),
            "shipping_mode": best_scenario.get("shipping_mode"),
            "route_id": best_scenario.get("route_id"),
            "moq_tier": best_scenario.get("moq_tier"),
        },
        "first_batch_units": best_scenario.get("moq_tier"),
        "target_break_even_price": best_scenario.get("break_even_price"),
        "next_90_day_actions": [
            "完成必需认证的时间表与预算锁定。",
            "与首选供应商完成样品确认和首批 MOQ 谈判。",
            "按推荐物流路径跑一票试单并记录完整 shipment events。",
        ],
    }
