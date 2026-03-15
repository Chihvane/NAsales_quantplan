from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from datetime import date
from statistics import mean, median

from .advanced_quant_tools import (
    bayesian_shrinkage_mean,
    entropy_growth_profile,
    fibonacci_retracement_levels,
    recursive_ewma,
)
from .models import EventLibraryRecord, Part1Dataset, TransactionRecord
from .stats_utils import clip, percentile, safe_divide, score_level


_DATE_FIELDS = (
    "date",
    "month",
    "event_date",
    "collected_at",
    "captured_at",
    "sold_at",
    "review_date",
    "updated_at",
    "signed_at",
)

_TABLE_STALENESS_TARGETS = {
    "search_trends": 45,
    "region_demand": 90,
    "customer_segments": 90,
    "listings": 60,
    "transactions": 30,
    "channels": 30,
    "market_size_inputs": 120,
    "channel_benchmarks": 90,
    "event_library": 365,
    "source_registry": 30,
    "part1_threshold_registry": 180,
    "market_destination_registry": 365,
    "consumer_habit_vectors": 180,
    "region_weight_profiles": 180,
}

_PROXY_SOURCE_TYPES = {
    "proxy",
    "estimate",
    "estimated",
    "third_party",
    "synthetic",
    "survey",
    "modeled",
}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        if len(cleaned) == 7:
            return date.fromisoformat(f"{cleaned}-01")
        return date.fromisoformat(cleaned[:10])
    except ValueError:
        return None


def _next_month(month_label: str) -> str:
    current = _parse_date(month_label)
    if current is None:
        return month_label
    year = current.year + (1 if current.month == 12 else 0)
    month = 1 if current.month == 12 else current.month + 1
    return f"{year:04d}-{month:02d}"


def _month_bucket(month_label: str) -> str:
    return month_label[5:7] if len(month_label) >= 7 else month_label


def _normalize_label(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _direction_sign(expected_direction: str) -> int:
    normalized = (expected_direction or "").strip().lower()
    if normalized in {"up", "positive", "increase", "supportive"}:
        return 1
    if normalized in {"down", "negative", "decrease", "drag"}:
        return -1
    return 0


def _habit_vector_distance(product_vector: dict[str, float], market_vector: dict[str, float]) -> float:
    shared_keys = sorted(set(product_vector) & set(market_vector))
    if not shared_keys:
        return 1.0
    squared_distance = mean(
        (float(product_vector[key]) - float(market_vector[key])) ** 2 for key in shared_keys
    )
    return clip(squared_distance ** 0.5, 0.0, 1.0)


def _parse_evidence_bundle(evidence_bundle: str) -> dict[str, object]:
    if not evidence_bundle:
        return {}
    try:
        parsed = json.loads(evidence_bundle)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _evidence_strength(evidence_bundle: str) -> float:
    evidence_map = _parse_evidence_bundle(evidence_bundle)
    if not evidence_map:
        return 1.0
    score_map = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4}
    scores = [score_map.get(str(value).upper(), 0.5) for value in evidence_map.values()]
    return mean(scores) if scores else 1.0


def _product_habit_fingerprint(section_metrics: dict[str, dict]) -> dict[str, float]:
    customer_metrics = section_metrics.get("1.2", {})
    channel_metrics = section_metrics.get("1.4", {})
    listed_price_metrics = section_metrics.get("1.5", {})
    transaction_metrics = section_metrics.get("1.6", {})
    brand_premium_map = listed_price_metrics.get("brand_premium", {})
    positive_brand_premium = mean([max(float(value), 0.0) for value in brand_premium_map.values()]) if brand_premium_map else 0.0
    return {
        "price_sensitivity": round(clip(transaction_metrics.get("discount_dependency_score", 0.0), 0.0, 1.0), 4),
        "brand_loyalty": round(clip(customer_metrics.get("customer_fit_score", 0.0) * 0.75, 0.0, 1.0), 4),
        "quality_premium_preference": round(clip(0.5 + positive_brand_premium, 0.0, 1.0), 4),
        "novelty_seeking": round(clip(channel_metrics.get("channel_risk_factor", 0.0) * 0.65, 0.0, 1.0), 4),
        "social_proof_dependency": round(clip(customer_metrics.get("persona_confidence_score", 0.0), 0.0, 1.0), 4),
        "discount_dependency": round(clip(transaction_metrics.get("discount_dependency_score", 0.0), 0.0, 1.0), 4),
        "delivery_speed_preference": round(clip(channel_metrics.get("channel_efficiency_factor", 0.0), 0.0, 1.0), 4),
        "return_aversion": round(clip(1 - transaction_metrics.get("discount_dependency_score", 0.0) * 0.4, 0.0, 1.0), 4),
        "cross_border_affinity": round(clip(channel_metrics.get("channel_dependency_score", 0.0) * 0.9, 0.0, 1.0), 4),
        "content_driven_discovery": round(clip(channel_metrics.get("channel_efficiency_factor", 0.0) * 0.75, 0.0, 1.0), 4),
        "payment_friction_tolerance": round(clip(transaction_metrics.get("price_realization_factor", 0.0), 0.0, 1.0), 4),
        "offline_affinity": round(clip(1 - channel_metrics.get("channel_dependency_score", 0.0), 0.0, 1.0), 4),
    }


def _rows_from_records(records: list[object]) -> list[dict]:
    rows = []
    for record in records:
        if is_dataclass(record):
            rows.append(asdict(record))
        elif isinstance(record, dict):
            rows.append(record)
    return rows


