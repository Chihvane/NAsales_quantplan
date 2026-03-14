from __future__ import annotations

from collections import Counter, defaultdict

from .models import HorizontalSystemAssumptions, HorizontalSystemDataset
from .stats_utils import mean_or_zero, safe_divide, score_level


def compute_master_data_governance_metrics(
    dataset: HorizontalSystemDataset,
    assumptions: HorizontalSystemAssumptions,
) -> dict:
    entities = dataset.master_data_entities
    fields = dataset.data_dictionary_fields
    if not entities and not fields:
        return {}

    entity_types = {record.entity_type for record in entities if record.entity_type}
    required_entity_type_names = tuple(name for name in assumptions.required_entity_type_names if name)
    if required_entity_type_names:
        covered_required_entity_types = sorted(entity_types & set(required_entity_type_names))
        missing_required_entity_types = sorted(set(required_entity_type_names) - entity_types)
        entity_type_coverage_ratio = safe_divide(len(covered_required_entity_types), len(required_entity_type_names))
    else:
        covered_required_entity_types = sorted(entity_types)
        missing_required_entity_types = []
        entity_type_coverage_ratio = min(safe_divide(len(entity_types), assumptions.required_entity_types), 1.0)

    approved_entity_ratio = safe_divide(sum(1 for record in entities if record.approved_flag), len(entities))
    active_entity_ratio = safe_divide(sum(1 for record in entities if record.active_flag), len(entities))
    duplicate_free_ratio = safe_divide(sum(1 for record in entities if not record.duplicate_flag), len(entities))
    required_field_compliance_ratio = safe_divide(
        sum(1 for record in entities if record.missing_required_field_count == 0),
        len(entities),
    )
    owner_coverage_ratio = safe_divide(sum(1 for record in entities if record.owner_role), len(entities))
    version_coverage_ratio = safe_divide(sum(1 for record in entities if record.version), len(entities))

    dictionary_approval_ratio = safe_divide(sum(1 for record in fields if record.approved_flag), len(fields))
    validation_rule_coverage_ratio = safe_divide(sum(1 for record in fields if record.validation_rule), len(fields))
    dictionary_version_coverage_ratio = safe_divide(sum(1 for record in fields if record.version), len(fields))
    entity_dictionary_alignment_ratio = safe_divide(
        sum(1 for record in fields if record.entity_type in entity_types),
        len(fields),
    )
    field_groups = {record.field_group for record in fields if record.field_group}
    required_field_groups = tuple(group for group in assumptions.required_field_groups if group)
    if required_field_groups:
        covered_field_groups = sorted(field_groups & set(required_field_groups))
        missing_field_groups = sorted(set(required_field_groups) - field_groups)
        core_field_group_coverage_ratio = safe_divide(len(covered_field_groups), len(required_field_groups))
    else:
        covered_field_groups = sorted(field_groups)
        missing_field_groups = []
        core_field_group_coverage_ratio = 1.0

    master_data_health_score = round(
        entity_type_coverage_ratio * 0.2
        + dictionary_approval_ratio * 0.18
        + duplicate_free_ratio * 0.18
        + required_field_compliance_ratio * 0.16
        + validation_rule_coverage_ratio * 0.12
        + version_coverage_ratio * 0.08
        + dictionary_version_coverage_ratio * 0.04
        + entity_dictionary_alignment_ratio * 0.02
        + core_field_group_coverage_ratio * 0.02,
        4,
    )

    return {
        "entity_count": len(entities),
        "field_count": len(fields),
        "entity_type_mix": dict(sorted(Counter(record.entity_type for record in entities if record.entity_type).items())),
        "required_entity_type_targets": list(required_entity_type_names),
        "covered_required_entity_types": covered_required_entity_types,
        "missing_required_entity_types": missing_required_entity_types,
        "entity_type_coverage_ratio": round(entity_type_coverage_ratio, 4),
        "approved_entity_ratio": round(approved_entity_ratio, 4),
        "active_entity_ratio": round(active_entity_ratio, 4),
        "duplicate_free_ratio": round(duplicate_free_ratio, 4),
        "required_field_compliance_ratio": round(required_field_compliance_ratio, 4),
        "owner_coverage_ratio": round(owner_coverage_ratio, 4),
        "version_coverage_ratio": round(version_coverage_ratio, 4),
        "dictionary_approval_ratio": round(dictionary_approval_ratio, 4),
        "validation_rule_coverage_ratio": round(validation_rule_coverage_ratio, 4),
        "dictionary_version_coverage_ratio": round(dictionary_version_coverage_ratio, 4),
        "entity_dictionary_alignment_ratio": round(entity_dictionary_alignment_ratio, 4),
        "required_field_group_targets": list(required_field_groups),
        "covered_field_groups": covered_field_groups,
        "missing_field_groups": missing_field_groups,
        "core_field_group_coverage_ratio": round(core_field_group_coverage_ratio, 4),
        "master_data_health_score": master_data_health_score,
        "master_data_health_level": score_level(master_data_health_score),
    }


