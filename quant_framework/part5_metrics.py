from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from .models import Part4Assumptions, Part5Assumptions, Part5Dataset
from .part5_audit import summarize_part5_data_contract
from .part4_metrics import compute_channel_pnl_rows as _compute_part4_channel_pnl_rows
from .part5_experiments import summarize_experiment_readouts, summarize_experiment_registry
from .part5_forecasting import summarize_kpi_trend
from .part5_optimization import recommend_budget_allocation
from .stats_utils import mean_or_zero, safe_divide, score_level


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _week_bucket(value: str) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        return ""
    iso_year, iso_week, _ = parsed.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _days_since(reference_value: str, target_value: str) -> int | None:
    reference_date = _parse_date(reference_value)
    target_date = _parse_date(target_value)
    if reference_date is None or target_date is None:
        return None
    return (reference_date - target_date).days


def build_part5_channel_rows(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
) -> list[dict]:
    adapted = Part4Assumptions(
        target_payback_months=6.0,
        max_loss_probability=0.25,
        min_contribution_margin_rate=assumptions.min_contribution_margin_rate,
        target_repeat_rate=assumptions.target_repeat_rate,
        target_inventory_days=assumptions.target_inventory_days,
        risk_penalty_lambda=0.4,
        minimum_experiment_days=assumptions.min_experiment_weeks * 7,
    )
    return _compute_part4_channel_pnl_rows(dataset, adapted)


def compute_operating_goals_metrics(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
    channel_rows: list[dict],
    alert_payload: dict,
) -> dict:
    if not dataset.kpi_daily_snapshots:
        return {}

    status_counts = Counter(record.operating_status for record in dataset.kpi_daily_snapshots)
    channel_health_rows = []
    for row in channel_rows:
        profit_safety = min(row.get("contribution_margin_rate", 0.0) / max(assumptions.min_contribution_margin_rate, 0.01), 1.0)
        refund_safety = max(0.0, 1 - row.get("return_rate", 0.0) / max(assumptions.max_refund_rate, 0.01))
        dispute_safety = max(0.0, 1 - row.get("dispute_rate", 0.0) / max(assumptions.max_dispute_rate, 0.01))
        inventory_safety = max(0.0, 1 - abs(row.get("inventory_days", 0.0) - assumptions.target_inventory_days) / max(assumptions.target_inventory_days, 1))
        health_score = round(
            profit_safety * 0.4 + refund_safety * 0.25 + dispute_safety * 0.15 + inventory_safety * 0.2,
            4,
        )
        channel_health_rows.append(
            {
                "channel": row["channel"],
                "health_score": health_score,
                "health_level": score_level(health_score),
                "contribution_margin_rate": row.get("contribution_margin_rate", 0.0),
                "return_rate": row.get("return_rate", 0.0),
                "dispute_rate": row.get("dispute_rate", 0.0),
                "inventory_days": row.get("inventory_days", 0.0),
            }
        )
    operating_health_score = round(mean_or_zero([row["health_score"] for row in channel_health_rows]), 4)
    gate_results = {
        "health_gate": operating_health_score >= assumptions.target_health_score,
        "margin_gate": min((row.get("contribution_margin_rate", 0.0) for row in channel_rows), default=0.0) >= assumptions.min_contribution_margin_rate,
        "refund_gate": max((row.get("return_rate", 0.0) for row in channel_rows), default=0.0) <= assumptions.max_refund_rate,
        "dispute_gate": max((row.get("dispute_rate", 0.0) for row in channel_rows), default=0.0) <= assumptions.max_dispute_rate,
        "alert_gate": alert_payload.get("rollback_trigger_count", 0) == 0,
    }
    gate_breach_rate = safe_divide(sum(1 for value in gate_results.values() if not value), len(gate_results))
    return {
        "operating_health_score": operating_health_score,
        "operating_health_level": score_level(operating_health_score),
        "channel_health_rows": channel_health_rows,
        "gate_results": gate_results,
        "gate_breach_rate": round(gate_breach_rate, 4),
        "status_mix": {
            status: round(count / len(dataset.kpi_daily_snapshots), 4)
            for status, count in status_counts.items()
        },
        "primary_kpi_set": [
            "revenue",
            "contribution_profit",
            "return_rate",
            "inventory_days",
            "ad_spend",
        ],
        "guardrail_kpi_set": [
            "contribution_margin_rate",
            "refund_rate",
            "dispute_rate",
            "cash_lock",
        ],
    }


