from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any, Mapping

from .models import (
    DecisionRecordV2,
    GateConditionSpec,
    GateDecisionOutput,
    GateEvaluationResultV2,
    GateSpecV2,
)


def _compare(value: Any, operator: str, threshold: Any) -> bool:
    if operator == ">=":
        return value >= threshold
    if operator == "<=":
        return value <= threshold
    if operator == ">":
        return value > threshold
    if operator == "<":
        return value < threshold
    if operator == "==":
        return value == threshold
    if operator == "!=":
        return value != threshold
    raise ValueError(f"Unsupported operator: {operator}")


def _resolve_budget_ref(
    budget_ref: str,
    factor_scores: Mapping[str, Any],
    model_outputs: Mapping[str, Any],
    capital_state: Mapping[str, Any],
    risk_state: Mapping[str, Any],
) -> Any:
    namespace, _, ref = budget_ref.partition(".")
    if namespace == "factor":
        return factor_scores.get(ref)
    if namespace == "model_output":
        return model_outputs.get(ref)
    if namespace == "capital_pool":
        return capital_state.get(ref)
    if namespace == "risk_budget":
        return risk_state.get(ref)
    return None


def _condition_value(
    condition: GateConditionSpec,
    factor_scores: Mapping[str, Any],
    model_outputs: Mapping[str, Any],
    capital_state: Mapping[str, Any],
    risk_state: Mapping[str, Any],
) -> Any:
    if condition.source == "factor":
        return factor_scores.get(condition.ref)
    if condition.source == "capital":
        return capital_state.get(condition.ref)
    if condition.source == "risk":
        return risk_state.get(condition.ref)
    return model_outputs.get(condition.ref)


def build_gate_spec(payload: Mapping[str, Any]) -> GateSpecV2:
    body = payload.get("gate_schema", payload)
    conditions = tuple(
        GateConditionSpec(
            source=str(item.get("source", "model_output")),
            ref=str(item.get("ref", "")),
            operator=str(item.get("operator", "==")),
            value=item.get("value"),
            budget_ref=str(item.get("budget_ref", "")),
        )
        for item in body.get("conditions", [])
        if isinstance(item, Mapping)
    )
    decision_output_payload = body.get("decision_output", {})
    return GateSpecV2(
        gate_id=str(body.get("gate_id", "")),
        schema_version=str(body.get("schema_version", "")),
        logic=str(body.get("logic", "AND")).upper(),
        conditions=conditions,
        decision_output=GateDecisionOutput(
            on_pass=str(decision_output_payload.get("on_pass", "GO")),
            on_fail=str(decision_output_payload.get("on_fail", "NO_GO")),
        ),
    )


class GateEngineV2:
    def evaluate(
        self,
        gate_spec: GateSpecV2 | Mapping[str, Any],
        model_outputs: Mapping[str, Any],
        factor_scores: Mapping[str, Any] | None = None,
        capital_state: Mapping[str, Any] | None = None,
        risk_state: Mapping[str, Any] | None = None,
    ) -> GateEvaluationResultV2:
        spec = gate_spec if isinstance(gate_spec, GateSpecV2) else build_gate_spec(gate_spec)
        factor_scores = factor_scores or {}
        capital_state = capital_state or {}
        risk_state = risk_state or {}

        failed_conditions: list[str] = []
        passed_conditions = 0

        for condition in spec.conditions:
            current_value = _condition_value(condition, factor_scores, model_outputs, capital_state, risk_state)
            threshold = (
                _resolve_budget_ref(condition.budget_ref, factor_scores, model_outputs, capital_state, risk_state)
                if condition.budget_ref
                else condition.value
            )
            if current_value is None or threshold is None or not _compare(current_value, condition.operator, threshold):
                failed_conditions.append(f"{condition.source}:{condition.ref}")
            else:
                passed_conditions += 1

        if spec.logic == "AND":
            status = spec.decision_output.on_pass if not failed_conditions else spec.decision_output.on_fail
        elif spec.logic == "OR":
            status = spec.decision_output.on_pass if passed_conditions > 0 else spec.decision_output.on_fail
        else:
            raise ValueError(f"Unsupported gate logic: {spec.logic}")

        return GateEvaluationResultV2(
            gate_id=spec.gate_id,
            status=status,
            failed_conditions=tuple(failed_conditions),
            evaluated_condition_count=len(spec.conditions),
        )


def evaluate_gate_v2(
    gate_spec: GateSpecV2 | Mapping[str, Any],
    model_outputs: Mapping[str, Any],
    factor_scores: Mapping[str, Any] | None = None,
    capital_state: Mapping[str, Any] | None = None,
    risk_state: Mapping[str, Any] | None = None,
) -> GateEvaluationResultV2:
    return GateEngineV2().evaluate(gate_spec, model_outputs, factor_scores, capital_state, risk_state)


def build_decision_record(
    decision_id: str,
    gate_result: GateEvaluationResultV2,
    model_version: str,
    capital_version: str,
    risk_version: str,
    approved_by: str = "",
    approved_at: str = "",
) -> DecisionRecordV2:
    payload = {
        "decision_id": decision_id,
        "gate_id": gate_result.gate_id,
        "model_version": model_version,
        "capital_version": capital_version,
        "risk_version": risk_version,
        "status": gate_result.status,
        "failed_conditions": list(gate_result.failed_conditions),
        "approved_by": approved_by,
        "approved_at": approved_at,
    }
    signature = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return DecisionRecordV2(
        decision_id=decision_id,
        gate_id=gate_result.gate_id,
        model_version=model_version,
        capital_version=capital_version,
        risk_version=risk_version,
        status=gate_result.status,
        failed_conditions=gate_result.failed_conditions,
        approved_by=approved_by,
        approved_at=approved_at,
        hash_signature=signature,
    )


def serialize_decision_record(record: DecisionRecordV2) -> dict[str, Any]:
    return asdict(record)
