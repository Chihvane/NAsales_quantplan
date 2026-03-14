from __future__ import annotations

from .decision_summary import build_horizontal_system_decision_summary
from .horizontal_metrics import (
    compute_decision_threshold_system_metrics,
    compute_evidence_audit_chain_metrics,
    compute_master_data_governance_metrics,
)
from .models import HorizontalSystemAssumptions, HorizontalSystemDataset
from .registry import HORIZONTAL_SYSTEM_METRICS
from .reporting import (
    attach_decision_summary,
    attach_headline_metrics,
    build_standard_report,
    finalize_report_overview,
)
from .uncertainty import build_horizontal_system_uncertainty_snapshot
from .validation import build_horizontal_system_validation


HORIZONTAL_SYSTEM_SECTION_STRUCTURE = {
    "H1": {
        "title": "数据字典与主数据管理",
        "required_tables": ["master_data_entities", "data_dictionary_fields"],
        "metric_ids": ["master_data_governance"],
        "quality_targets": {"master_data_entities": 8, "data_dictionary_fields": 12},
        "analysis_grain": "master data entity / field row",
        "entity_grain": "entity type x field group",
        "time_grain": "dictionary version",
        "channel_scope": ["control_tower"],
        "master_data_refs": ["mdm.sku", "mdm.channel", "mdm.calendar", "mdm.price_metric", "mdm.supplier"],
        "evidence_refs": ["evidence.dictionary_versions"],
        "rule_refs": ["control.master_data_health"],
    },
    "H2": {
        "title": "证据链与审计链",
        "required_tables": ["evidence_lineage", "audit_events"],
        "metric_ids": ["evidence_audit_chain"],
        "quality_targets": {"evidence_lineage": 8, "audit_events": 8},
        "analysis_grain": "lineage / audit event",
        "entity_grain": "metric lineage x audit record",
        "time_grain": "audit timestamp",
        "channel_scope": ["control_tower"],
        "master_data_refs": ["mdm.source_system", "mdm.approval_role"],
        "evidence_refs": ["evidence.lineage_register", "evidence.audit_events"],
        "rule_refs": ["control.audit_traceability"],
    },
    "H3": {
        "title": "决策门槛系统",
        "required_tables": ["decision_rules", "decision_triggers"],
        "metric_ids": ["decision_threshold_system"],
        "quality_targets": {"decision_rules": 8, "decision_triggers": 6},
        "analysis_grain": "decision rule / trigger",
        "entity_grain": "scenario x gate x trigger",
        "time_grain": "trigger timestamp",
        "channel_scope": ["control_tower"],
        "master_data_refs": ["mdm.gate_threshold", "mdm.rule_scenario"],
        "evidence_refs": ["evidence.decision_trigger"],
        "rule_refs": ["control.stop_loss", "control.go_no_go"],
    },
}


def build_horizontal_system_report(
    dataset: HorizontalSystemDataset,
    assumptions: HorizontalSystemAssumptions,
) -> dict:
    section_metrics = {
        "H1": compute_master_data_governance_metrics(dataset, assumptions),
        "H2": compute_evidence_audit_chain_metrics(dataset, assumptions),
        "H3": compute_decision_threshold_system_metrics(dataset, assumptions),
    }
    report = build_standard_report(
        report_id="horizontal_system_management_report",
        section_structure=HORIZONTAL_SYSTEM_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in HORIZONTAL_SYSTEM_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_horizontal_system_uncertainty_snapshot(report)
    report["validation"] = build_horizontal_system_validation(report)
    report = attach_headline_metrics(
        report,
        [
            {
                "key": "master_data_health_score",
                "label": "主数据健康分",
                "value": section_metrics["H1"].get("master_data_health_score", 0.0),
                "unit": "score",
            },
            {
                "key": "audit_trace_score",
                "label": "证据链追溯分",
                "value": section_metrics["H2"].get("audit_trace_score", 0.0),
                "unit": "score",
            },
            {
                "key": "decision_gate_control_score",
                "label": "决策门槛控制分",
                "value": section_metrics["H3"].get("decision_gate_control_score", 0.0),
                "unit": "score",
            },
            {
                "key": "traceback_sla_ratio",
                "label": "30分钟追溯达标率",
                "value": section_metrics["H2"].get("traceback_sla_ratio", 0.0),
                "unit": "ratio",
            },
        ],
    )
    report = attach_decision_summary(report, build_horizontal_system_decision_summary(section_metrics))
    return finalize_report_overview(report)