def compute_evidence_audit_chain_metrics(
    dataset: HorizontalSystemDataset,
    assumptions: HorizontalSystemAssumptions,
) -> dict:
    lineage = dataset.evidence_lineage
    audits = dataset.audit_events
    if not lineage and not audits:
        return {}

    target_metric_coverage_ratio = safe_divide(sum(1 for record in lineage if record.target_metric_id), len(lineage))
    dataset_version_coverage_ratio = safe_divide(sum(1 for record in lineage if record.dataset_version), len(lineage))
    script_version_coverage_ratio = safe_divide(sum(1 for record in lineage if record.script_version), len(lineage))
    approval_linkage_ratio = safe_divide(sum(1 for record in lineage if record.approval_ref), len(lineage))
    reproducibility_ratio = safe_divide(sum(1 for record in lineage if record.reproducible_flag), len(lineage))
    traceback_sla_ratio = safe_divide(
        sum(1 for record in lineage if record.reconstruction_minutes <= assumptions.max_traceback_minutes),
        len(lineage),
    )
    average_transform_step_count = mean_or_zero([record.transform_step_count for record in lineage])

    immutable_audit_ratio = safe_divide(sum(1 for record in audits if record.immutable_flag), len(audits))
    audit_actor_coverage_ratio = safe_divide(sum(1 for record in audits if record.actor_role), len(audits))
    audit_approval_ref_ratio = safe_divide(sum(1 for record in audits if record.approval_ref), len(audits))
    audit_closed_ratio = safe_divide(
        sum(1 for record in audits if record.status.lower() in {"closed", "approved", "completed"}),
        len(audits),
    )

    audit_trace_score = round(
        reproducibility_ratio * 0.22
        + traceback_sla_ratio * 0.18
        + immutable_audit_ratio * 0.18
        + approval_linkage_ratio * 0.14
        + audit_approval_ref_ratio * 0.12
        + script_version_coverage_ratio * 0.08
        + dataset_version_coverage_ratio * 0.08,
        4,
    )

    return {
        "lineage_count": len(lineage),
        "audit_event_count": len(audits),
        "target_metric_coverage_ratio": round(target_metric_coverage_ratio, 4),
        "dataset_version_coverage_ratio": round(dataset_version_coverage_ratio, 4),
        "script_version_coverage_ratio": round(script_version_coverage_ratio, 4),
        "approval_linkage_ratio": round(approval_linkage_ratio, 4),
        "reproducibility_ratio": round(reproducibility_ratio, 4),
        "traceback_sla_ratio": round(traceback_sla_ratio, 4),
        "average_transform_step_count": round(average_transform_step_count, 2),
        "immutable_audit_ratio": round(immutable_audit_ratio, 4),
        "audit_actor_coverage_ratio": round(audit_actor_coverage_ratio, 4),
        "audit_approval_ref_ratio": round(audit_approval_ref_ratio, 4),
        "audit_closed_ratio": round(audit_closed_ratio, 4),
        "audit_type_mix": dict(sorted(Counter(record.event_type for record in audits if record.event_type).items())),
        "audit_trace_score": round(audit_trace_score, 4),
        "audit_trace_level": score_level(audit_trace_score),
    }