def _detect_date_values(table_name: str, rows: list[dict]) -> list[date]:
    parsed_dates: list[date] = []
    preferred_fields = [field_name for field_name in _DATE_FIELDS if any(field_name in row for row in rows)]
    for row in rows:
        for field_name in preferred_fields:
            parsed = _parse_date(str(row.get(field_name, "")))
            if parsed is not None:
                parsed_dates.append(parsed)
                break
    return parsed_dates


def _numeric_field_values(rows: list[dict]) -> dict[str, list[float]]:
    numeric_values: dict[str, list[float]] = {}
    for row in rows:
        for key, value in row.items():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                numeric_values.setdefault(key, []).append(float(value))
    return numeric_values


def _iqr_outlier_rate(values: list[float]) -> float:
    if len(values) < 4:
        return 0.0
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outlier_count = sum(1 for value in values if value < lower or value > upper)
    return safe_divide(outlier_count, len(values))


def build_part1_data_quality_log(
    dataset: Part1Dataset,
    *,
    as_of_date: date | None = None,
) -> dict:
    as_of_date = as_of_date or date.today()
    table_logs = []

    for field_def in fields(dataset):
        table_name = field_def.name
        records = getattr(dataset, table_name)
        rows = _rows_from_records(records)
        record_count = len(rows)
        total_cells = 0
        missing_cells = 0
        for row in rows:
            for value in row.values():
                total_cells += 1
                if value in (None, ""):
                    missing_cells += 1
        missingness_rate = safe_divide(missing_cells, total_cells, default=0.0)

        date_values = _detect_date_values(table_name, rows)
        freshness_days = round(
            mean(max((as_of_date - row_date).days, 0) for row_date in date_values),
            2,
        ) if date_values else None
        freshness_target = _TABLE_STALENESS_TARGETS.get(table_name, 90)
        freshness_score = (
            clip(1 - safe_divide(float(freshness_days), float(freshness_target or 1)), 0.0, 1.0)
            if freshness_days is not None
            else 0.5
        )

        numeric_fields = _numeric_field_values(rows)
        outlier_rates = [
            _iqr_outlier_rate(values)
            for values in numeric_fields.values()
            if len(values) >= 4
        ]
        outlier_rate_iqr = round(mean(outlier_rates), 4) if outlier_rates else 0.0

        proxy_dependency_ratio = 0.0
        if table_name == "source_registry" and records:
            flagged_proxy = 0
            for source in records:
                source_type = (source.source_type or "").strip().lower()
                if source_type in _PROXY_SOURCE_TYPES or (source.confidence_grade or "").upper() in {"C", "D"}:
                    flagged_proxy += 1
            proxy_dependency_ratio = round(safe_divide(flagged_proxy, len(records)), 4)

        health_score = round(
            clip(1 - missingness_rate, 0.0, 1.0) * 0.45
            + freshness_score * 0.25
            + clip(1 - outlier_rate_iqr, 0.0, 1.0) * 0.15
            + clip(1 - proxy_dependency_ratio, 0.0, 1.0) * 0.15,
            4,
        ) if record_count else 0.0

        table_logs.append(
            {
                "table_name": table_name,
                "record_count": record_count,
                "field_missingness_rate": round(missingness_rate, 4),
                "freshness_days": freshness_days,
                "freshness_target_days": freshness_target,
                "freshness_status": "fresh"
                if freshness_days is not None and freshness_days <= freshness_target
                else ("unknown" if freshness_days is None else "stale"),
                "outlier_rate_iqr": outlier_rate_iqr,
                "proxy_dependency_ratio": proxy_dependency_ratio,
                "health_score": health_score,
                "health_level": score_level(health_score),
            }
        )

    average_missingness_rate = round(mean([row["field_missingness_rate"] for row in table_logs]), 4) if table_logs else 0.0
    average_outlier_rate = round(mean([row["outlier_rate_iqr"] for row in table_logs]), 4) if table_logs else 0.0
    average_proxy_dependency = round(mean([row["proxy_dependency_ratio"] for row in table_logs]), 4) if table_logs else 0.0
    stale_table_count = sum(1 for row in table_logs if row["freshness_status"] == "stale")
    health_score = round(mean([row["health_score"] for row in table_logs]), 4) if table_logs else 0.0

    return {
        "table_logs": table_logs,
        "summary": {
            "table_count": len(table_logs),
            "average_missingness_rate": average_missingness_rate,
            "average_outlier_rate_iqr": average_outlier_rate,
            "proxy_dependency_ratio": average_proxy_dependency,
            "stale_table_count": stale_table_count,
            "health_score": health_score,
            "health_level": score_level(health_score),
        },
    }


