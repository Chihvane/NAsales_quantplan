from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from .models import Part0Assumptions, Part0Dataset
from .stats_utils import mean_or_zero, safe_divide, score_level


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _days_since(value: str) -> int | None:
    parsed = _parse_date(value)
    if parsed is None:
        return None
    return max((date.today() - parsed).days, 0)


def _strategic_metric_family(metric_name: str, gate_name: str) -> str | None:
    normalized = f"{metric_name} {gate_name}".lower()
    if any(token in normalized for token in ("heat", "trend", "volatility", "season", "lag", "demand")):
        return "demand_stability"
    if any(token in normalized for token in ("roic", "roi", "irr", "margin", "profit")):
        return "capital_return"
    if any(token in normalized for token in ("tam", "sam", "som", "hhi", "cagr", "market")):
        return "market_structure"
    if any(token in normalized for token in ("payback", "recovery", "cash_cycle")):
        return "payback_control"
    if any(token in normalized for token in ("risk", "tariff", "compliance", "supplier", "defect", "fx")):
        return "risk_control"
    return None


def compute_decision_tree_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.decision_nodes:
        return {}

    child_counts: dict[str, int] = defaultdict(int)
    domains = set()
    gate_ids = set()
    owner_count = 0
    linked_paths = 0
    for record in dataset.decision_nodes:
        if record.parent_id:
            child_counts[record.parent_id] += 1
        if record.domain:
            domains.add(record.domain)
        if record.gate_id:
            gate_ids.add(record.gate_id)
        if record.owner_role:
            owner_count += 1
        if record.go_path or record.hold_path or record.kill_path:
            linked_paths += 1

    leaf_count = sum(1 for record in dataset.decision_nodes if child_counts.get(record.node_id, 0) == 0)
    gate_coverage_ratio = min(safe_divide(len(gate_ids), assumptions.required_gate_count), 1.0)
    domain_coverage_ratio = min(safe_divide(len(domains), assumptions.required_decision_domains), 1.0)
    owner_coverage_ratio = safe_divide(owner_count, len(dataset.decision_nodes))
    path_coverage_ratio = safe_divide(linked_paths, len(dataset.decision_nodes))
    decision_tree_score = round(
        gate_coverage_ratio * 0.35
        + domain_coverage_ratio * 0.25
        + owner_coverage_ratio * 0.2
        + path_coverage_ratio * 0.2,
        4,
    )
    return {
        "decision_node_count": len(dataset.decision_nodes),
        "gate_count": len(gate_ids),
        "leaf_count": leaf_count,
        "gate_coverage_ratio": round(gate_coverage_ratio, 4),
        "domain_coverage_ratio": round(domain_coverage_ratio, 4),
        "owner_coverage_ratio": round(owner_coverage_ratio, 4),
        "path_coverage_ratio": round(path_coverage_ratio, 4),
        "domain_mix": dict(sorted(Counter(record.domain for record in dataset.decision_nodes if record.domain).items())),
        "decision_tree_score": decision_tree_score,
        "decision_tree_level": score_level(decision_tree_score),
    }