def compute_data_monitoring_metrics(
    dataset: Part5Dataset,
    channel_rows: list[dict],
    assumptions: Part5Assumptions,
) -> dict:
    active_channels = {row["channel"] for row in channel_rows}
    fee_channels = {record.channel for record in dataset.channel_rate_cards}
    policy_platforms = {record.platform for record in dataset.policy_change_log}
    data_contract = summarize_part5_data_contract(dataset)
    latest_snapshot_date = max((record.date for record in dataset.kpi_daily_snapshots), default="")
    record_counts = {
        "kpi_daily_snapshots": len(dataset.kpi_daily_snapshots),
        "marketing_spend": len(dataset.marketing_spend),
        "traffic_sessions": len(dataset.traffic_sessions),
        "inventory_positions": len(dataset.inventory_positions),
        "returns_claims": len(dataset.returns_claims),
        "policy_change_log": len(dataset.policy_change_log),
    }
    available_ratio = safe_divide(sum(1 for value in record_counts.values() if value > 0), len(record_counts))
    fee_version_coverage = safe_divide(len(active_channels & fee_channels), max(len(active_channels), 1))
    policy_monitoring_completeness = safe_divide(len(active_channels & policy_platforms), max(len(active_channels), 1))
    fee_source_ref_coverage = safe_divide(
        sum(1 for record in dataset.channel_rate_cards if record.source_ref),
        max(len(dataset.channel_rate_cards), 1),
    ) if dataset.channel_rate_cards else 0.0
    policy_source_url_coverage = safe_divide(
        sum(1 for record in dataset.policy_change_log if record.source_url),
        max(len(dataset.policy_change_log), 1),
    ) if dataset.policy_change_log else 0.0
    latest_fee_effective_date = max((record.effective_date for record in dataset.channel_rate_cards), default="")
    latest_policy_effective_date = max((record.effective_date for record in dataset.policy_change_log), default="")

    weekly_channel_rows: list[dict] = []
    weekly_buckets: dict[tuple[str, str], dict[str, float | str]] = {}
    for record in dataset.kpi_daily_snapshots:
        week = _week_bucket(record.date)
        if not week:
            continue
        key = (week, record.channel)
        bucket = weekly_buckets.setdefault(
            key,
            {
                "week": week,
                "channel": record.channel,
                "revenue": 0.0,
                "contribution_profit": 0.0,
                "ad_spend": 0.0,
                "refunds": 0.0,
                "days_observed": 0,
            },
        )
        bucket["revenue"] += record.revenue
        bucket["contribution_profit"] += record.contribution_profit
        bucket["ad_spend"] += record.ad_spend
        bucket["refunds"] += record.refunds
        bucket["days_observed"] += 1
    for bucket in sorted(weekly_buckets.values(), key=lambda item: (item["week"], item["channel"])):
        revenue = float(bucket["revenue"])
        weekly_channel_rows.append(
            {
                **bucket,
                "contribution_margin_rate": round(safe_divide(float(bucket["contribution_profit"]), revenue if revenue > 0 else 1.0), 4),
            }
        )

    weekly_contribution_profit = defaultdict(float)
    for row in weekly_channel_rows:
        weekly_contribution_profit[row["week"]] += float(row["contribution_profit"])

    fee_records_by_channel: dict[str, list] = defaultdict(list)
    for record in dataset.channel_rate_cards:
        fee_records_by_channel[record.channel].append(record)
    fee_version_binding_rows = []
    for channel in sorted(active_channels or fee_records_by_channel.keys()):
        records = fee_records_by_channel.get(channel, [])
        latest_effective = max((record.effective_date for record in records), default="")
        age_days = _days_since(latest_snapshot_date, latest_effective)
        stale_flag = age_days is None or age_days > assumptions.max_fee_version_age_days
        fee_version_binding_rows.append(
            {
                "channel": channel,
                "fee_type_count": len({record.fee_type for record in records}),
                "latest_effective_date": latest_effective,
                "fee_version_age_days": age_days,
                "source_ref_coverage": round(
                    safe_divide(sum(1 for record in records if record.source_ref), max(len(records), 1)),
                    4,
                ) if records else 0.0,
                "stale_flag": stale_flag,
            }
        )

    policy_rows_by_platform: dict[str, list] = defaultdict(list)
    for record in dataset.policy_change_log:
        policy_rows_by_platform[record.platform].append(record)
    policy_monitoring_rows = []
    for platform in sorted(active_channels | policy_platforms):
        records = policy_rows_by_platform.get(platform, [])
        latest_effective = max((record.effective_date for record in records), default="")
        age_days = _days_since(latest_snapshot_date, latest_effective)
        stale_flag = bool(platform in active_channels) and (age_days is None or age_days > assumptions.max_policy_age_days)
        policy_monitoring_rows.append(
            {
                "platform": platform,
                "policy_event_count": len(records),
                "latest_effective_date": latest_effective,
                "policy_age_days": age_days,
                "high_impact_count": sum(1 for record in records if record.impact_level.lower() in {"high", "critical"}),
                "stale_flag": stale_flag,
            }
        )

    stale_fee_version_ratio = safe_divide(
        sum(1 for row in fee_version_binding_rows if row["stale_flag"]),
        max(len(fee_version_binding_rows), 1),
    ) if fee_version_binding_rows else 0.0
    stale_policy_monitoring_ratio = safe_divide(
        sum(1 for row in policy_monitoring_rows if row["stale_flag"]),
        max(len(policy_monitoring_rows), 1),
    ) if policy_monitoring_rows else 0.0
    data_coverage_score = round(
        available_ratio * 0.45
        + fee_version_coverage * 0.2
        + policy_monitoring_completeness * 0.15
        + max(0.0, 1 - stale_fee_version_ratio) * 0.1
        + max(0.0, 1 - stale_policy_monitoring_ratio) * 0.1,
        4,
    )
    return {
        "record_counts": record_counts,
        "data_coverage_score": data_coverage_score,
        "data_coverage_level": score_level(data_coverage_score),
        "fee_version_coverage": round(fee_version_coverage, 4),
        "fee_source_ref_coverage": round(fee_source_ref_coverage, 4),
        "policy_monitoring_completeness": round(policy_monitoring_completeness, 4),
        "policy_source_url_coverage": round(policy_source_url_coverage, 4),
        "latest_fee_effective_date": latest_fee_effective_date,
        "latest_policy_effective_date": latest_policy_effective_date,
        "stale_fee_version_ratio": round(stale_fee_version_ratio, 4),
        "stale_policy_monitoring_ratio": round(stale_policy_monitoring_ratio, 4),
        "fee_version_binding_rows": fee_version_binding_rows,
        "policy_monitoring_rows": policy_monitoring_rows,
        "weekly_channel_pnl": weekly_channel_rows,
        "weekly_contribution_profit": {
            week: round(value, 2) for week, value in sorted(weekly_contribution_profit.items())
        },
        "refresh_latency_proxy_days": 1,
        "metric_consistency_score": round(min(1.0, available_ratio + 0.2), 4),
        "data_contract": data_contract,
    }


