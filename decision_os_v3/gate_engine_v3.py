from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any, Mapping

from .models import (
    DecisionRecordV3,
    GateConditionV3,
    GateDecisionOutputV3,
    GateEvaluationV3,
    GateSpecV3,
)


def _compare(left: Any, operator: str, right: Any) -> bool:
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    raise ValueError(f"Unsupported operator: {operator}")


def _resolve_mapping_value(namespace_ref: str, bundles: Mapping[str, Mapping[str, Any]]) -> Any:
    namespace, _, ref = namespace_ref.partition(".")
    mapping = bundles.get(namespace, {})
    return mapping.get(ref)


def _resolve_condition_value(
    condition: GateConditionV3,
    model_outputs: Mapping[str, Any],
    factor_scores: Mapping[str, Any],
    capital_state: Mapping[str, Any],
    risk_state: Mapping[str, Any],
) -> Any:
    source_map = {
        "model_output": model_outputs,
        "factor": factor_scores,
        "capital": capital_state,
        "risk": risk_state,
    }
    return source_map.get(condition.source, {}).get(condition.ref)


def build_gate_spec(payload: Mapping[str, Any]) -> GateSpecV3:
    body = payload.get("gate", payload)
    decision_output = body.get("decision_output", {})
    return GateSpecV3(
        gate_id=str(body.get("gate_id", "")),
        schema_version=str(body.get("schema_version", "")),
        logic=str(body.get("logic", "AND")).upper(),
        conditions=tuple(
            GateConditionV3(
                source=str(condition.get("source", "model_output")),
                ref=str(condition.get("ref", "")),
                operator=str(condition.get("operator", "==")),
                value=condition.get("value"),
                budget_ref=str(condition.get("budget_ref", "")),
            )
            for condition in body.get("conditions", [])
            if isinstance(condition, Mapping)
        ),
        decision_output=GateDecisionOutputV3(
            on_pass=str(decision_output.get("pass", "GO")),
            on_fail=str(decision_output.get("fail", "NO_GO")),
        ),
    )


def evaluate_gate_v3(
    gate_spec: GateSpecV3 | Mapping[str, Any],
    model_outputs: Mapping[str, Any],
    factor_scores: Mapping[str, Any] | None = None,
    capital_state: Mapping[str, Any] | None = None,
    risk_state: Mapping[str, Any] | None = None,
) -> GateEvaluationV3:
    spec = gate_spec if isinstance(gate_spec, GateSpecV3) else build_gate_spec(gate_spec)
    factor_scores = factor_scores or {}
    capital_state = capital_state or {}
    risk_state = risk_state or {}

    bundles = {
        "model_output": model_outputs,
        "factor": factor_scores,
        "capital_pool": capital_state,
        "risk_budget": risk_state,
    }

    failed_conditions: list[str] = []
    capital_blocked = False
    risk_blocked = False
    passed_conditions = 0

    for condition in spec.conditions:
        current_value = _resolve_condition_value(
            condition, model_outputs, factor_scores, capital_state, risk_state
        )
        threshold = (
            _resolve_mapping_value(condition.budget_ref, bundles)
            if condition.budget_ref
            else condition.value
        )
        if current_value is None or threshold is None or not _compare(current_value, condition.operator, threshold):
            failed_conditions.append(f"{condition.source}:{condition.ref}")
            if condition.source == "capital" or condition.budget_ref.startswith("capital_pool."):
                capital_blocked = True
            if condition.source == "risk" or condition.budget_ref.startswith("risk_budget."):
                risk_blocked = True
        else:
            passed_conditions += 1

    if spec.logic == "AND":
        status = spec.decision_output.on_pass if not failed_conditions else spec.decision_output.on_fail
    elif spec.logic == "OR":
        status = spec.decision_output.on_pass if passed_conditions > 0 else spec.decision_output.on_fail
    else:
        raise ValueError(f"Unsupported gate logic: {spec.logic}")

    return GateEvaluationV3(
        gate_id=spec.gate_id,
        status=status,
        failed_conditions=tuple(failed_conditions),
        evaluated_condition_count=len(spec.conditions),
        capital_blocked=capital_blocked,
        risk_blocked=risk_blocked,
    )


def build_decision_record_v3(
    decision_id: str,
    gate_result: GateEvaluationV3,
    model_version: str,
    capital_version: str,
    risk_version: str,
    portfolio_id: str = "",
    approved_by: str = "",
    approved_at: str = "",
    notes: str = "",
) -> DecisionRecordV3:
    payload = {
        "decision_id": decision_id,
        "gate_id": gate_result.gate_id,
        "model_version": model_version,
        "capital_version": capital_version,
        "risk_version": risk_version,
        "status": gate_result.status,
        "failed_conditions": list(gate_result.failed_conditions),
        "portfolio_id": portfolio_id,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "notes": notes,
    }
    signature = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return DecisionRecordV3(
        decision_id=decision_id,
        gate_id=gate_result.gate_id,
        model_version=model_version,
        capital_version=capital_version,
        risk_version=risk_version,
        status=gate_result.status,
        failed_conditions=gate_result.failed_conditions,
        portfolio_id=portfolio_id,
        approved_by=approved_by,
        approved_at=approved_at,
        notes=notes,
        hash_signature=signature,
    )


def serialize_decision_record_v3(record: DecisionRecordV3) -> dict[str, Any]:
    return asdict(record)
