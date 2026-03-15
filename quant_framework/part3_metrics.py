from __future__ import annotations

import json
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
from .stats_utils import (
    normalize_reverse_score,
    percentile as _percentile,
    safe_divide as _safe_divide,
    score_level,
)


RECOMMENDED_SUPPLIER_QUOTAS = {
    "factory": 5,
    "trader": 3,
    "wholesaler": 2,
}

PROCESS_MAP_STEPS = [
    {"step": 1, "name": "供应商定稿与样品确认", "owner": "采购/产品"},
    {"step": 2, "name": "合同与 Incoterm 锁定", "owner": "采购/法务"},
    {"step": 3, "name": "生产排期与原料备货", "owner": "工厂"},
    {"step": 4, "name": "过程质检与出厂放行", "owner": "工厂/质检"},
    {"step": 5, "name": "中国境内提货与出口报关", "owner": "货代/报关"},
    {"step": 6, "name": "国际运输与到港操作", "owner": "货代"},
    {"step": 7, "name": "进口清关与入仓上架", "owner": "清关/仓配"},
]

LOGISTICS_COST_SPLITS = {
    "EXW": {
        "china_inland_cost": 0.08,
        "export_fees": 0.03,
        "origin_handling_cost": 0.07,
        "international_freight_cost": 0.67,
        "insurance_cost": 0.02,
        "destination_handling_cost": 0.13,
    },
    "FOB": {
        "china_inland_cost": 0.0,
        "export_fees": 0.0,
        "origin_handling_cost": 0.0,
        "international_freight_cost": 0.79,
        "insurance_cost": 0.03,
        "destination_handling_cost": 0.18,
    },
    "CIF": {
        "china_inland_cost": 0.0,
        "export_fees": 0.0,
        "origin_handling_cost": 0.0,
        "international_freight_cost": 0.0,
        "insurance_cost": 0.0,
        "destination_handling_cost": 1.0,
    },
    "DDP": {
        "china_inland_cost": 0.0,
        "export_fees": 0.0,
        "origin_handling_cost": 0.0,
        "international_freight_cost": 0.0,
        "insurance_cost": 0.0,
        "destination_handling_cost": 0.0,
    },
}

def _normalized_score(value: float, min_value: float, max_value: float) -> float:
    return normalize_reverse_score(value, min_value, max_value)


def _level_from_score(score: float) -> str:
    return score_level(score, high_threshold=0.75, medium_threshold=0.55)


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _parse_date_or_none(value: str) -> date | None:
    if not value:
        return None
    try:
        return _parse_date(value)
    except ValueError:
        return None


def _days_between(start: str, end: str) -> int:
    return (_parse_date(end) - _parse_date(start)).days


def _days_between_safe(start: str, end: str) -> int | None:
    start_date = _parse_date_or_none(start)
    end_date = _parse_date_or_none(end)
    if start_date is None or end_date is None:
        return None
    return (end_date - start_date).days


def _distribution_summary(values: list[float | int]) -> dict[str, float]:
    if not values:
        return {}
    numeric = [float(value) for value in values]
    return {
        "mean": round(mean(numeric), 2),
        "median": round(median(numeric), 2),
        "p10": round(_percentile(numeric, 10), 2),
        "p90": round(_percentile(numeric, 90), 2),
    }


def _normalize_confidence(value: float) -> float:
    if value > 1:
        value /= 100
    return max(0.0, min(1.0, value))


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


def _anchor_date(values: list[str]) -> date | None:
    parsed = [_parse_date_or_none(value) for value in values if value]
    parsed = [value for value in parsed if value is not None]
    if not parsed:
        return None
    return max(parsed)


def _quote_reference_date(record: RFQQuoteRecord) -> str:
    return record.captured_at or record.quote_date


def _quote_freshness_score(record: RFQQuoteRecord, as_of_date: date | None) -> float:
    reference_date = _parse_date_or_none(_quote_reference_date(record))
    if reference_date is None or as_of_date is None:
        return 0.55
    age_days = max((as_of_date - reference_date).days, 0)
    if age_days <= 14:
        return 1.0
    if age_days <= 30:
        return 0.85
    if age_days <= 60:
        return 0.7
    if age_days <= 90:
        return 0.55
    return 0.35