def compute_growth_loop_metrics(
    dataset: Part5Dataset,
    channel_rows: list[dict],
) -> dict:
    traffic_source_sessions: dict[str, int] = defaultdict(int)
    for record in dataset.traffic_sessions:
        traffic_source_sessions[record.traffic_source] += record.sessions
    total_sessions = sum(record.sessions for record in dataset.traffic_sessions)
    funnel = {
        "sessions": sum(record.sessions for record in dataset.traffic_sessions),
        "product_page_views": sum(record.product_page_views for record in dataset.traffic_sessions),
        "add_to_cart": sum(record.add_to_cart for record in dataset.traffic_sessions),
        "checkout_start": sum(record.checkout_start for record in dataset.traffic_sessions),
        "orders": sum(record.orders for record in dataset.traffic_sessions),
    }
    retention_curve = {
        record.channel: round(safe_divide(record.repeat_customers, record.customers), 4)
        for record in dataset.customer_cohorts
    }
    repeat_rate = safe_divide(
        sum(row.get("repeat_rate", 0.0) * row.get("orders", 0) for row in channel_rows),
        max(sum(row.get("orders", 0) for row in channel_rows), 1),
    )
    forecast_summary = summarize_kpi_trend(dataset.kpi_daily_snapshots)
    growth_leverage_score = round(
        min(safe_divide(funnel["orders"], max(funnel["sessions"], 1)) / 0.08, 1.0) * 0.4
        + min(repeat_rate / 0.18, 1.0) * 0.3
        + (1.0 if forecast_summary.get("trend_direction") != "down" else 0.2) * 0.3,
        4,
    )
    return {
        "traffic_mix": {
            source: round(safe_divide(session_count, total_sessions), 4)
            for source, session_count in traffic_source_sessions.items()
        },
        "funnel_conversion_matrix": {
            "page_view_rate": round(safe_divide(funnel["product_page_views"], max(funnel["sessions"], 1)), 4),
            "add_to_cart_rate": round(safe_divide(funnel["add_to_cart"], max(funnel["product_page_views"], 1)), 4),
            "checkout_rate": round(safe_divide(funnel["checkout_start"], max(funnel["add_to_cart"], 1)), 4),
            "order_rate": round(safe_divide(funnel["orders"], max(funnel["checkout_start"], 1)), 4),
        },
        "new_customer_efficiency": {
            "total_sessions": funnel["sessions"],
            "total_orders": funnel["orders"],
            "session_to_order_rate": round(safe_divide(funnel["orders"], max(funnel["sessions"], 1)), 4),
        },
        "repeat_rate": round(repeat_rate, 4),
        "retention_curve": retention_curve,
        "forecast_summary": forecast_summary,
        "growth_leverage_score": growth_leverage_score,
        "growth_leverage_level": score_level(growth_leverage_score),
    }