def compute_data_confidence_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.evidence_sources:
        return {}

    confidence_counts = Counter((record.confidence_grade or "unknown").upper() for record in dataset.evidence_sources)
    ages = [_days_since(record.collected_at) for record in dataset.evidence_sources]
    fresh_count = 0
    version_count = 0
    status_count = 0
    owner_count = 0
    for record in dataset.evidence_sources:
        if record.version:
            version_count += 1
        if record.status:
            status_count += 1
        if record.owner_role:
            owner_count += 1
        age_days = _days_since(record.collected_at)
        freshness_limit = min(record.freshness_days or assumptions.max_source_age_days, assumptions.max_source_age_days)
        if age_days is not None and age_days <= freshness_limit:
            fresh_count += 1
    confidence_mix = {
        key: round(safe_divide(value, len(dataset.evidence_sources)), 4)
        for key, value in sorted(confidence_counts.items())
    }
    version_coverage_ratio = safe_divide(version_count, len(dataset.evidence_sources))
    status_coverage_ratio = safe_divide(status_count, len(dataset.evidence_sources))
    owner_coverage_ratio = safe_divide(owner_count, len(dataset.evidence_sources))
    freshness_compliance_ratio = safe_divide(fresh_count, len(dataset.evidence_sources))
    auditability_score = round(
        confidence_mix.get("A", 0.0) * 0.35
        + version_coverage_ratio * 0.2
        + freshness_compliance_ratio * 0.25
        + owner_coverage_ratio * 0.1
        + status_coverage_ratio * 0.1,
        4,
    )
    return {
        "source_count": len(dataset.evidence_sources),
        "confidence_mix": confidence_mix,
        "version_coverage_ratio": round(version_coverage_ratio, 4),
        "status_coverage_ratio": round(status_coverage_ratio, 4),
        "owner_coverage_ratio": round(owner_coverage_ratio, 4),
        "freshness_compliance_ratio": round(freshness_compliance_ratio, 4),
        "average_source_age_days": round(mean_or_zero([age for age in ages if age is not None]), 2),
        "auditability_score": auditability_score,
        "auditability_level": score_level(auditability_score),
    }


def compute_assumption_register_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.assumptions_register:
        return {}

    status_counts = Counter(record.status for record in dataset.assumptions_register if record.status)
    confidence_counts = Counter(record.confidence_grade.upper() for record in dataset.assumptions_register if record.confidence_grade)
    validated_statuses = {"validated", "confirmed", "已验证"}
    owner_count = 0
    method_count = 0
    overdue_count = 0
    for record in dataset.assumptions_register:
        if record.owner_role:
            owner_count += 1
        if record.validation_method:
            method_count += 1
        due_age = _days_since(record.due_date)
        if due_age is not None and due_age > assumptions.max_assumption_overdue_days and record.status.lower() not in validated_statuses:
            overdue_count += 1
    validated_ratio = safe_divide(
        sum(1 for record in dataset.assumptions_register if record.status.lower() in validated_statuses),
        len(dataset.assumptions_register),
    )
    owner_coverage_ratio = safe_divide(owner_count, len(dataset.assumptions_register))
    method_coverage_ratio = safe_divide(method_count, len(dataset.assumptions_register))
    high_confidence_share = safe_divide(confidence_counts.get("A", 0) + confidence_counts.get("B", 0), len(dataset.assumptions_register))
    governance_score = round(
        validated_ratio * 0.35
        + owner_coverage_ratio * 0.2
        + method_coverage_ratio * 0.2
        + high_confidence_share * 0.15
        + max(0.0, 1 - safe_divide(overdue_count, len(dataset.assumptions_register))) * 0.1,
        4,
    )
    return {
        "assumption_count": len(dataset.assumptions_register),
        "status_mix": dict(sorted(status_counts.items())),
        "confidence_mix": {
            key: round(safe_divide(value, len(dataset.assumptions_register)), 4)
            for key, value in sorted(confidence_counts.items())
        },
        "validated_ratio": round(validated_ratio, 4),
        "owner_coverage_ratio": round(owner_coverage_ratio, 4),
        "validation_method_coverage_ratio": round(method_coverage_ratio, 4),
        "high_confidence_share": round(high_confidence_share, 4),
        "overdue_assumption_count": overdue_count,
        "assumption_governance_score": governance_score,
        "assumption_governance_level": score_level(governance_score),
    }


