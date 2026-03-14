from __future__ import annotations

from collections import defaultdict

from .models import Part5Dataset


def summarize_part5_data_contract(dataset: Part5Dataset) -> dict:
    has_returns_reason = any(record.return_reason for record in dataset.returns_claims)
    has_inventory_eta = any(record.eta for record in dataset.reorder_plan)
    has_policy_urls = any(record.source_url for record in dataset.policy_change_log)
    has_fee_versions = bool(dataset.channel_rate_cards)
    has_customer_identity = False
    has_new_customer_identity = False
    has_experiment_assignment = bool(dataset.experiment_assignments)
    has_experiment_metrics = bool(dataset.experiment_metrics)
    has_landed_cost = bool(dataset.landed_cost_scenarios)

    data_availability_flags = {
        "customer_identity_available": has_customer_identity,
        "new_customer_identification_available": has_new_customer_identity,
        "return_reason_available": has_returns_reason,
        "inventory_eta_available": has_inventory_eta,
        "policy_change_log_available": bool(dataset.policy_change_log),
        "policy_source_url_available": has_policy_urls,
        "fee_version_available": has_fee_versions,
        "experiment_assignment_available": has_experiment_assignment,
        "experiment_metric_available": has_experiment_metrics,
        "landed_cost_available": has_landed_cost,
    }

    proxy_usage_flags = []
    confidence_downgrade_reason = []
    model_blockers = []

    if not has_customer_identity:
        proxy_usage_flags.append("cohort_repeat_rate_proxy_for_ltv")
        confidence_downgrade_reason.append("缺少 customer_id，LTV 与生命周期模型降级为 cohort 粒度。")
        model_blockers.append("customer_level_ltv")
    if not has_new_customer_identity:
        proxy_usage_flags.append("platform_level_customer_acquisition_proxy")
        confidence_downgrade_reason.append("缺少新客识别字段，CAC 仅能按平台或会话口径近似。")
    if not has_experiment_assignment:
        proxy_usage_flags.append("registry_only_experiment_tracking")
        confidence_downgrade_reason.append("缺少实验分配表，增量结论只能依赖注册表与聚合结果。")
        model_blockers.append("strict_causal_attribution")
    if not has_experiment_metrics:
        confidence_downgrade_reason.append("缺少实验读数表，无法稳定输出 uplift 与显著性结果。")
        model_blockers.append("experiment_result_readout")
    if not has_inventory_eta:
        proxy_usage_flags.append("wide_interval_replenishment_assumption")
        confidence_downgrade_reason.append("补货 ETA 缺失，库存风险判断需使用更宽的区间。")
    if not has_policy_urls:
        confidence_downgrade_reason.append("政策变更缺少来源 URL，风险追溯能力受限。")
    if not has_landed_cost:
        confidence_downgrade_reason.append("缺少 landed cost 情景，利润与现金流模拟无法回接 Part 3。")
        model_blockers.append("risk_adjusted_profit_simulation")

    return {
        "data_availability_flags": data_availability_flags,
        "proxy_usage_flags": proxy_usage_flags,
        "confidence_downgrade_reason": confidence_downgrade_reason,
        "model_blockers": model_blockers,
    }


def build_part5_audit_pack(dataset: Part5Dataset) -> dict:
    latest_fee_versions: dict[str, dict] = {}
    fee_sources: dict[str, set[str]] = defaultdict(set)
    for record in dataset.channel_rate_cards:
        current = latest_fee_versions.get(record.channel)
        if current is None or record.effective_date >= current["effective_date"]:
            latest_fee_versions[record.channel] = {
                "channel": record.channel,
                "effective_date": record.effective_date,
                "fee_type": record.fee_type,
                "source_ref": record.source_ref,
            }
        if record.source_ref:
            fee_sources[record.channel].add(record.source_ref)

    latest_policy_changes: dict[str, dict] = {}
    for record in dataset.policy_change_log:
        current = latest_policy_changes.get(record.platform)
        if current is None or record.effective_date >= current["effective_date"]:
            latest_policy_changes[record.platform] = {
                "platform": record.platform,
                "policy_type": record.policy_type,
                "effective_date": record.effective_date,
                "source_url": record.source_url,
                "impact_level": record.impact_level,
            }

    experiment_channels = sorted({record.channel for record in dataset.experiment_registry if record.channel})
    return {
        "table_batches": {
            "kpi_daily_snapshots": len(dataset.kpi_daily_snapshots),
            "pricing_actions": len(dataset.pricing_actions),
            "reorder_plan": len(dataset.reorder_plan),
            "policy_change_log": len(dataset.policy_change_log),
            "cash_flow_snapshots": len(dataset.cash_flow_snapshots),
        },
        "fee_version_audit": {
            "latest_versions": list(latest_fee_versions.values()),
            "source_ref_coverage": {
                channel: sorted(source_refs)
                for channel, source_refs in fee_sources.items()
            },
        },
        "policy_change_audit": {
            "latest_changes": list(latest_policy_changes.values()),
            "source_url_count": sum(1 for record in dataset.policy_change_log if record.source_url),
        },
        "experiment_audit": {
            "experiment_count": len(dataset.experiment_registry),
            "assignment_count": len(dataset.experiment_assignments),
            "metric_row_count": len(dataset.experiment_metrics),
            "channels_covered": experiment_channels,
            "completed_count": sum(1 for record in dataset.experiment_registry if record.status.lower() == "completed"),
            "active_count": sum(1 for record in dataset.experiment_registry if record.status.lower() == "active"),
        },
        "data_contract": summarize_part5_data_contract(dataset),
    }