def _route_freshness_score(record: LogisticsQuoteRecord, as_of_date: date | None) -> float:
    reference_date = _parse_date_or_none(record.quote_date)
    if reference_date is None or as_of_date is None:
        return 0.6
    age_days = max((as_of_date - reference_date).days, 0)
    if age_days <= 14:
        return 1.0
    if age_days <= 30:
        return 0.85
    if age_days <= 60:
        return 0.7
    if age_days <= 90:
        return 0.55
    return 0.4


def _quote_inclusion_score(record: RFQQuoteRecord) -> float:
    if record.included_items:
        return 1.0
    if any(value > 0 for value in (record.packaging_cost, record.customization_cost, record.sample_fee, record.tooling_fee)):
        return 0.8
    return 0.55


def _quote_validity_score(record: RFQQuoteRecord, as_of_date: date | None) -> float:
    if not record.quote_valid_until or as_of_date is None:
        return 0.75
    valid_until = _parse_date_or_none(record.quote_valid_until)
    if valid_until is None:
        return 0.55
    return 1.0 if valid_until >= as_of_date else 0.35


def _quote_confidence_score(record: RFQQuoteRecord, as_of_date: date | None) -> float:
    source_confidence = _normalize_confidence(record.source_confidence or 0.72)
    freshness = _quote_freshness_score(record, as_of_date)
    inclusion = _quote_inclusion_score(record)
    validity = _quote_validity_score(record, as_of_date)
    score = source_confidence * 0.4 + freshness * 0.25 + inclusion * 0.2 + validity * 0.15
    return round(score, 4)