def compute_pricing_profit_metrics(
    dataset: Part5Dataset,
    channel_rows: list[dict],
) -> dict:
    if not dataset.pricing_actions:
        return {}
    promo_actions = [record for record in dataset.pricing_actions if record.promo_flag]
    bundle_actions = [record for record in dataset.pricing_actions if record.bundle_flag]
    price_change_rates = [
        safe_divide(record.new_price - record.old_price, max(record.old_price, 1))
        for record in dataset.pricing_actions
        if record.old_price
    ]
    negative_profit_days = sum(1 for record in dataset.kpi_daily_snapshots if record.contribution_profit < 0)
    promo_dependency_score = round(safe_divide(len(promo_actions), len(dataset.pricing_actions)), 4)
    latest_reference_price: dict[tuple[str, str], float] = {}
    for record in sorted(dataset.pricing_actions, key=lambda item: item.date):
        latest_reference_price[(record.channel, record.sku_id)] = record.new_price or record.old_price
    reference_revenue = 0.0
    realized_revenue = 0.0
    for record in dataset.sold_transactions:
        realized_revenue += record.transaction_price * record.units
        reference_price = latest_reference_price.get((record.platform, record.canonical_sku), record.transaction_price)
        reference_revenue += reference_price * record.units
    price_realization_rate = round(
        safe_divide(realized_revenue, reference_revenue if reference_revenue > 0 else 1.0),
        4,
    )
    margin_protection_score = round(
        max(0.0, 1 - promo_dependency_score) * 0.45
        + max(0.0, 1 - safe_divide(negative_profit_days, max(len(dataset.kpi_daily_snapshots), 1))) * 0.35
        + min(mean_or_zero([row.get("contribution_margin_rate", 0.0) for row in channel_rows]) / 0.12, 1.0) * 0.2,
        4,
    )
    return {
        "pricing_action_count": len(dataset.pricing_actions),
        "promo_action_share": promo_dependency_score,
        "bundle_action_share": round(safe_divide(len(bundle_actions), len(dataset.pricing_actions)), 4),
        "average_price_change_rate": round(mean_or_zero(price_change_rates), 4),
        "discount_depth_band": {
            "p10": round(min(price_change_rates), 4) if price_change_rates else 0.0,
            "p50": round(mean_or_zero(price_change_rates), 4),
            "p90": round(max(price_change_rates), 4) if price_change_rates else 0.0,
        },
        "promo_dependency_score": promo_dependency_score,
        "price_realization_rate": price_realization_rate,
        "margin_floor_breach_count": negative_profit_days,
        "margin_protection_score": margin_protection_score,
        "margin_protection_level": score_level(margin_protection_score),
    }


