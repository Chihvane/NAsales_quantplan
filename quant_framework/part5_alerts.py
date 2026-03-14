from __future__ import annotations

from collections import Counter
from datetime import date

from .models import Part5Assumptions, Part5Dataset


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _build_alert(
    alert_type: str,
    severity: str,
    channel: str,
    message: str,
    alert_family: str,
    runbook_action: str,
) -> dict:
    return {
        "alert_type": alert_type,
        "severity": severity,
        "channel": channel,
        "message": message,
        "alert_family": alert_family,
        "runbook_action": runbook_action,
    }


def generate_operating_alerts(
    dataset: Part5Dataset,
    channel_rows: list[dict],
    assumptions: Part5Assumptions,
) -> dict:
    alerts = []
    for row in channel_rows:
        if row.get("contribution_margin_rate", 0.0) < assumptions.min_contribution_margin_rate:
            alerts.append(_build_alert("margin_floor_breach", "high", row["channel"], "贡献毛利率低于最小保护阈值。", "guardrail", "freeze_scale_and_review_fee_stack"))
        if row.get("return_rate", 0.0) > assumptions.max_refund_rate:
            alerts.append(_build_alert("refund_spike", "high", row["channel"], "退货率高于预设阈值。", "guardrail", "audit_returns_and_pause_promo"))
        if row.get("dispute_rate", 0.0) > assumptions.max_dispute_rate:
            alerts.append(_build_alert("dispute_spike", "medium", row["channel"], "争议率高于预设阈值。", "guardrail", "review_claims_and_payment_risk"))
        if row.get("inventory_days", 0.0) > assumptions.target_inventory_days * 1.5:
            alerts.append(_build_alert("inventory_overhang", "medium", row["channel"], "库存覆盖天数过高，存在积压风险。", "inventory", "tighten_reorder_and_clear_old_stock"))
        if row.get("inventory_days", 0.0) and row.get("inventory_days", 0.0) < assumptions.target_inventory_days * 0.35:
            alerts.append(_build_alert("inventory_tight", "medium", row["channel"], "库存覆盖天数偏低，存在断货风险。", "inventory", "raise_reorder_priority"))
        burn_ratio = 0.0
        if row.get("revenue", 0.0):
            burn_ratio = row.get("acquisition_cost_total", 0.0) / row["revenue"]
        if burn_ratio > assumptions.max_budget_burn_ratio:
            alerts.append(_build_alert("budget_burn_high", "medium", row["channel"], "广告消耗占收入比过高。", "spend", "cap_budget_and_recheck_creative"))

    for record in dataset.policy_change_log:
        if record.impact_level.lower() in {"high", "critical"}:
            alerts.append(_build_alert("policy_change", "high", record.platform, record.change_summary or "平台政策发生高影响变化。", "policy", "route_to_policy_review_and_pause_risky_actions"))

    snapshots_by_channel: dict[str, list] = {}
    for record in sorted(dataset.kpi_daily_snapshots, key=lambda item: (_parse_date(item.date) or date.min, item.channel)):
        snapshots_by_channel.setdefault(record.channel, []).append(record)

    for channel, rows in snapshots_by_channel.items():
        if len(rows) < max(assumptions.min_change_signal_points, 2):
            continue
        latest = rows[-1]
        history = rows[:-1]
        if not history:
            continue
        avg_revenue = sum(row.revenue for row in history) / len(history)
        avg_profit = sum(row.contribution_profit for row in history) / len(history)
        avg_refunds = sum(row.refunds for row in history) / len(history)
        revenue_change = ((latest.revenue - avg_revenue) / avg_revenue) if avg_revenue else 0.0
        profit_change = ((latest.contribution_profit - avg_profit) / avg_profit) if avg_profit else 0.0
        refund_change = ((latest.refunds - avg_refunds) / avg_refunds) if avg_refunds else (1.0 if latest.refunds > 0 else 0.0)

        if avg_revenue > 0 and revenue_change <= -assumptions.change_signal_relative_threshold:
            alerts.append(
                _build_alert(
                    "revenue_change_point",
                    "high" if revenue_change <= -assumptions.change_signal_relative_threshold * 1.5 else "medium",
                    channel,
                    "最新收入显著低于历史均值，触发收入变点预警。",
                    "change_point",
                    "inspect_channel_funnel_and_pause_scale",
                )
            )
        if avg_profit > 0 and profit_change <= -assumptions.change_signal_relative_threshold:
            alerts.append(
                _build_alert(
                    "profit_change_point",
                    "high" if profit_change <= -assumptions.change_signal_relative_threshold * 1.5 else "medium",
                    channel,
                    "最新贡献利润显著低于历史均值，触发利润变点预警。",
                    "change_point",
                    "rebuild_unit_economics_and_review_price",
                )
            )
        if latest.refunds > 0 and refund_change >= assumptions.change_signal_relative_threshold:
            alerts.append(
                _build_alert(
                    "refund_change_point",
                    "medium",
                    channel,
                    "最新退款额显著高于历史均值，触发售后变点预警。",
                    "change_point",
                    "inspect_recent_orders_and_returns",
                )
            )

    type_counts = Counter(alert["alert_type"] for alert in alerts)
    severity_counts = Counter(alert["severity"] for alert in alerts)
    family_counts = Counter(alert["alert_family"] for alert in alerts)
    rollback_triggers = [
        alert for alert in alerts if alert["severity"] == "high"
    ]
    change_signal_alerts = [alert for alert in alerts if alert["alert_family"] == "change_point"]
    runbook_actions = dict(Counter(alert["runbook_action"] for alert in alerts))
    return {
        "alerts": alerts,
        "alert_count": len(alerts),
        "alert_type_mix": dict(type_counts),
        "severity_mix": dict(severity_counts),
        "alert_family_mix": dict(family_counts),
        "rollback_trigger_count": len(rollback_triggers),
        "change_signal_count": len(change_signal_alerts),
        "channels_with_change_signals": sorted({alert["channel"] for alert in change_signal_alerts}),
        "runbook_actions": runbook_actions,
    }