def _parse_list_field(value: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_price_breaks(value: str) -> list[dict[str, float]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            rows = []
            for item in parsed:
                if isinstance(item, dict):
                    rows.append(
                        {
                            "moq": float(item.get("moq", 0) or 0),
                            "unit_price": float(item.get("unit_price", 0) or 0),
                        }
                    )
            return rows
    except json.JSONDecodeError:
        return []
    return []


def _split_logistics_cost(logistics_cost: float, incoterm: str) -> dict[str, float]:
    split = LOGISTICS_COST_SPLITS.get(incoterm, LOGISTICS_COST_SPLITS["FOB"])
    return {
        key: round(logistics_cost * share, 2)
        for key, share in split.items()
    }


def compute_supply_structure_metrics(suppliers: list[SupplierRecord]) -> dict:
    if not suppliers:
        return {}

    supplier_count = len(suppliers)
    supplier_type_counts = Counter(record.supplier_type for record in suppliers)
    region_counts = Counter(record.region for record in suppliers)
    supplier_type_share = {
        supplier_type: round(_safe_divide(count, supplier_count), 4)
        for supplier_type, count in supplier_type_counts.most_common()
    }
    regional_share = {
        region: round(_safe_divide(count, supplier_count), 4)
        for region, count in region_counts.most_common()
    }
    factory_share = _safe_divide(
        sum(1 for record in suppliers if record.factory_flag),
        supplier_count,
    )
    oem_share = _safe_divide(sum(1 for record in suppliers if record.oem_flag), supplier_count)
    odm_share = _safe_divide(sum(1 for record in suppliers if record.odm_flag), supplier_count)
    average_capacity = mean(record.capacity_score for record in suppliers)
    average_compliance = mean(record.compliance_support_score for record in suppliers)

    quota_rows = []
    attained_points = 0
    total_points = 0
    for supplier_type, target_count in RECOMMENDED_SUPPLIER_QUOTAS.items():
        actual_count = supplier_type_counts.get(supplier_type, 0)
        attained_points += min(actual_count, target_count)
        total_points += target_count
        attainment_ratio = _safe_divide(actual_count, target_count)
        quota_rows.append(
            {
                "supplier_type": supplier_type,
                "actual_count": actual_count,
                "recommended_minimum": target_count,
                "attainment_ratio": round(min(attainment_ratio, 1.0), 4),
                "status": "met" if actual_count >= target_count else "under_sampled",
            }
        )
    sample_quota_attainment = _safe_divide(attained_points, total_points)

    unique_regions = len(region_counts)
    unique_types = len(supplier_type_counts)
    top_region_share = max(regional_share.values()) if regional_share else 0.0
    top_type_share = max(supplier_type_share.values()) if supplier_type_share else 0.0
    representativeness_flags = []
    if sample_quota_attainment < 1.0:
        representativeness_flags.append("supplier_quota_not_fully_met")
    if top_region_share > 0.65:
        representativeness_flags.append("supplier_region_over_concentrated")
    if top_type_share > 0.8:
        representativeness_flags.append("supplier_type_over_concentrated")

    sample_confidence_score = min(
        1.0,
        sample_quota_attainment * 0.45
        + min(unique_regions / 3, 1.0) * 0.2
        + min(unique_types / 3, 1.0) * 0.15
        + (1 - top_region_share) * 0.1
        + factory_share * 0.1,
    )
    maturity_score = min(
        1.0,
        (average_capacity / 5) * 0.3
        + (average_compliance / 5) * 0.3
        + sample_confidence_score * 0.2
        + factory_share * 0.1
        + min(unique_regions / 4, 1.0) * 0.1,
    )

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
        "sample_adequacy": {
            "recommended_total": total_points,
            "actual_total": supplier_count,
            "quota_attainment_ratio": round(sample_quota_attainment, 4),
            "by_supplier_type": quota_rows,
        },
        "representativeness_flags": representativeness_flags,
        "sample_confidence_score": round(sample_confidence_score, 4),
        "sample_confidence_level": _level_from_score(sample_confidence_score),
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
    as_of_date = _anchor_date([_quote_reference_date(record) for record in quotes])
    incoterm_costs: dict[str, list[float]] = defaultdict(list)
    moq_costs: dict[int, list[float]] = defaultdict(list)
    moq_lead_times: dict[int, list[int]] = defaultdict(list)
    supplier_type_costs: dict[str, list[float]] = defaultdict(list)
    incoterm_supplier_matrix: dict[str, Counter[str]] = defaultdict(Counter)
    payment_terms_counter = Counter()
    certification_supplier_ids = set()
    quote_rows = []
    quote_confidences = []
    source_confidences = []
    fresh_quote_count = 0
    valid_quote_count = 0
    included_items_count = 0
    price_break_count = 0

    for record in quotes:
        quoted_cost = _quoted_unit_cost(record)
        confidence_score = _quote_confidence_score(record, as_of_date)
        source_confidence = _normalize_confidence(record.source_confidence or 0.72)
        incoterm_costs[record.incoterm].append(quoted_cost)
        moq_costs[record.moq_tier].append(quoted_cost)
        if record.lead_time_days:
            moq_lead_times[record.moq_tier].append(record.lead_time_days)
        supplier = supplier_lookup.get(record.supplier_id)
        supplier_type = supplier.supplier_type if supplier is not None else "unknown"
        supplier_type_costs[supplier_type].append(quoted_cost)
        incoterm_supplier_matrix[record.incoterm][supplier_type] += 1
        if record.payment_terms:
            payment_terms_counter[record.payment_terms] += 1
        if _parse_list_field(record.certifications_list):
            certification_supplier_ids.add(record.supplier_id)
        if _quote_freshness_score(record, as_of_date) >= 0.85:
            fresh_quote_count += 1
        if _quote_validity_score(record, as_of_date) >= 0.75:
            valid_quote_count += 1
        if _quote_inclusion_score(record) >= 0.8:
            included_items_count += 1
        if _parse_price_breaks(record.price_breaks_json):
            price_break_count += 1

        quote_rows.append(
            {
                "quote_id": record.quote_id or f"{record.supplier_id}-{record.incoterm}-{record.moq_tier}",
                "supplier_id": record.supplier_id,
                "supplier_name": supplier.supplier_name if supplier else record.supplier_id,
                "supplier_type": supplier_type,
                "incoterm": record.incoterm,
                "moq_tier": record.moq_tier,
                "quoted_unit_cost": round(quoted_cost, 2),
                "lead_time_days": record.lead_time_days,
                "payment_terms": record.payment_terms,
                "quote_confidence_score": confidence_score,
                "quote_confidence_level": _level_from_score(confidence_score),
            }
        )
        quote_confidences.append(confidence_score)
        source_confidences.append(source_confidence)

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

    moq_curve = []
    for moq, values in sorted(moq_costs.items()):
        lead_time_distribution = _distribution_summary(moq_lead_times.get(moq, []))
        moq_curve.append(
            {
                "moq_tier": moq,
                "average_quoted_unit_cost": round(mean(values), 2),
                "median_quoted_unit_cost": round(median(values), 2),
                "median_lead_time_days": lead_time_distribution.get("median", 0.0),
            }
        )

    quoted_supplier_count = len({record.supplier_id for record in quotes})
    supplier_pool_count = len({record.supplier_id for record in suppliers}) or quoted_supplier_count
    coverage_ratio = _safe_divide(quoted_supplier_count, supplier_pool_count)
    quote_rows.sort(key=lambda row: (row["quoted_unit_cost"], -row["quote_confidence_score"]))
    quote_bias_flags = []
    if coverage_ratio < 0.7:
        quote_bias_flags.append("supplier_quote_coverage_low")
    if _safe_divide(included_items_count, len(quotes)) < 0.8:
        quote_bias_flags.append("quote_scope_not_fully_disclosed")
    if _safe_divide(price_break_count, len(quotes)) < 0.6:
        quote_bias_flags.append("price_break_coverage_low")

    return {
        "incoterm_median_quoted_cost": {
            incoterm: round(median(values), 2)
            for incoterm, values in sorted(incoterm_costs.items())
        },
        "supplier_type_median_quoted_cost": supplier_type_median_cost,
        "factory_vs_trade_cost_gap": factory_vs_trade_gap,
        "price_dispersion_ratio": round(price_dispersion, 4),
        "sampled_supplier_coverage": {
            "quoted_supplier_count": quoted_supplier_count,
            "supplier_pool_count": supplier_pool_count,
            "coverage_ratio": round(coverage_ratio, 4),
        },
        "quote_quality": {
            "average_source_confidence": round(mean(source_confidences), 4),
            "average_quote_confidence": round(mean(quote_confidences), 4),
            "fresh_quote_share": round(_safe_divide(fresh_quote_count, len(quotes)), 4),
            "valid_quote_share": round(_safe_divide(valid_quote_count, len(quotes)), 4),
            "included_items_coverage": round(_safe_divide(included_items_count, len(quotes)), 4),
            "price_break_coverage": round(_safe_divide(price_break_count, len(quotes)), 4),
            "certification_supplier_coverage": round(
                _safe_divide(len(certification_supplier_ids), quoted_supplier_count),
                4,
            ),
        },
        "payment_terms_mix": {
            label: round(_safe_divide(count, sum(payment_terms_counter.values())), 4)
            for label, count in payment_terms_counter.items()
        },
        "supplier_incoterm_matrix": {
            incoterm: {
                supplier_type: count
                for supplier_type, count in counter.items()
            }
            for incoterm, counter in sorted(incoterm_supplier_matrix.items())
        },
        "quote_bias_flags": quote_bias_flags,
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
    requirement_type_mix = Counter(record.requirement_type for record in filtered)
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
        "requirement_type_mix": {
            requirement_type: round(_safe_divide(count, total_requirements), 4)
            for requirement_type, count in requirement_type_mix.items()
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
    quote_anchor = _anchor_date([record.quote_date for record in logistics_quotes])
    best_routes = []
    for record in logistics_quotes:
        route_score = (
            _normalized_score(record.cost_value, min(cost_values), max(cost_values)) * 0.4
            + _normalized_score(record.lead_time_days, min(lead_values), max(lead_values)) * 0.3
            + _normalized_score(record.volatility_score, min(vol_values), max(vol_values)) * 0.15
            + _route_freshness_score(record, quote_anchor) * 0.15
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

    linehaul_days = []
    customs_days = []
    inbound_days = []
    shelf_days = []
    actual_lead_days = []
    issue_counter = Counter()
    on_time_count = 0
    complete_event_count = 0
    shipping_mode_actual: dict[str, list[int]] = defaultdict(list)
    for record in shipment_events:
        stage_rows = [
            _days_between_safe(record.etd, record.eta),
            _days_between_safe(record.eta, record.customs_release_date),
            _days_between_safe(record.customs_release_date, record.warehouse_received_date),
            _days_between_safe(record.warehouse_received_date, record.sellable_date),
            _days_between_safe(record.etd, record.sellable_date),
        ]
        if all(value is not None for value in stage_rows):
            complete_event_count += 1
            linehaul_days.append(stage_rows[0])
            customs_days.append(stage_rows[1])
            inbound_days.append(stage_rows[2])
            shelf_days.append(stage_rows[3])
            actual_lead_days.append(stage_rows[4])
            shipping_mode_actual[record.shipping_mode].append(stage_rows[4])
        issue = record.delay_reason or record.issue_type or "none"
        issue_counter[issue] += 1
        if record.delay_days <= 0:
            on_time_count += 1

    shipment_count = len(shipment_events)
    delay_count = sum(1 for record in shipment_events if record.delay_days > 0)
    customs_delay_count = sum(
        1
        for record in shipment_events
        if (record.delay_reason or record.issue_type) == "customs_delay"
        or (_days_between_safe(record.eta, record.customs_release_date) or 0) > 2
    )

    return {
        "route_count": len(logistics_quotes),
        "shipping_mode_mix": {
            mode: round(_safe_divide(count, mode_count), 4)
            for mode, count in shipping_mode_mix.items()
        },
        "best_routes": best_routes[:5],
        "average_actual_lead_time_days": round(mean(actual_lead_days), 2) if actual_lead_days else 0.0,
        "median_actual_lead_time_days": round(median(actual_lead_days), 2) if actual_lead_days else 0.0,
        "delay_rate": round(_safe_divide(delay_count, shipment_count), 4) if shipment_count else 0.0,
        "on_time_rate": round(_safe_divide(on_time_count, shipment_count), 4) if shipment_count else 0.0,
        "customs_delay_rate": round(_safe_divide(customs_delay_count, shipment_count), 4) if shipment_count else 0.0,
        "event_coverage_score": round(_safe_divide(complete_event_count, shipment_count), 4) if shipment_count else 0.0,
        "stage_distribution": {
            "linehaul_days": _distribution_summary(linehaul_days),
            "customs_days": _distribution_summary(customs_days),
            "warehouse_inbound_days": _distribution_summary(inbound_days),
            "shelf_ready_days": _distribution_summary(shelf_days),
            "total_days": _distribution_summary(actual_lead_days),
        },
        "shipping_mode_actual_summary": {
            mode: _distribution_summary(values)
            for mode, values in shipping_mode_actual.items()
        },
        "issue_mix": {
            issue: round(_safe_divide(count, shipment_count), 4)
            for issue, count in issue_counter.items()
        },
        "process_map_steps": PROCESS_MAP_STEPS,
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
    quote_anchor = _anchor_date([_quote_reference_date(record) for record in quotes])
    route_anchor = _anchor_date([record.quote_date for record in logistics_quotes])
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
    ddp_risk_premium_rate = 0.03
    brokerage_fee = tariff_row.brokerage_fee if tariff_row is not None else 0.0
    port_fee = tariff_row.port_fee if tariff_row is not None else 0.0

    scenarios = []
    incoterm_summaries: dict[str, list[dict[str, float]]] = defaultdict(list)
    for quote in quotes:
        procurement_cost = _quoted_unit_cost(quote)
        quote_confidence = _quote_confidence_score(quote, quote_anchor)
        if quote.incoterm == "DDP":
            logistics_candidates: list[LogisticsQuoteRecord | None] = [None]
        else:
            logistics_candidates = [
                record for record in logistics_quotes if record.incoterm == quote.incoterm
            ]
        if not logistics_candidates:
            continue

        for route in logistics_candidates:
            logistics_cost = 0.0 if route is None else route.cost_value
            logistics_components = _split_logistics_cost(logistics_cost, quote.incoterm)
            duty_cost = 0.0 if quote.incoterm == "DDP" else procurement_cost * tariff_rate
            brokerage_cost = 0.0 if quote.incoterm == "DDP" else brokerage_fee
            port_cost = 0.0 if quote.incoterm == "DDP" else port_fee
            ddp_risk_premium = procurement_cost * ddp_risk_premium_rate if quote.incoterm == "DDP" else 0.0
            warehousing_cost = 0.0
            last_mile_cost = 0.0
            fees_cost = brokerage_cost + port_cost + ddp_risk_premium
            landed_cost = (
                procurement_cost
                + compliance_cost_per_unit
                + sum(logistics_components.values())
                + duty_cost
                + fees_cost
                + warehousing_cost
                + last_mile_cost
            )
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
            route_freshness = 0.75 if route is None else _route_freshness_score(route, route_anchor)
            route_volatility = 0.2 if route is None else route.volatility_score
            lead_time_days = (
                route.lead_time_days
                if route is not None and route.lead_time_days
                else quote.lead_time_days
            )
            scenario_confidence_score = min(
                1.0,
                quote_confidence * 0.55
                + route_freshness * 0.15
                + (1 - min(route_volatility, 1.0)) * 0.15
                + (1.0 if quote.incoterm != "DDP" else 0.8) * 0.15,
            )
            capital_required = landed_cost * min(quote.moq_tier or assumptions.target_order_units, assumptions.target_order_units)
            scenario_loss_proxy = min(
                1.0,
                max(0.0, assumptions.target_margin_floor - net_margin_rate)
                / max(assumptions.target_margin_floor, 0.01)
                + route_volatility * 0.35
                + max(0.0, 1 - scenario_confidence_score) * 0.2,
            )
            assumption_flags = []
            if warehousing_cost == 0:
                assumption_flags.append("warehousing_not_separately_sourced")
            if last_mile_cost == 0:
                assumption_flags.append("last_mile_not_separately_sourced")
            if quote.incoterm == "DDP":
                assumption_flags.append("ddp_transparency_risk")

            scenario = {
                "supplier_id": quote.supplier_id,
                "supplier_name": supplier.supplier_name if supplier else quote.supplier_id,
                "supplier_type": supplier.supplier_type if supplier else "unknown",
                "quote_id": quote.quote_id or f"{quote.supplier_id}-{quote.incoterm}-{quote.moq_tier}",
                "incoterm": quote.incoterm,
                "shipping_mode": route.shipping_mode if route is not None else "included_in_quote",
                "route_id": route.route_id if route is not None else "included",
                "moq_tier": quote.moq_tier,
                "lead_time_days": lead_time_days,
                "route_volatility_score": round(route_volatility, 4),
                "procurement_cost": round(procurement_cost, 2),
                "china_inland_cost": logistics_components["china_inland_cost"],
                "export_fees": logistics_components["export_fees"],
                "origin_handling_cost": logistics_components["origin_handling_cost"],
                "international_freight_cost": logistics_components["international_freight_cost"],
                "insurance_cost": logistics_components["insurance_cost"],
                "destination_handling_cost": logistics_components["destination_handling_cost"],
                "compliance_cost": round(compliance_cost_per_unit, 2),
                "logistics_cost": round(sum(logistics_components.values()), 2),
                "duty_cost": round(duty_cost, 2),
                "brokerage_cost": round(brokerage_cost, 2),
                "port_cost": round(port_cost, 2),
                "ddp_risk_premium": round(ddp_risk_premium, 2),
                "fees_cost": round(fees_cost, 2),
                "warehousing_cost": round(warehousing_cost, 2),
                "last_mile_cost": round(last_mile_cost, 2),
                "landed_cost": round(landed_cost, 2),
                "working_capital_cost": round(working_capital_cost, 2),
                "return_reserve": round(return_reserve, 2),
                "sellable_cost": round(sellable_cost, 2),
                "channel_fee": round(channel_fee, 2),
                "marketing_fee": round(marketing_fee, 2),
                "net_margin": round(net_margin, 2),
                "net_margin_rate": round(net_margin_rate, 4),
                "break_even_price": round(break_even_price, 2),
                "capital_required": round(capital_required, 2),
                "scenario_loss_proxy": round(scenario_loss_proxy, 4),
                "scenario_confidence_score": round(scenario_confidence_score, 4),
                "scenario_confidence_level": _level_from_score(scenario_confidence_score),
                "assumption_flags": assumption_flags,
            }
            scenarios.append(scenario)
            incoterm_summaries[quote.incoterm].append(
                {
                    "landed_cost": scenario["landed_cost"],
                    "net_margin": scenario["net_margin"],
                    "net_margin_rate": scenario["net_margin_rate"],
                    "scenario_confidence_score": scenario["scenario_confidence_score"],
                }
            )

    scenarios.sort(key=lambda row: (row["net_margin"], row["scenario_confidence_score"]), reverse=True)
    best_scenario = scenarios[0] if scenarios else {}
    margin_safety_score = best_scenario.get("net_margin_rate", 0.0)
    scenario_summary_by_incoterm = {}
    for incoterm, rows in incoterm_summaries.items():
        scenario_summary_by_incoterm[incoterm] = {
            "median_landed_cost": round(median(row["landed_cost"] for row in rows), 2),
            "median_net_margin": round(median(row["net_margin"] for row in rows), 2),
            "median_net_margin_rate": round(median(row["net_margin_rate"] for row in rows), 4),
            "average_confidence_score": round(mean(row["scenario_confidence_score"] for row in rows), 4),
        }

    return {
        "target_sell_price": assumptions.target_sell_price,
        "target_order_units": assumptions.target_order_units,
        "tariff_total_rate": round(tariff_rate, 4),
        "scenarios_evaluated": len(scenarios),
        "best_scenario": best_scenario,
        "top_scenarios": scenarios[:5],
        "scenario_table": scenarios,
        "scenario_summary_by_incoterm": scenario_summary_by_incoterm,
        "margin_safety_level": _level_from_score(max(margin_safety_score, 0.0)),
        "cost_breakdown": {
            "procurement_cost": best_scenario.get("procurement_cost", 0.0),
            "china_inland_cost": best_scenario.get("china_inland_cost", 0.0),
            "export_fees": best_scenario.get("export_fees", 0.0),
            "origin_handling_cost": best_scenario.get("origin_handling_cost", 0.0),
            "international_freight_cost": best_scenario.get("international_freight_cost", 0.0),
            "insurance_cost": best_scenario.get("insurance_cost", 0.0),
            "destination_handling_cost": best_scenario.get("destination_handling_cost", 0.0),
            "compliance_cost": best_scenario.get("compliance_cost", 0.0),
            "duty_cost": best_scenario.get("duty_cost", 0.0),
            "brokerage_cost": best_scenario.get("brokerage_cost", 0.0),
            "port_cost": best_scenario.get("port_cost", 0.0),
            "ddp_risk_premium": best_scenario.get("ddp_risk_premium", 0.0),
            "warehousing_cost": best_scenario.get("warehousing_cost", 0.0),
            "last_mile_cost": best_scenario.get("last_mile_cost", 0.0),
            "working_capital_cost": best_scenario.get("working_capital_cost", 0.0),
            "return_reserve": best_scenario.get("return_reserve", 0.0),
        },
        "break_even_price": best_scenario.get("break_even_price", 0.0),
        "assumption_gaps": best_scenario.get("assumption_flags", []),
    }


def compute_risk_matrix_metrics(
    suppliers: list[SupplierRecord],
    requirements: list[ComplianceRequirementRecord],
    logistics_quotes: list[LogisticsQuoteRecord],
    shipment_events: list[ShipmentEventRecord],
    landed_cost_metrics: dict,
    assumptions: Part3Assumptions,
    supply_metrics: dict | None = None,
) -> dict:
    if not suppliers:
        return {}

    supplier_base_risk = 1 - (
        (
            mean(record.capacity_score for record in suppliers)
            + mean(record.compliance_support_score for record in suppliers)
        )
        / 10
    )
    supplier_sample_penalty = 0.0
    if supply_metrics:
        supplier_sample_penalty = max(
            0.0,
            1 - supply_metrics.get("sample_confidence_score", 1.0),
        ) * 0.35
    supplier_risk = min(1.0, supplier_base_risk * 0.7 + supplier_sample_penalty)

    mandatory = [
        record for record in requirements
        if record.market == assumptions.target_market and record.mandatory_flag
    ] or [record for record in requirements if record.mandatory_flag]
    compliance_risk = min(
        1.0,
        _safe_divide(sum(1 for record in mandatory if record.risk_level == "high"), max(len(mandatory), 1)) * 0.6
        + _safe_divide(max((record.estimated_days for record in mandatory), default=0), 90) * 0.4,
    )
    logistics_risk = min(
        1.0,
        (
            mean(record.volatility_score for record in logistics_quotes) * 0.45
            + _safe_divide(sum(1 for record in shipment_events if record.delay_days > 0), max(len(shipment_events), 1)) * 0.35
            + max(0.0, 1 - landed_cost_metrics.get("best_scenario", {}).get("scenario_confidence_score", 1.0)) * 0.2
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
    optimizer_metrics: dict | None = None,
) -> dict:
    optimized_best = (optimizer_metrics or {}).get("best_feasible_scenario", {})
    best_scenario = optimized_best or landed_cost_metrics.get("best_scenario", {})
    if not best_scenario:
        return {}

    margin_rate = best_scenario.get("net_margin_rate", 0.0)
    risk_score = risk_metrics.get("overall_risk_score", 1.0)
    supply_level = supply_metrics.get("supply_maturity_level", "low")
    confidence_score = best_scenario.get("scenario_confidence_score", 0.0)
    recommendation_reason = "margin_risk_supply_joint_evaluation"

    if margin_rate >= 0.2 and risk_score <= 0.45 and supply_level == "high" and confidence_score >= 0.7:
        recommendation = "recommended_entry"
    elif margin_rate > 0 and risk_score <= 0.7:
        recommendation = "pilot_first"
    else:
        recommendation = "hold"

    if "ddp_transparency_risk" in best_scenario.get("assumption_flags", []):
        if recommendation == "recommended_entry":
            recommendation = "pilot_first"
        recommendation_reason = "ddp_path_requires_real_order_validation"
    elif optimizer_metrics and optimizer_metrics.get("optimizer_gate_result") == "fail":
        if recommendation == "recommended_entry":
            recommendation = "pilot_first"
        if not optimizer_metrics.get("best_feasible_scenario"):
            recommendation = "hold"
        recommendation_reason = "optimizer_constraints_not_satisfied"

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
        "recommendation_reason": recommendation_reason,
        "execution_confidence_score": best_scenario.get("scenario_confidence_score", 0.0),
        "execution_confidence_level": best_scenario.get("scenario_confidence_level", "low"),
        "optimizer_binding": {
            "optimizer_id": (optimizer_metrics or {}).get("optimizer_id", ""),
            "optimizer_gate_result": (optimizer_metrics or {}).get("optimizer_gate_result", ""),
            "feasible_scenarios_count": (optimizer_metrics or {}).get("feasible_scenarios_count", 0),
        },
        "next_90_day_actions": [
            "完成必需认证的时间表与预算锁定。",
            "与首选供应商完成样品确认和首批 MOQ 谈判。",
            "按推荐物流路径跑一票试单并记录完整 shipment events。",
        ],
    }