def compute_inventory_cash_metrics(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
    channel_rows: list[dict],
) -> dict:
    inventory_days = [row.get("inventory_days", 0.0) for row in channel_rows if row.get("inventory_days", 0.0) > 0]
    cash_lock_values = [record.inventory_cash_lock for record in dataset.cash_flow_snapshots]
    receivables = [record.receivable for record in dataset.cash_flow_snapshots]
    payables = [record.payable for record in dataset.cash_flow_snapshots]
    reorder_ready = sum(1 for record in dataset.reorder_plan if record.planned_units > 0 and record.target_cover_days >= assumptions.target_inventory_days * 0.5)
    reorder_readiness_score = round(safe_divide(reorder_ready, max(len(dataset.reorder_plan), 1)), 4)
    stockout_risk = round(
        safe_divide(sum(1 for days in inventory_days if days < assumptions.target_inventory_days * 0.35), max(len(inventory_days), 1)),
        4,
    ) if inventory_days else 0.0
    overstock_risk = round(
        safe_divide(sum(1 for days in inventory_days if days > assumptions.target_inventory_days * 1.5), max(len(inventory_days), 1)),
        4,
    ) if inventory_days else 0.0
    cash_lock_days = round(safe_divide(mean_or_zero(cash_lock_values), max(mean_or_zero(receivables), 1)), 4)
    return {
        "inventory_days": round(mean_or_zero(inventory_days), 2),
        "stockout_risk": stockout_risk,
        "overstock_risk": overstock_risk,
        "cash_lock_days": cash_lock_days,
        "receivable_mean": round(mean_or_zero(receivables), 2),
        "payable_mean": round(mean_or_zero(payables), 2),
        "reorder_readiness_score": reorder_readiness_score,
        "reorder_readiness_level": score_level(reorder_readiness_score),
    }