def build_part1_evidence_trace_index(
    report: dict,
    section_metrics: dict[str, dict],
    factor_snapshots: dict[str, dict],
) -> dict:
    section_traces = []
    lineage_edges = []

    for section_id, section_payload in report.get("sections", {}).items():
        metrics = section_metrics.get(section_id, {})
        source_health = metrics.get("source_health", {})
        required_tables = section_payload.get("required_tables", [])
        for table_name in required_tables:
            lineage_edges.append(
                {
                    "from_node": table_name,
                    "to_node": section_id,
                    "edge_type": "table_to_section",
                }
            )
        trace_score = round(
            (
                (1.0 if section_payload.get("evidence_ref") else 0.0) * 0.35
                + source_health.get("coverage_ratio", 0.0) * 0.35
                + metrics.get("threshold_coverage_ratio", 0.0) * 0.15
                + (1.0 if section_payload.get("rule_ref") else 0.0) * 0.15
            ),
            4,
        )
        section_traces.append(
            {
                "section_id": section_id,
                "title": section_payload.get("title", ""),
                "required_tables": required_tables,
                "evidence_ref": section_payload.get("evidence_ref", []),
                "rule_ref": section_payload.get("rule_ref", []),
                "source_topics_expected": source_health.get("topics_expected", []),
                "source_topics_covered": source_health.get("topics_covered", []),
                "source_count": source_health.get("source_count", 0),
                "threshold_coverage_ratio": metrics.get("threshold_coverage_ratio", 0.0),
                "trace_score": trace_score,
                "trace_level": score_level(trace_score),
            }
        )

    factor_traces = []
    for factor_id, payload in sorted(factor_snapshots.items()):
        source_section = payload.get("source_section", "")
        section_payload = report.get("sections", {}).get(source_section, {})
        lineage_edges.append(
            {
                "from_node": source_section,
                "to_node": factor_id,
                "edge_type": "section_to_factor",
            }
        )
        factor_traces.append(
            {
                "factor_id": factor_id,
                "label": payload.get("label", ""),
                "source_section": source_section,
                "evidence_ref": section_payload.get("evidence_ref", []),
                "rule_ref": section_payload.get("rule_ref", []),
                "traceable": bool(source_section and section_payload),
            }
        )

    section_trace_coverage_ratio = round(
        safe_divide(
            sum(1 for row in section_traces if row["trace_score"] >= 0.5),
            len(section_traces),
        ),
        4,
    ) if section_traces else 0.0
    factor_trace_coverage_ratio = round(
        safe_divide(sum(1 for row in factor_traces if row["traceable"]), len(factor_traces)),
        4,
    ) if factor_traces else 0.0
    evidence_trace_coverage_ratio = round(
        mean([row["trace_score"] for row in section_traces]),
        4,
    ) if section_traces else 0.0

    return {
        "section_traces": section_traces,
        "factor_traces": factor_traces,
        "lineage_edges": lineage_edges,
        "summary": {
            "section_trace_coverage_ratio": section_trace_coverage_ratio,
            "factor_trace_coverage_ratio": factor_trace_coverage_ratio,
            "evidence_trace_coverage_ratio": evidence_trace_coverage_ratio,
            "traceability_score": round(
                section_trace_coverage_ratio * 0.6 + factor_trace_coverage_ratio * 0.4,
                4,
            ),
        },
    }


def _linear_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x_values = list(range(len(values)))
    x_mean = mean(x_values)
    y_mean = mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    return safe_divide(numerator, denominator, default=0.0)


def _event_adjustment_by_month(event_library: list[EventLibraryRecord]) -> dict[str, float]:
    month_effects: dict[str, list[float]] = {}
    for event in event_library:
        month_key = _month_bucket(event.event_date)
        month_effects.setdefault(month_key, []).append(_direction_sign(event.expected_direction) * event.severity)
    return {
        month_key: mean(values) * 5.0
        for month_key, values in month_effects.items()
        if values
    }


def _forecast_value(
    history_labels: list[str],
    history_values: list[float],
    target_label: str,
    event_adjustments: dict[str, float],
) -> float:
    if not history_values:
        return 0.0
    overall_mean = mean(history_values)
    recent_values = history_values[-6:] if len(history_values) >= 6 else history_values
    slope = _linear_slope(recent_values)
    baseline = history_values[-1] + slope
    seasonal_buckets: dict[str, list[float]] = {}
    for label, value in zip(history_labels, history_values):
        seasonal_buckets.setdefault(_month_bucket(label), []).append(value)
    seasonal_factor = safe_divide(
        mean(seasonal_buckets.get(_month_bucket(target_label), history_values)),
        overall_mean or 1.0,
        default=1.0,
    )
    seasonal_target = overall_mean * seasonal_factor
    event_adjustment = event_adjustments.get(_month_bucket(target_label), 0.0)
    return round(clip(baseline * 0.65 + seasonal_target * 0.35 + event_adjustment, 0.0, 100.0), 2)


def _monthly_units_map(transactions: list[TransactionRecord]) -> dict[str, int]:
    monthly_units: dict[str, int] = {}
    for record in transactions:
        month_label = record.date[:7] if len(record.date) >= 7 else record.date
        monthly_units[month_label] = monthly_units.get(month_label, 0) + max(record.units, 0)
    return monthly_units


def _lead_lag_profile(monthly_average: dict[str, float], transactions: list[TransactionRecord]) -> list[dict]:
    monthly_units = _monthly_units_map(transactions)
    ordered_labels = sorted(monthly_average)
    ordered_values = [monthly_average[label] for label in ordered_labels]
    lag_rows = []
    for lag_months in range(0, 4):
        paired_interest = []
        paired_units = []
        for index, label in enumerate(ordered_labels):
            if label not in monthly_units:
                continue
            trend_index = index - lag_months
            if trend_index < 0:
                continue
            paired_interest.append(ordered_values[trend_index])
            paired_units.append(monthly_units[label])
        if len(paired_interest) < 3:
            continue
        interest_mean = mean(paired_interest)
        units_mean = mean(paired_units)
        numerator = sum(
            (interest - interest_mean) * (units - units_mean)
            for interest, units in zip(paired_interest, paired_units)
        )
        interest_variance = sum((interest - interest_mean) ** 2 for interest in paired_interest)
        units_variance = sum((units - units_mean) ** 2 for units in paired_units)
        denominator = (interest_variance * units_variance) ** 0.5
        correlation = safe_divide(numerator, denominator, default=0.0)
        lag_rows.append(
            {
                "lag_months": lag_months,
                "correlation": round(correlation, 4),
                "observation_count": len(paired_interest),
            }
        )
    return lag_rows


