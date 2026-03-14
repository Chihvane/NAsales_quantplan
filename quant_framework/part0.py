from __future__ import annotations

from .decision_summary import build_part0_decision_summary
from .models import Part0Assumptions, Part0Dataset
from .part0_metrics import (
    compute_approval_chain_metrics,
    compute_assumption_register_metrics,
    compute_data_confidence_metrics,
    compute_decision_tree_metrics,
    compute_field_dictionary_metrics,
    compute_gate_threshold_metrics,
    compute_update_policy_metrics,
)
from .registry import PART0_METRICS
from .reporting import attach_decision_summary, attach_headline_metrics, build_standard_report, finalize_report_overview
from .uncertainty import build_part0_uncertainty_snapshot
from .validation import build_part0_methodology_validation


PART0_SECTION_STRUCTURE = {
    "0.1": {
        "title": "全局决策树与研究问题映射",
        "required_tables": ["decision_nodes"],
        "metric_ids": ["decision_tree_governance"],
        "quality_targets": {"decision_nodes": 10},
        "analysis_grain": "decision node",
        "entity_grain": "decision question",
        "time_grain": "version event",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.decision_domain"],
        "evidence_refs": ["evidence.decision_tree"],
        "rule_refs": ["gate.governance_scope"],
    },
    "0.2": {
        "title": "数据置信度与版本控制",
        "required_tables": ["evidence_sources"],
        "metric_ids": ["data_confidence_versioning"],
        "quality_targets": {"evidence_sources": 8},
        "analysis_grain": "source record",
        "entity_grain": "evidence source",
        "time_grain": "source freshness window",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.source_system"],
        "evidence_refs": ["evidence.source_register"],
        "rule_refs": ["gate.data_confidence"],
    },
    "0.3": {
        "title": "策略假设登记与验证机制",
        "required_tables": ["assumptions_register"],
        "metric_ids": ["assumption_register"],
        "quality_targets": {"assumptions_register": 8},
        "analysis_grain": "assumption item",
        "entity_grain": "strategic assumption",
        "time_grain": "assumption due date",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.assumption_domain"],
        "evidence_refs": ["evidence.assumption_register"],
        "rule_refs": ["gate.assumption_validity"],
    },
    "0.4": {
        "title": "决策门槛与 Gate 管理",
        "required_tables": ["gate_thresholds"],
        "metric_ids": ["gate_threshold_operability"],
        "quality_targets": {"gate_thresholds": 5},
        "analysis_grain": "gate threshold",
        "entity_grain": "gate x metric",
        "time_grain": "gate version",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.gate_threshold"],
        "evidence_refs": ["evidence.gate_threshold_register"],
        "rule_refs": ["gate.entry", "gate.scale", "gate.exit"],
    },
    "0.5": {
        "title": "责任链与签字流",
        "required_tables": ["approval_chain", "gate_thresholds"],
        "metric_ids": ["signature_chain_integrity"],
        "quality_targets": {"approval_chain": 10, "gate_thresholds": 5},
        "analysis_grain": "approval step",
        "entity_grain": "gate x signer",
        "time_grain": "approval timestamp",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.approval_role"],
        "evidence_refs": ["evidence.approval_chain"],
        "rule_refs": ["gate.approval_route"],
    },
    "0.6": {
        "title": "更新周期与失效规则",
        "required_tables": ["update_policies"],
        "metric_ids": ["update_expiration_policy"],
        "quality_targets": {"update_policies": 6},
        "analysis_grain": "update policy",
        "entity_grain": "scope x refresh rule",
        "time_grain": "refresh cadence",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.policy_scope"],
        "evidence_refs": ["evidence.update_policy"],
        "rule_refs": ["gate.expiry_control"],
    },
    "0.7": {
        "title": "字段字典、复用与审计要求",
        "required_tables": ["field_dictionary"],
        "metric_ids": ["field_dictionary_reuse"],
        "quality_targets": {"field_dictionary": 12},
        "analysis_grain": "field dictionary row",
        "entity_grain": "field definition",
        "time_grain": "dictionary version",
        "channel_scope": ["governance"],
        "master_data_refs": ["mdm.field_dictionary"],
        "evidence_refs": ["evidence.field_dictionary"],
        "rule_refs": ["gate.naming_compliance"],
    },
}


def build_part0_quant_report(
    dataset: Part0Dataset,
    assumptions: Part0Assumptions,
) -> dict:
    section_metrics = {
        "0.1": compute_decision_tree_metrics(dataset, assumptions),
        "0.2": compute_data_confidence_metrics(dataset, assumptions),
        "0.3": compute_assumption_register_metrics(dataset, assumptions),
        "0.4": compute_gate_threshold_metrics(dataset, assumptions),
        "0.5": compute_approval_chain_metrics(dataset, assumptions),
        "0.6": compute_update_policy_metrics(dataset, assumptions),
        "0.7": compute_field_dictionary_metrics(dataset, assumptions),
    }
    report = build_standard_report(
        report_id="part0_quant_report",
        section_structure=PART0_SECTION_STRUCTURE,
        metric_specs=[metric.__dict__ for metric in PART0_METRICS],
        dataset=dataset,
        assumptions=assumptions,
        section_metrics=section_metrics,
    )
    report["uncertainty"] = build_part0_uncertainty_snapshot(report)
    report["validation"] = build_part0_methodology_validation(report)
    report = attach_decision_summary(report, build_part0_decision_summary(section_metrics))
    report = attach_headline_metrics(
        report,
        [
            {
                "key": "decision_tree_score",
                "label": "决策树完整度",
                "value": section_metrics["0.1"].get("decision_tree_score", 0.0),
                "unit": "score",
            },
            {
                "key": "auditability_score",
                "label": "证据链审计分",
                "value": section_metrics["0.2"].get("auditability_score", 0.0),
                "unit": "score",
            },
            {
                "key": "gate_operability_score",
                "label": "Gate 可执行性",
                "value": section_metrics["0.4"].get("gate_operability_score", 0.0),
                "unit": "score",
            },
            {
                "key": "strategic_gate_score",
                "label": "战略 Gate 覆盖分",
                "value": section_metrics["0.4"].get("strategic_gate_score", 0.0),
                "unit": "score",
            },
            {
                "key": "signature_chain_score",
                "label": "签字链完整性",
                "value": section_metrics["0.5"].get("signature_chain_score", 0.0),
                "unit": "score",
            },
            {
                "key": "refresh_policy_score",
                "label": "更新失效规则分",
                "value": section_metrics["0.6"].get("refresh_policy_score", 0.0),
                "unit": "score",
            },
        ],
    )
    return finalize_report_overview(report)