def compute_experiment_metrics(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
) -> dict:
    summary = summarize_experiment_registry(
        dataset.experiment_registry,
        dataset.traffic_sessions,
        min_weeks=assumptions.min_experiment_weeks,
    )
    if not summary:
        return {}
    readouts = summarize_experiment_readouts(
        dataset.experiment_registry,
        dataset.experiment_assignments,
        dataset.experiment_metrics,
        min_runtime_days=assumptions.min_experiment_weeks * 7,
        stop_thresholds={
            "ship_threshold": assumptions.experiment_ship_threshold,
            "loss_threshold": assumptions.experiment_loss_threshold,
            "futility_lower": assumptions.experiment_futility_lower,
            "futility_upper": assumptions.experiment_futility_upper,
            "effect_floor_share_of_mde": assumptions.experiment_effect_floor_share_of_mde,
        },
    )
    causal_confidence_score = round(
        summary.get("coverage_ratio", 0.0) * 0.35
        + summary.get("minimum_duration_pass_rate", 0.0) * 0.25
        + min(summary.get("test_velocity_per_30d", 0.0) / 3, 1.0) * 0.15
        + (1.0 if summary.get("sample_size_guidance", {}).get("sample_size_per_variant", 0) > 0 else 0.0) * 0.15
        + min(readouts.get("readout_coverage_ratio", 0.0) / 0.8, 1.0) * 0.05
        + min(readouts.get("average_hierarchical_win_probability", 0.0) / 0.8, 1.0) * 0.03
        + readouts.get("temporal_consistency_score", 0.0) * 0.02,
        4,
    )
    summary["platform_hard_constraints"] = {
        "minimum_runtime_days": assumptions.min_experiment_weeks * 7,
        "minimum_runtime_pass_rate": summary.get("minimum_duration_pass_rate", 0.0),
        "audience_threshold_status": "unavailable_without_assignment_or_platform_audience_table",
        "auto_stop_rules_enabled": True,
        "preferred_method_order": [
            "platform_ab_or_lift",
            "holdout_or_split_test",
            "did_or_ipw_if_randomization_unavailable",
        ],
    }
    summary["readouts"] = readouts
    summary["auto_stop_policy"] = {
        "ship_threshold": assumptions.experiment_ship_threshold,
        "loss_threshold": assumptions.experiment_loss_threshold,
        "futility_lower": assumptions.experiment_futility_lower,
        "futility_upper": assumptions.experiment_futility_upper,
        "effect_floor_share_of_mde": assumptions.experiment_effect_floor_share_of_mde,
    }
    summary["incrementality_score"] = round(
        readouts.get("readout_coverage_ratio", 0.0) * 0.25
        + readouts.get("winning_experiment_share", 0.0) * 0.2
        + readouts.get("assignment_coverage_ratio", 0.0) * 0.2
        + readouts.get("average_hierarchical_win_probability", 0.0) * 0.2
        + readouts.get("temporal_consistency_score", 0.0) * 0.15,
        4,
    )
    summary["causal_confidence_score"] = causal_confidence_score
    summary["causal_confidence_level"] = score_level(causal_confidence_score)
    return summary


def compute_risk_scale_metrics(
    dataset: Part5Dataset,
    assumptions: Part5Assumptions,
    channel_rows: list[dict],
    alert_payload: dict,
    operating_metrics: dict,
    inventory_metrics: dict,
    experiment_metrics: dict,
) -> dict:
    budget_payload = recommend_budget_allocation(channel_rows, assumptions)
    alert_count = alert_payload.get("alert_count", 0)
    rollback_trigger_count = alert_payload.get("rollback_trigger_count", 0)
    alert_penalty = min(alert_count / 10, 1.0)
    scale_readiness_score = round(
        operating_metrics.get("operating_health_score", 0.0) * 0.35
        + max(0.0, 1 - alert_penalty) * 0.2
        + experiment_metrics.get("causal_confidence_score", 0.0) * 0.2
        + inventory_metrics.get("reorder_readiness_score", 0.0) * 0.15
        + max(0.0, 1 - inventory_metrics.get("stockout_risk", 0.0) - inventory_metrics.get("overstock_risk", 0.0)) * 0.1,
        4,
    )
    if rollback_trigger_count > 0:
        expansion_gate_status = "rollback"
    elif scale_readiness_score >= 0.72:
        expansion_gate_status = "scale_up"
    elif scale_readiness_score >= 0.5:
        expansion_gate_status = "hold_and_optimize"
    else:
        expansion_gate_status = "pilot_only"
    return {
        "risk_alert_count": alert_count,
        "rollback_trigger_rate": round(safe_divide(rollback_trigger_count, max(alert_count, 1)), 4),
        "scale_readiness_score": scale_readiness_score,
        "scale_readiness_level": score_level(scale_readiness_score),
        "expansion_gate_status": expansion_gate_status,
        "budget_allocation": budget_payload.get("allocation", {}),
        "budget_allocation_method": budget_payload.get("method", ""),
        "policy_high_impact_count": sum(1 for record in dataset.policy_change_log if record.impact_level.lower() in {"high", "critical"}),
        "change_signal_count": alert_payload.get("change_signal_count", 0),
        "channels_with_change_signals": alert_payload.get("channels_with_change_signals", []),
        "runbook_actions": alert_payload.get("runbook_actions", {}),
    }