def build_part1_forecast_engine(
    section_metrics: dict[str, dict],
    dataset: Part1Dataset,
) -> dict:
    demand_metrics = section_metrics.get("1.1", {})
    monthly_average = demand_metrics.get("trend", {}).get("monthly_average_interest", {})
    ordered_labels = sorted(monthly_average)
    history_values = [float(monthly_average[label]) for label in ordered_labels]
    if len(history_values) < 4:
        return {
            "model_id": "part1_forecast_engine_v1",
            "status": "insufficient_history",
            "backtest": {"observation_count": 0},
            "next_forecast": [],
        }

    event_adjustments = _event_adjustment_by_month(dataset.event_library)
    backtest_rows = []
    min_history = min(4, len(history_values) - 1)
    for index in range(min_history, len(ordered_labels)):
        history_labels = ordered_labels[:index]
        history = history_values[:index]
        target_label = ordered_labels[index]
        actual = history_values[index]
        forecast = _forecast_value(history_labels, history, target_label, event_adjustments)
        error = forecast - actual
        absolute_error = abs(error)
        backtest_rows.append(
            {
                "target_month": target_label,
                "forecast_interest": forecast,
                "actual_interest": round(actual, 2),
                "absolute_error": round(absolute_error, 2),
                "absolute_percentage_error": round(safe_divide(absolute_error, max(actual, 1.0)), 4),
                "event_window_flag": any(
                    _parse_date(event.event_date) and _parse_date(event.event_date).strftime("%Y-%m") == target_label
                    for event in dataset.event_library
                ),
            }
        )

    absolute_errors = [row["absolute_error"] for row in backtest_rows]
    percentage_errors = [row["absolute_percentage_error"] for row in backtest_rows]
    squared_errors = [(row["forecast_interest"] - row["actual_interest"]) ** 2 for row in backtest_rows]
    signed_errors = [row["forecast_interest"] - row["actual_interest"] for row in backtest_rows]

    lead_lag_rows = _lead_lag_profile(monthly_average, dataset.transactions)
    midpoint = max(len(ordered_labels) // 2, 3)
    first_half_profile = _lead_lag_profile(
        {label: monthly_average[label] for label in ordered_labels[:midpoint]},
        [record for record in dataset.transactions if record.date[:7] in set(ordered_labels[:midpoint])],
    )
    second_half_profile = _lead_lag_profile(
        {label: monthly_average[label] for label in ordered_labels[midpoint:]},
        [record for record in dataset.transactions if record.date[:7] in set(ordered_labels[midpoint:])],
    )
    first_best = max(first_half_profile, key=lambda item: item["correlation"], default={"lag_months": 0, "correlation": 0.0})
    second_best = max(second_half_profile, key=lambda item: item["correlation"], default={"lag_months": 0, "correlation": 0.0})
    lead_lag_stability_score = round(
        clip(
            1
            - (abs(first_best["lag_months"] - second_best["lag_months"]) / 3) * 0.4
            - abs(first_best["correlation"] - second_best["correlation"]) * 0.6,
            0.0,
            1.0,
        ),
        4,
    )

    event_rows = [row for row in backtest_rows if row["event_window_flag"]]
    non_event_rows = [row for row in backtest_rows if not row["event_window_flag"]]
    event_window_mae = round(mean([row["absolute_error"] for row in event_rows]), 2) if event_rows else 0.0
    non_event_window_mae = round(mean([row["absolute_error"] for row in non_event_rows]), 2) if non_event_rows else 0.0
    event_window_stability_score = round(
        clip(
            1 - safe_divide(abs(event_window_mae - non_event_window_mae), max(non_event_window_mae, 1.0)),
            0.0,
            1.0,
        ),
        4,
    ) if non_event_rows else 0.5

    next_forecast = []
    simulated_labels = list(ordered_labels)
    simulated_values = list(history_values)
    next_label = _next_month(ordered_labels[-1])
    for _ in range(3):
        predicted = _forecast_value(simulated_labels, simulated_values, next_label, event_adjustments)
        next_forecast.append({"month": next_label, "forecast_interest": predicted})
        simulated_labels.append(next_label)
        simulated_values.append(predicted)
        next_label = _next_month(next_label)

    rmse = (safe_divide(sum(squared_errors), len(squared_errors), default=0.0)) ** 0.5 if squared_errors else 0.0
    mae = mean(absolute_errors) if absolute_errors else 0.0
    backtest_score = round(
        clip(
            (1 - safe_divide(mae, 15.0)) * 0.45
            + (1 - safe_divide(mean(percentage_errors) if percentage_errors else 0.0, 0.25)) * 0.35
            + lead_lag_stability_score * 0.2,
            0.0,
            1.0,
        ),
        4,
    )

    return {
        "model_id": "part1_forecast_engine_v1",
        "status": "ready",
        "history_months": len(history_values),
        "backtest": {
            "observation_count": len(backtest_rows),
            "mae": round(mae, 2),
            "mape": round(mean(percentage_errors), 4) if percentage_errors else 0.0,
            "rmse": round(rmse, 2),
            "bias": round(mean(signed_errors), 2) if signed_errors else 0.0,
            "score": backtest_score,
        },
        "rolling_window_error": backtest_rows[-6:],
        "event_window_stability": {
            "event_month_count": len(event_rows),
            "event_window_mae": event_window_mae,
            "non_event_window_mae": non_event_window_mae,
            "stability_score": event_window_stability_score,
        },
        "lead_lag_stability": {
            "full_profile": lead_lag_rows,
            "first_half_best_lag": first_best,
            "second_half_best_lag": second_best,
            "stability_score": lead_lag_stability_score,
        },
        "next_forecast": next_forecast,
    }


def build_part1_drift_report(
    section_metrics: dict[str, dict],
    dataset: Part1Dataset,
    data_quality_log: dict,
) -> dict:
    demand_metrics = section_metrics.get("1.1", {})
    monthly_average = demand_metrics.get("trend", {}).get("monthly_average_interest", {})
    ordered_labels = sorted(monthly_average)
    early_labels = ordered_labels[: max(len(ordered_labels) // 2, 1)]
    late_labels = ordered_labels[max(len(ordered_labels) // 2, 1) :]
    early_values = [float(monthly_average[label]) for label in early_labels]
    late_values = [float(monthly_average[label]) for label in late_labels]

    demand_shift_ratio = round(
        safe_divide(abs(mean(late_values) - mean(early_values)), max(mean(early_values), 1.0)),
        4,
    ) if early_values and late_values else 0.0
    demand_volatility_shift_ratio = round(
        safe_divide(abs((max(late_values) - min(late_values)) - (max(early_values) - min(early_values))), max(max(early_values) - min(early_values), 1.0)),
        4,
    ) if len(early_values) >= 2 and len(late_values) >= 2 else 0.0

    early_tx = [record for record in dataset.transactions if record.date[:7] in set(early_labels)]
    late_tx = [record for record in dataset.transactions if record.date[:7] in set(late_labels)]
    early_actual_prices = [record.actual_price for record in early_tx]
    late_actual_prices = [record.actual_price for record in late_tx]
    price_shift_ratio = round(
        safe_divide(abs(median(late_actual_prices) - median(early_actual_prices)), max(median(early_actual_prices), 1.0)),
        4,
    ) if early_actual_prices and late_actual_prices else 0.0

    early_discounts = [
        safe_divide(record.list_price - record.actual_price, max(record.list_price, 1.0))
        for record in early_tx
        if record.list_price > 0
    ]
    late_discounts = [
        safe_divide(record.list_price - record.actual_price, max(record.list_price, 1.0))
        for record in late_tx
        if record.list_price > 0
    ]
    discount_shift_ratio = round(
        safe_divide(abs(mean(late_discounts) - mean(early_discounts)), max(mean(early_discounts), 0.01)),
        4,
    ) if early_discounts and late_discounts else 0.0

    early_platform_units: dict[str, int] = {}
    late_platform_units: dict[str, int] = {}
    for record in early_tx:
        early_platform_units[record.platform] = early_platform_units.get(record.platform, 0) + max(record.units, 0)
    for record in late_tx:
        late_platform_units[record.platform] = late_platform_units.get(record.platform, 0) + max(record.units, 0)
    platforms = sorted(set(early_platform_units) | set(late_platform_units))
    early_total_units = sum(early_platform_units.values())
    late_total_units = sum(late_platform_units.values())
    channel_mix_shift = round(
        sum(
            abs(
                safe_divide(early_platform_units.get(platform, 0), early_total_units)
                - safe_divide(late_platform_units.get(platform, 0), late_total_units)
            )
            for platform in platforms
        )
        / 2,
        4,
    ) if early_total_units and late_total_units else 0.0

    data_quality_summary = data_quality_log.get("summary", {})
    source_drift_report = {
        "proxy_dependency_ratio": data_quality_summary.get("proxy_dependency_ratio", 0.0),
        "stale_table_count": data_quality_summary.get("stale_table_count", 0),
        "source_drift_score": round(
            clip(
                (1 - data_quality_summary.get("proxy_dependency_ratio", 0.0)) * 0.5
                + (1 - safe_divide(data_quality_summary.get("stale_table_count", 0), max(data_quality_summary.get("table_count", 1), 1))) * 0.5,
                0.0,
                1.0,
            ),
            4,
        ),
    }
    factor_drift_checks = [
        demand_shift_ratio,
        demand_volatility_shift_ratio,
        price_shift_ratio,
        discount_shift_ratio,
        channel_mix_shift,
    ]
    factor_drift_report = {
        "demand_shift_ratio": demand_shift_ratio,
        "demand_volatility_shift_ratio": demand_volatility_shift_ratio,
        "price_shift_ratio": price_shift_ratio,
        "discount_shift_ratio": discount_shift_ratio,
        "channel_mix_shift": channel_mix_shift,
        "drift_risk_score": round(clip(mean(factor_drift_checks), 0.0, 1.0), 4),
    }
    benchmark_gaps = []
    for channel_row in section_metrics.get("1.4", {}).get("channels", []):
        for field_name in ("conversion_rate_gap", "average_order_value_gap", "roas_gap", "cac_gap"):
            gap_value = channel_row.get(field_name)
            if gap_value is not None:
                benchmark_gaps.append(abs(float(gap_value)))
    benchmark_drift_report = {
        "benchmark_gap_severity": round(mean(benchmark_gaps), 4) if benchmark_gaps else 0.0,
        "benchmark_coverage_ratio": section_metrics.get("1.4", {}).get("totals", {}).get("benchmark_coverage_ratio", 0.0),
    }

    stable_checks = [
        demand_shift_ratio <= 0.2,
        demand_volatility_shift_ratio <= 0.25,
        price_shift_ratio <= 0.15,
        discount_shift_ratio <= 0.2,
        channel_mix_shift <= 0.25,
    ]
    drift_score = round(
        clip(
            source_drift_report["source_drift_score"] * 0.25
            + (1 - factor_drift_report["drift_risk_score"]) * 0.5
            + (1 - benchmark_drift_report["benchmark_gap_severity"]) * 0.25,
            0.0,
            1.0,
        ),
        4,
    )

    return {
        "source_drift_report": source_drift_report,
        "factor_drift_report": factor_drift_report,
        "benchmark_drift_report": benchmark_drift_report,
        "summary": {
            "check_count": len(stable_checks),
            "stable_check_ratio": round(safe_divide(sum(1 for flag in stable_checks if flag), len(stable_checks)), 4),
            "drift_score": drift_score,
            "drift_level": score_level(drift_score),
        },
    }


def _flatten_numeric_metric_paths(payload: dict, prefix: str = "") -> dict[str, list[dict]]:
    metric_map: dict[str, list[dict]] = {}
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            nested = _flatten_numeric_metric_paths(value, path)
            for nested_key, nested_rows in nested.items():
                metric_map.setdefault(nested_key, []).extend(nested_rows)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            metric_map.setdefault(key, []).append({"path": path, "value": float(value)})
    return metric_map


def _factor_realized_outcomes(section_metrics: dict[str, dict]) -> dict[str, int]:
    demand = section_metrics.get("1.1", {})
    customer = section_metrics.get("1.2", {})
    market_inputs = section_metrics.get("1.3", {}).get("market_size_inputs", {})
    channels = section_metrics.get("1.4", {})
    transactions = section_metrics.get("1.6", {})
    return {
        "FAC-MARKET-ATTRACT": int(
            market_inputs.get("consistency_ratio", 0.0) >= 0.75
            and market_inputs.get("assumption_vs_reference_gap_ratio", 1.0) <= 0.15
        ),
        "FAC-DEMAND-STABILITY": int(
            demand.get("trend", {}).get("heat_volatility_coefficient", 1.0) <= 0.25
            and (demand.get("lag_analysis", {}).get("best_lag_correlation") or 0.0) >= 0.4
        ),
        "FAC-CUSTOMER-FIT": int(
            customer.get("persona_confidence_score", 0.0) >= 0.5
            and customer.get("persona_concentration_score", 0.0) >= 0.4
        ),
        "FAC-CHANNEL-EFFICIENCY": int(
            channels.get("totals", {}).get("overall_conversion_rate", 0.0) >= 0.08
            and channels.get("totals", {}).get("benchmark_coverage_ratio", 0.0) >= 0.5
        ),
        "FAC-CHANNEL-RISK": int(
            channels.get("channel_dependency_score", 1.0) <= 0.75
            and channels.get("channel_risk_factor", 0.0) >= 0.5
        ),
        "FAC-PRICE-REALIZATION": int(
            transactions.get("price_realization_rate", 0.0) >= 0.85
            and transactions.get("elasticity_reliability_score", 0.0) >= 0.4
        ),
    }


def build_part1_calibration_report(
    report: dict,
    section_metrics: dict[str, dict],
    factor_snapshots: dict[str, dict],
    dataset: Part1Dataset,
) -> dict:
    metric_paths = _flatten_numeric_metric_paths(section_metrics)
    threshold_rows = []
    aligned_thresholds = 0
    flip_candidates = []
    for threshold in dataset.part1_threshold_registry:
        matches = metric_paths.get(threshold.metric_name, [])
        aligned = bool(matches)
        if aligned:
            aligned_thresholds += 1
            for match in matches:
                threshold_base = max(abs(float(threshold.threshold_value)), 0.01)
                distance_ratio = abs(match["value"] - float(threshold.threshold_value)) / threshold_base
                if distance_ratio <= 0.1:
                    flip_candidates.append(
                        {
                            "metric_name": threshold.metric_name,
                            "metric_path": match["path"],
                            "observed_value": round(match["value"], 4),
                            "threshold_value": round(float(threshold.threshold_value), 4),
                            "distance_ratio": round(distance_ratio, 4),
                            "decision_if_fail": threshold.decision_if_fail,
                        }
                    )
        threshold_rows.append(
            {
                "gate_id": threshold.gate_id,
                "metric_name": threshold.metric_name,
                "aligned": aligned,
                "matched_paths": [match["path"] for match in matches],
            }
        )

    realized_outcomes = _factor_realized_outcomes(section_metrics)
    factor_rows = []
    for factor_id, payload in sorted(factor_snapshots.items()):
        predicted_score = float(payload.get("value", 0.0))
        realized_success = realized_outcomes.get(factor_id, 0)
        factor_rows.append(
            {
                "factor_id": factor_id,
                "predicted_score": round(predicted_score, 4),
                "realized_success": realized_success,
                "calibration_gap": round(predicted_score - realized_success, 4),
            }
        )

    bucket_map = {"low": [], "medium": [], "high": []}
    for row in factor_rows:
        score = row["predicted_score"]
        if score < 0.4:
            bucket_map["low"].append(row)
        elif score < 0.7:
            bucket_map["medium"].append(row)
        else:
            bucket_map["high"].append(row)
    probability_bucket_diagnostics = [
        {
            "bucket": bucket_name,
            "count": len(rows),
            "average_predicted_score": round(mean([row["predicted_score"] for row in rows]), 4) if rows else 0.0,
            "realized_success_rate": round(mean([row["realized_success"] for row in rows]), 4) if rows else 0.0,
        }
        for bucket_name, rows in bucket_map.items()
    ]

    gate_consistency_rows = []
    consistent_sections = 0
    sections_with_gates = 0
    for section_id, section_payload in report.get("sections", {}).items():
        gate_results = section_payload.get("metrics", {}).get("gate_results")
        if not isinstance(gate_results, dict) or not gate_results:
            continue
        sections_with_gates += 1
        expected_status = "pass" if all(gate_results.values()) else ("fail" if not any(gate_results.values()) else "review")
        actual_status = section_payload.get("gate_result", {}).get("status")
        consistent = expected_status == actual_status
        if consistent:
            consistent_sections += 1
        gate_consistency_rows.append(
            {
                "section_id": section_id,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "consistent": consistent,
            }
        )

    brier_score = round(
        mean([(row["predicted_score"] - row["realized_success"]) ** 2 for row in factor_rows]),
        4,
    ) if factor_rows else 0.0
    average_calibration_gap = round(
        mean([abs(row["calibration_gap"]) for row in factor_rows]),
        4,
    ) if factor_rows else 0.0
    threshold_alignment_ratio = round(
        safe_divide(aligned_thresholds, len(dataset.part1_threshold_registry)),
        4,
    ) if dataset.part1_threshold_registry else 0.0
    gate_consistency_ratio = round(
        safe_divide(consistent_sections, sections_with_gates),
        4,
    ) if sections_with_gates else 0.0
    naming_alignment_status = (
        "aligned"
        if threshold_alignment_ratio >= 0.9
        else ("partial" if threshold_alignment_ratio >= 0.6 else "misaligned")
    )

    return {
        "threshold_alignment": {
            "rows": threshold_rows,
            "threshold_alignment_ratio": threshold_alignment_ratio,
            "naming_alignment_status": naming_alignment_status,
        },
        "factor_outcome_pairs": factor_rows,
        "probability_bucket_diagnostics": probability_bucket_diagnostics,
        "gate_consistency": {
            "rows": gate_consistency_rows,
            "gate_consistency_ratio": gate_consistency_ratio,
        },
        "gate_flip_candidates": flip_candidates,
        "summary": {
            "brier_score": brier_score,
            "average_calibration_gap": average_calibration_gap,
            "threshold_alignment_ratio": threshold_alignment_ratio,
            "gate_consistency_ratio": gate_consistency_ratio,
            "flip_candidate_count": len(flip_candidates),
            "naming_alignment_status": naming_alignment_status,
        },
    }


def build_part1_advanced_quant_tools(
    section_metrics: dict[str, dict],
    dataset: Part1Dataset,
) -> dict:
    monthly_average = section_metrics.get("1.1", {}).get("trend", {}).get("monthly_average_interest", {})
    ordered_labels = sorted(monthly_average)
    history_values = [float(monthly_average[label]) for label in ordered_labels]
    if not history_values:
        return {
            "toolkit_id": "part1_advanced_quant_tools_v1",
            "status": "insufficient_history",
        }

    fourier_payload = section_metrics.get("1.1", {}).get("advanced_time_series", {})
    fibonacci_payload = fibonacci_retracement_levels(history_values)
    recursive_payload = recursive_ewma(history_values)
    entropy_payload = entropy_growth_profile(history_values)
    posterior_demand_signal = bayesian_shrinkage_mean(
        observed_mean=history_values[-1],
        prior_mean=mean(history_values),
        prior_strength=4.0,
        sample_size=min(len(history_values), 6),
    )
    return {
        "toolkit_id": "part1_advanced_quant_tools_v1",
        "status": "ready",
        "modules": [
            "fourier",
            "bayesian_shrinkage",
            "fibonacci_levels",
            "entropy_growth",
            "recursive_ewma",
        ],
        "fourier": fourier_payload,
        "bayesian_shrinkage": {
            "prior_mean": round(mean(history_values), 4),
            "observed_latest": round(history_values[-1], 4),
            "posterior_demand_signal": posterior_demand_signal,
        },
        "fibonacci": fibonacci_payload,
        "entropy_growth": entropy_payload,
        "recursive": recursive_payload,
        "summary": {
            "tool_count": 5,
            "posterior_demand_signal": posterior_demand_signal,
            "entropy_growth_score": entropy_payload.get("entropy_growth_score", 0.0),
            "recursive_stability_score": recursive_payload.get("stability_score", 0.0),
            "event_library_count": len(dataset.event_library),
        },
    }


def build_part1_market_destination_engine(
    dataset: Part1Dataset,
    section_metrics: dict[str, dict],
    factor_snapshots: dict[str, dict],
) -> dict:
    active_markets = [row for row in dataset.market_destination_registry if row.active_flag]
    if not active_markets:
        return {
            "engine_id": "part1_market_destination_engine_v1",
            "status": "missing_market_registry",
            "market_rows": [],
            "summary": {"market_count": 0},
        }

    product_vector = _product_habit_fingerprint(section_metrics)
    habit_map = {row.market_code: row for row in dataset.consumer_habit_vectors}
    weight_map = {row.market_code: row for row in dataset.region_weight_profiles if row.active_flag}
    prior_raw_scores: list[float] = []
    raw_rows: list[dict[str, object]] = []

    factor_values = {
        "market_attract": float(factor_snapshots.get("FAC-MARKET-ATTRACT", {}).get("value", 0.0)),
        "demand_stability": float(factor_snapshots.get("FAC-DEMAND-STABILITY", {}).get("value", 0.0)),
        "customer_fit": float(factor_snapshots.get("FAC-CUSTOMER-FIT", {}).get("value", 0.0)),
        "channel_efficiency": float(factor_snapshots.get("FAC-CHANNEL-EFFICIENCY", {}).get("value", 0.0)),
        "channel_risk": float(factor_snapshots.get("FAC-CHANNEL-RISK", {}).get("value", 0.0)),
        "price_realization": float(factor_snapshots.get("FAC-PRICE-REALIZATION", {}).get("value", 0.0)),
    }

    for market in active_markets:
        weight_profile = weight_map.get(market.market_code)
        habit_vector = habit_map.get(market.market_code)
        if weight_profile is None:
            continue
        localized_factor_score = (
            factor_values["market_attract"] * weight_profile.factor_weight_market_attract
            + factor_values["demand_stability"] * weight_profile.factor_weight_demand_stability
            + factor_values["customer_fit"] * weight_profile.factor_weight_customer_fit
            + factor_values["channel_efficiency"] * weight_profile.factor_weight_channel_efficiency
            + factor_values["channel_risk"] * weight_profile.factor_weight_channel_risk
            + factor_values["price_realization"] * weight_profile.factor_weight_price_realization
        )
        geo_fit_score = clip(
            market.digital_maturity * 0.35
            + market.cross_border_acceptance * 0.35
            + (1 - market.regulatory_complexity) * 0.15
            + (1 - market.logistics_complexity) * 0.15,
            0.0,
            1.0,
        )
        habit_fit_score = 0.5
        evidence_strength = 0.8
        if habit_vector is not None:
            market_vector = {
                "price_sensitivity": habit_vector.price_sensitivity,
                "brand_loyalty": habit_vector.brand_loyalty,
                "quality_premium_preference": habit_vector.quality_premium_preference,
                "novelty_seeking": habit_vector.novelty_seeking,
                "social_proof_dependency": habit_vector.social_proof_dependency,
                "discount_dependency": habit_vector.discount_dependency,
                "delivery_speed_preference": habit_vector.delivery_speed_preference,
                "return_aversion": habit_vector.return_aversion,
                "cross_border_affinity": habit_vector.cross_border_affinity,
                "content_driven_discovery": habit_vector.content_driven_discovery,
                "payment_friction_tolerance": habit_vector.payment_friction_tolerance,
                "offline_affinity": habit_vector.offline_affinity,
            }
            habit_fit_score = clip(1 - _habit_vector_distance(product_vector, market_vector), 0.0, 1.0)
            evidence_strength = _evidence_strength(habit_vector.evidence_bundle)
        raw_score = clip(
            localized_factor_score * 0.55
            + geo_fit_score * weight_profile.geo_fit_weight
            + habit_fit_score * weight_profile.habit_fit_weight
            - market.fx_risk * weight_profile.penalty_fx_risk
            - market.regulatory_complexity * weight_profile.penalty_compliance_risk
            - market.logistics_complexity * weight_profile.penalty_logistics_volatility,
            0.0,
            1.0,
        )
        prior_raw_scores.append(raw_score)
        raw_rows.append(
            {
                "market_code": market.market_code,
                "market_name": market.market_name,
                "region_group": market.region_group,
                "analysis_method": market.analysis_method,
                "habit_model_family": market.habit_model_family,
                "localized_factor_score": round(localized_factor_score, 4),
                "geo_fit_score": round(geo_fit_score, 4),
                "habit_fit_score": round(habit_fit_score, 4),
                "raw_score": round(raw_score, 4),
                "evidence_strength": round(evidence_strength, 4),
            }
        )

    prior_mean = mean(prior_raw_scores) if prior_raw_scores else 0.0
    market_rows = []
    for row in raw_rows:
        posterior_score = bayesian_shrinkage_mean(
            observed_mean=float(row["raw_score"]),
            prior_mean=prior_mean,
            prior_strength=3.0,
            sample_size=max(float(row["evidence_strength"]) * 4, 1.0),
        )
        market_rows.append(
            {
                **row,
                "posterior_score": posterior_score,
                "destination_fit_level": score_level(posterior_score),
            }
        )
    market_rows.sort(key=lambda row: float(row["posterior_score"]), reverse=True)
    method_count = len({row["analysis_method"] for row in market_rows if row["analysis_method"]})
    model_family_count = len({row["habit_model_family"] for row in market_rows if row["habit_model_family"]})
    return {
        "engine_id": "part1_market_destination_engine_v1",
        "status": "ready",
        "product_habit_fingerprint": product_vector,
        "market_rows": market_rows,
        "summary": {
            "market_count": len(market_rows),
            "habit_vector_coverage_ratio": round(safe_divide(len(habit_map), len(active_markets)), 4),
            "weight_profile_coverage_ratio": round(safe_divide(len(weight_map), len(active_markets)), 4),
            "analysis_method_diversity_count": method_count,
            "habit_model_family_diversity_count": model_family_count,
            "top_market_code": market_rows[0]["market_code"] if market_rows else "",
            "top_market_score": market_rows[0]["posterior_score"] if market_rows else 0.0,
        },
    }


def build_part1_continuous_outputs(
    dataset: Part1Dataset,
    report: dict,
    section_metrics: dict[str, dict],
    factor_snapshots: dict[str, dict],
) -> dict:
    generated_at = report.get("metadata", {}).get("generated_at", "")
    as_of_date = _parse_date(generated_at[:10]) or date.today()
    data_quality_log = build_part1_data_quality_log(dataset, as_of_date=as_of_date)
    evidence_trace_index = build_part1_evidence_trace_index(report, section_metrics, factor_snapshots)
    forecast_engine = build_part1_forecast_engine(section_metrics, dataset)
    drift_report = build_part1_drift_report(section_metrics, dataset, data_quality_log)
    calibration_report = build_part1_calibration_report(report, section_metrics, factor_snapshots, dataset)
    advanced_quant_tools = build_part1_advanced_quant_tools(section_metrics, dataset)
    market_destination_engine = build_part1_market_destination_engine(dataset, section_metrics, factor_snapshots)
    return {
        "part1_data_quality_log": data_quality_log,
        "part1_evidence_trace_index": evidence_trace_index,
        "part1_forecast_engine": forecast_engine,
        "part1_drift_report": drift_report,
        "part1_calibration_report": calibration_report,
        "part1_advanced_quant_tools": advanced_quant_tools,
        "part1_market_destination_engine": market_destination_engine,
    }