def compute_decision_threshold_system_metrics(
    dataset: HorizontalSystemDataset,
    assumptions: HorizontalSystemAssumptions,
) -> dict:
    rules = dataset.decision_rules
    triggers = dataset.decision_triggers
    if not rules and not triggers:
        return {}

    scenarios = {record.scenario for record in rules if record.scenario}
    active_rules = [record for record in rules if record.active_flag]
    required_rule_scenario_names = tuple(name for name in assumptions.required_rule_scenario_names if name)
    if required_rule_scenario_names:
        covered_required_scenarios = sorted(scenarios & set(required_rule_scenario_names))
        missing_required_scenarios = sorted(set(required_rule_scenario_names) - scenarios)
        scenario_coverage_ratio = safe_divide(len(covered_required_scenarios), len(required_rule_scenario_names))
    else:
        covered_required_scenarios = sorted(scenarios)
        missing_required_scenarios = []
        scenario_coverage_ratio = min(safe_divide(len(scenarios), assumptions.required_rule_scenarios), 1.0)
    active_rule_ratio = safe_divide(len(active_rules), len(rules))
    version_coverage_ratio = safe_divide(sum(1 for record in rules if record.version), len(rules))
    stop_loss_rule_ratio = safe_divide(sum(1 for record in rules if record.stop_loss_flag), len(rules))
    approver_coverage_ratio = safe_divide(sum(1 for record in rules if record.approver_role), len(rules))

    active_rule_ids = {record.rule_id for record in active_rules}
    triggered_rule_ids = {record.rule_id for record in triggers if record.rule_id}
    triggered_rule_coverage_ratio = safe_divide(len(triggered_rule_ids & active_rule_ids), max(len(active_rule_ids), 1))
    trigger_resolution_ratio = safe_divide(sum(1 for record in triggers if record.resolved_flag), len(triggers))
    trigger_approval_ref_ratio = safe_divide(sum(1 for record in triggers if record.approval_ref), len(triggers))
    decision_status_mix = dict(sorted(Counter(record.decision_status for record in triggers if record.decision_status).items()))
    stop_loss_trigger_ratio = safe_divide(
        sum(1 for record in triggers if record.rule_id in {rule.rule_id for rule in rules if rule.stop_loss_flag}),
        len(triggers),
    )

    decision_gate_control_score = round(
        scenario_coverage_ratio * 0.2
        + active_rule_ratio * 0.1
        + version_coverage_ratio * 0.1
        + stop_loss_rule_ratio * 0.12
        + approver_coverage_ratio * 0.1
        + triggered_rule_coverage_ratio * 0.12
        + trigger_resolution_ratio * 0.14
        + trigger_approval_ref_ratio * 0.12
        ,
        4,
    )

    rules_by_scenario: dict[str, int] = defaultdict(int)
    for record in rules:
        if record.scenario:
            rules_by_scenario[record.scenario] += 1

    return {
        "rule_count": len(rules),
        "trigger_count": len(triggers),
        "rule_scenario_mix": dict(sorted(rules_by_scenario.items())),
        "required_rule_scenario_targets": list(required_rule_scenario_names),
        "covered_required_rule_scenarios": covered_required_scenarios,
        "missing_required_rule_scenarios": missing_required_scenarios,
        "scenario_coverage_ratio": round(scenario_coverage_ratio, 4),
        "active_rule_ratio": round(active_rule_ratio, 4),
        "version_coverage_ratio": round(version_coverage_ratio, 4),
        "stop_loss_rule_ratio": round(stop_loss_rule_ratio, 4),
        "approver_coverage_ratio": round(approver_coverage_ratio, 4),
        "triggered_rule_coverage_ratio": round(triggered_rule_coverage_ratio, 4),
        "trigger_resolution_ratio": round(trigger_resolution_ratio, 4),
        "trigger_approval_ref_ratio": round(trigger_approval_ref_ratio, 4),
        "stop_loss_trigger_ratio": round(stop_loss_trigger_ratio, 4),
        "decision_status_mix": decision_status_mix,
        "decision_gate_control_score": round(decision_gate_control_score, 4),
        "decision_gate_control_level": score_level(decision_gate_control_score),
    }