def compute_gate_threshold_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.gate_thresholds:
        return {}

    gate_ids = {record.gate_id for record in dataset.gate_thresholds if record.gate_id}
    approver_coverage = safe_divide(sum(1 for record in dataset.gate_thresholds if record.approver_role), len(dataset.gate_thresholds))
    fail_action_coverage = safe_divide(sum(1 for record in dataset.gate_thresholds if record.decision_if_fail), len(dataset.gate_thresholds))
    source_grade_coverage = safe_divide(sum(1 for record in dataset.gate_thresholds if record.source_grade_min), len(dataset.gate_thresholds))
    threshold_completeness = safe_divide(
        sum(
            1
            for record in dataset.gate_thresholds
            if record.metric_name and record.operator and record.unit and record.threshold_value is not None
        ),
        len(dataset.gate_thresholds),
    )
    gate_coverage_ratio = safe_divide(len(gate_ids), assumptions.required_gate_count)
    strategic_family_counts: Counter[str] = Counter()
    gate_family_map: dict[str, set[str]] = defaultdict(set)
    for record in dataset.gate_thresholds:
        family = _strategic_metric_family(record.metric_name, record.gate_name)
        if family:
            strategic_family_counts[family] += 1
            gate_family_map[record.gate_id].add(family)
    strategic_family_coverage_ratio = min(
        safe_divide(len(strategic_family_counts), assumptions.required_strategic_metric_families),
        1.0,
    )
    strategic_gate_score = round(
        strategic_family_coverage_ratio * 0.6
        + safe_divide(sum(len(families) for families in gate_family_map.values()), len(dataset.gate_thresholds)) * 0.4,
        4,
    )
    gate_operability_score = round(
        gate_coverage_ratio * 0.35
        + threshold_completeness * 0.25
        + approver_coverage * 0.15
        + fail_action_coverage * 0.15
        + source_grade_coverage * 0.1,
        4,
    )
    return {
        "gate_count": len(gate_ids),
        "threshold_count": len(dataset.gate_thresholds),
        "gate_coverage_ratio": round(gate_coverage_ratio, 4),
        "threshold_completeness_ratio": round(threshold_completeness, 4),
        "approver_coverage_ratio": round(approver_coverage, 4),
        "fail_action_coverage_ratio": round(fail_action_coverage, 4),
        "source_grade_policy_coverage_ratio": round(source_grade_coverage, 4),
        "strategic_metric_family_coverage_ratio": round(strategic_family_coverage_ratio, 4),
        "strategic_metric_family_mix": dict(sorted(strategic_family_counts.items())),
        "uncovered_strategic_metric_families": [
            family
            for family in (
                "capital_return",
                "market_structure",
                "demand_stability",
                "payback_control",
                "risk_control",
            )
            if family not in strategic_family_counts
        ],
        "gate_family_map": {
            gate_id: sorted(families)
            for gate_id, families in sorted(gate_family_map.items())
        },
        "strategic_gate_score": strategic_gate_score,
        "gate_operability_score": gate_operability_score,
        "gate_operability_level": score_level(gate_operability_score),
    }


def compute_approval_chain_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.approval_chain:
        return {}

    gate_steps: dict[str, list] = defaultdict(list)
    for record in dataset.approval_chain:
        gate_steps[record.gate_id].append(record)
    total_gates = max(len({record.gate_id for record in dataset.gate_thresholds if record.gate_id}), assumptions.required_gate_count)
    signed_ratio = safe_divide(
        sum(1 for record in dataset.approval_chain if record.status.lower() in {"signed", "approved", "completed"}),
        len(dataset.approval_chain),
    )
    owner_named_ratio = safe_divide(sum(1 for record in dataset.approval_chain if record.owner_name), len(dataset.approval_chain))
    veto_coverage_ratio = safe_divide(
        sum(1 for gate_id, rows in gate_steps.items() if any(record.veto_flag for record in rows)),
        max(len(gate_steps), 1),
    )
    minimum_step_pass_ratio = safe_divide(
        sum(1 for rows in gate_steps.values() if len(rows) >= assumptions.minimum_signoff_steps),
        max(len(gate_steps), 1),
    )
    gate_signoff_coverage_ratio = safe_divide(len(gate_steps), total_gates)
    signature_chain_score = round(
        gate_signoff_coverage_ratio * 0.3
        + minimum_step_pass_ratio * 0.25
        + signed_ratio * 0.2
        + veto_coverage_ratio * 0.1
        + owner_named_ratio * 0.15,
        4,
    )
    return {
        "approval_row_count": len(dataset.approval_chain),
        "gate_signoff_coverage_ratio": round(gate_signoff_coverage_ratio, 4),
        "minimum_step_pass_ratio": round(minimum_step_pass_ratio, 4),
        "signed_completion_ratio": round(signed_ratio, 4),
        "veto_coverage_ratio": round(veto_coverage_ratio, 4),
        "owner_named_ratio": round(owner_named_ratio, 4),
        "signature_chain_score": signature_chain_score,
        "signature_chain_level": score_level(signature_chain_score),
    }


