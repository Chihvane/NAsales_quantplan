from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from .stats_utils import score_level


def _score_level(score: float) -> str:
    return score_level(score)


def serialize_payload(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: serialize_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_payload(item) for item in value]
    return value


def build_table_inventory(dataset: Any) -> dict[str, dict[str, Any]]:
    if not is_dataclass(dataset):
        return {}

    inventory = {}
    for field_def in fields(dataset):
        value = getattr(dataset, field_def.name)
        record_count = len(value) if hasattr(value, "__len__") else None
        inventory[field_def.name] = {
            "record_count": record_count,
            "available": bool(record_count),
        }
    return inventory


def _derive_gate_result(
    section_definition: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    gate_status_key = section_definition.get("gate_status_key")
    recommendation_keys = ("recommendation", "expansion_gate_status", "decision_status", "status")
    pass_values = {"pass", "go", "scale_up", "recommended_entry", "ready_for_execution_system", "control_tower_ready"}
    review_values = {
        "review",
        "pilot_first",
        "pilot_only",
        "hold_and_optimize",
        "selective",
        "prepare_rollout",
        "control_tower_needs_hardening",
    }
    fail_values = {"fail", "no_go", "rollback", "stop", "not_recommended", "control_tower_not_ready"}

    if gate_status_key and gate_status_key in metrics:
        raw_value = metrics.get(gate_status_key)
        raw_value_normalized = str(raw_value).strip().lower()
        if raw_value_normalized in pass_values:
            status = "pass"
        elif raw_value_normalized in fail_values:
            status = "fail"
        elif raw_value_normalized in review_values:
            status = "review"
        else:
            status = "review" if raw_value not in (None, "", []) else "not_applicable"
        return {
            "status": status,
            "source": gate_status_key,
            "raw_value": raw_value,
            "failed_items": [],
        }

    gate_results = metrics.get("gate_results")
    if isinstance(gate_results, dict) and gate_results:
        failed_items = [key for key, value in gate_results.items() if not bool(value)]
        if not failed_items:
            status = "pass"
        elif len(failed_items) >= max(1, len(gate_results) // 2):
            status = "fail"
        else:
            status = "review"
        return {
            "status": status,
            "source": "gate_results",
            "raw_value": gate_results,
            "failed_items": failed_items,
        }

    for key in recommendation_keys:
        raw_value = metrics.get(key)
        if raw_value in (None, "", [], {}):
            continue
        raw_value_normalized = str(raw_value).strip().lower()
        if raw_value_normalized in pass_values:
            status = "pass"
        elif raw_value_normalized in fail_values:
            status = "fail"
        else:
            status = "review"
        return {
            "status": status,
            "source": key,
            "raw_value": raw_value,
            "failed_items": [],
        }

    return {
        "status": "not_applicable",
        "source": "",
        "raw_value": "",
        "failed_items": [],
    }


def build_section_payload(
    section_id: str,
    section_definition: dict[str, Any],
    metrics: dict[str, Any],
    table_inventory: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    required_tables = list(section_definition.get("required_tables", []))
    metric_ids = list(section_definition.get("metric_ids", []))
    quality_targets = section_definition.get("quality_targets", {})

    record_counts = {
        table_name: table_inventory.get(table_name, {}).get("record_count", 0) or 0
        for table_name in required_tables
    }
    available_tables = [table_name for table_name, count in record_counts.items() if count > 0]
    missing_tables = [table_name for table_name, count in record_counts.items() if count <= 0]

    if required_tables:
        completeness_ratio = len(available_tables) / len(required_tables)
        richness_values = []
        for table_name in required_tables:
            target_count = quality_targets.get(table_name, 1) or 1
            richness_values.append(min(record_counts.get(table_name, 0) / target_count, 1.0))
        richness_ratio = mean(richness_values) if richness_values else 0.0
    else:
        completeness_ratio = 1.0
        richness_ratio = 1.0
    quality_score = completeness_ratio * 0.65 + richness_ratio * 0.35

    data_quality = {
        "record_counts": record_counts,
        "available_tables": available_tables,
        "missing_tables": missing_tables,
        "completeness_ratio": round(completeness_ratio, 4),
        "richness_ratio": round(richness_ratio, 4),
        "quality_score": round(quality_score, 4),
        "quality_level": _score_level(quality_score),
    }
    return {
        "id": section_id,
        "title": section_definition.get("title", section_id),
        "required_tables": required_tables,
        "metric_ids": metric_ids,
        "granularity": {
            "analysis_grain": section_definition.get("analysis_grain", ""),
            "entity_grain": section_definition.get("entity_grain", ""),
            "time_grain": section_definition.get("time_grain", ""),
        },
        "channel_scope": list(section_definition.get("channel_scope", [])),
        "master_data_ref": list(section_definition.get("master_data_refs", [])),
        "evidence_ref": list(section_definition.get("evidence_refs", [])),
        "rule_ref": list(section_definition.get("rule_refs", [])),
        "gate_result": _derive_gate_result(section_definition, metrics),
        "data_quality": data_quality,
        "confidence": {
            "score": round(quality_score, 4),
            "level": _score_level(quality_score),
        },
        "metrics": metrics,
    }


def build_report_overview(sections: dict[str, dict[str, Any]]) -> dict[str, Any]:
    confidence_scores = [
        section.get("confidence", {}).get("score", 0.0)
        for section in sections.values()
    ]
    levels = [section.get("confidence", {}).get("level", "low") for section in sections.values()]
    all_channels = sorted(
        {
            channel
            for section in sections.values()
            for channel in section.get("channel_scope", [])
            if channel
        }
    )
    gate_statuses = [section.get("gate_result", {}).get("status", "not_applicable") for section in sections.values()]
    sections_with_master_refs = sum(1 for section in sections.values() if section.get("master_data_ref"))
    sections_with_evidence_refs = sum(1 for section in sections.values() if section.get("evidence_ref"))
    sections_with_rule_refs = sum(1 for section in sections.values() if section.get("rule_ref"))
    section_count = len(sections) or 1
    return {
        "section_count": len(sections),
        "average_confidence_score": round(mean(confidence_scores), 4) if confidence_scores else 0.0,
        "confidence_mix": {
            "high": sum(1 for level in levels if level == "high"),
            "medium": sum(1 for level in levels if level == "medium"),
            "low": sum(1 for level in levels if level == "low"),
        },
        "connected_channel_scope": all_channels,
        "control_tower_binding": {
            "master_data_ref_coverage_ratio": round(sections_with_master_refs / section_count, 4),
            "evidence_ref_coverage_ratio": round(sections_with_evidence_refs / section_count, 4),
            "rule_ref_coverage_ratio": round(sections_with_rule_refs / section_count, 4),
            "gate_status_mix": {
                "pass": sum(1 for status in gate_statuses if status == "pass"),
                "review": sum(1 for status in gate_statuses if status == "review"),
                "fail": sum(1 for status in gate_statuses if status == "fail"),
                "not_applicable": sum(1 for status in gate_statuses if status == "not_applicable"),
            },
        },
    }


def build_standard_report(
    report_id: str,
    section_structure: dict[str, dict[str, Any]],
    metric_specs: list[dict[str, Any]],
    dataset: Any,
    assumptions: Any,
    section_metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    table_inventory = build_table_inventory(dataset)
    sections = {
        section_id: build_section_payload(
            section_id,
            section_definition,
            section_metrics.get(section_id, {}),
            table_inventory,
        )
        for section_id, section_definition in section_structure.items()
    }
    return {
        "metadata": {
            "report_id": report_id,
            "report_version": "2026.03",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "section_order": list(section_structure.keys()),
            "section_structure": serialize_payload(section_structure),
            "metric_specs": metric_specs,
            "assumptions": serialize_payload(assumptions),
            "table_inventory": table_inventory,
        },
        "overview": build_report_overview(sections),
        "sections": sections,
    }


def finalize_report_overview(report: dict[str, Any]) -> dict[str, Any]:
    overview = report.setdefault("overview", {})
    overview["validation_summary"] = report.get("validation", {}).get("summary", {})
    overview["uncertainty_keys"] = list(report.get("uncertainty", {}).keys())
    return report


def attach_headline_metrics(
    report: dict[str, Any],
    headline_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    report.setdefault("overview", {})["headline_metrics"] = headline_metrics
    return report


def attach_decision_summary(
    report: dict[str, Any],
    decision_summary: dict[str, Any],
) -> dict[str, Any]:
    overview = report.setdefault("overview", {})
    overview["decision_summary"] = decision_summary
    overview["decision_signal"] = decision_summary.get("decision_signal")
    overview["decision_score"] = decision_summary.get("decision_score")
    return report


def build_cli_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "validation": report.get("validation", {}).get("summary", {}),
        "overview": report.get("overview", {}),
        "headline_metrics": report.get("overview", {}).get("headline_metrics", []),
        "decision_signal": report.get("overview", {}).get("decision_signal"),
        "decision_score": report.get("overview", {}).get("decision_score"),
        "sections": list(report.get("sections", {}).keys()),
    }