def compute_update_policy_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.update_policies:
        return {}

    scope_coverage_ratio = min(
        safe_divide(len({record.scope_id for record in dataset.update_policies}), assumptions.required_policy_scopes),
        1.0,
    )
    expiry_coverage_ratio = safe_divide(sum(1 for record in dataset.update_policies if record.expiry_days > 0), len(dataset.update_policies))
    trigger_coverage_ratio = safe_divide(sum(1 for record in dataset.update_policies if record.event_trigger), len(dataset.update_policies))
    owner_coverage_ratio = safe_divide(sum(1 for record in dataset.update_policies if record.owner_role), len(dataset.update_policies))
    sla_coverage_ratio = safe_divide(sum(1 for record in dataset.update_policies if record.sla_days > 0), len(dataset.update_policies))
    aligned_ratio = safe_divide(
        sum(1 for record in dataset.update_policies if record.update_frequency_days > 0 and record.expiry_days >= record.update_frequency_days),
        len(dataset.update_policies),
    )
    refresh_policy_score = round(
        scope_coverage_ratio * 0.25
        + expiry_coverage_ratio * 0.2
        + trigger_coverage_ratio * 0.2
        + owner_coverage_ratio * 0.15
        + sla_coverage_ratio * 0.1
        + aligned_ratio * 0.1,
        4,
    )
    return {
        "policy_count": len(dataset.update_policies),
        "scope_coverage_ratio": round(scope_coverage_ratio, 4),
        "expiry_rule_coverage_ratio": round(expiry_coverage_ratio, 4),
        "event_trigger_coverage_ratio": round(trigger_coverage_ratio, 4),
        "owner_coverage_ratio": round(owner_coverage_ratio, 4),
        "sla_coverage_ratio": round(sla_coverage_ratio, 4),
        "refresh_expiry_alignment_ratio": round(aligned_ratio, 4),
        "refresh_policy_score": refresh_policy_score,
        "refresh_policy_level": score_level(refresh_policy_score),
    }


def compute_field_dictionary_metrics(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    if not dataset.field_dictionary:
        return {}

    definition_coverage_ratio = safe_divide(sum(1 for record in dataset.field_dictionary if record.definition), len(dataset.field_dictionary))
    type_coverage_ratio = safe_divide(sum(1 for record in dataset.field_dictionary if record.data_type), len(dataset.field_dictionary))
    source_table_coverage_ratio = safe_divide(sum(1 for record in dataset.field_dictionary if record.source_table), len(dataset.field_dictionary))
    reusable_field_share = safe_divide(sum(1 for record in dataset.field_dictionary if record.reusable_flag), len(dataset.field_dictionary))
    required_field_share = safe_divide(sum(1 for record in dataset.field_dictionary if record.required_flag), len(dataset.field_dictionary))
    naming_compliance_ratio = safe_divide(
        sum(1 for record in dataset.field_dictionary if record.naming_style == assumptions.required_naming_style),
        len(dataset.field_dictionary),
    )
    dictionary_score = round(
        definition_coverage_ratio * 0.25
        + type_coverage_ratio * 0.2
        + source_table_coverage_ratio * 0.15
        + reusable_field_share * 0.15
        + required_field_share * 0.05
        + naming_compliance_ratio * 0.2,
        4,
    )
    return {
        "field_count": len(dataset.field_dictionary),
        "definition_coverage_ratio": round(definition_coverage_ratio, 4),
        "data_type_coverage_ratio": round(type_coverage_ratio, 4),
        "source_table_coverage_ratio": round(source_table_coverage_ratio, 4),
        "reusable_field_share": round(reusable_field_share, 4),
        "required_field_share": round(required_field_share, 4),
        "naming_compliance_ratio": round(naming_compliance_ratio, 4),
        "naming_style_mix": dict(sorted(Counter(record.naming_style for record in dataset.field_dictionary if record.naming_style).items())),
        "dictionary_reuse_score": dictionary_score,
        "dictionary_reuse_level": score_level(dictionary_score),
    }
