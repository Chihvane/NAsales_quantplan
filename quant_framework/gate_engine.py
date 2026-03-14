from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Any, Mapping


def _optional_yaml_load(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised indirectly
        raise RuntimeError(
            "Loading .yaml files requires PyYAML. Install `PyYAML` or pass a Python dict instead."
        ) from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Gate config at {path} must load as a mapping.")
    return payload


@dataclass(frozen=True)
class GateCondition:
    source: str
    ref: str
    operator: str
    value: Any

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GateCondition":
        return cls(
            source=str(payload.get("source", "metric")),
            ref=str(payload.get("ref", "")),
            operator=str(payload.get("operator", "==")),
            value=payload.get("value"),
        )


@dataclass(frozen=True)
class GateConstraint:
    lhs: str
    operator: str
    rhs: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "GateConstraint | None":
        if not payload:
            return None
        return cls(
            lhs=str(payload.get("lhs", "")),
            operator=str(payload.get("operator", "==")),
            rhs=str(payload.get("rhs", "")),
        )


@dataclass(frozen=True)
class GateConfig:
    gate_id: str
    schema_version: str
    logic: str = "AND"
    trigger_conditions: tuple[GateCondition, ...] = field(default_factory=tuple)
    capital_constraint: GateConstraint | None = None
    risk_budget: GateConstraint | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "GateConfig":
        body = payload.get("gate_schema", payload)
        trigger = body.get("trigger", {})
        conditions = tuple(
            GateCondition.from_mapping(item)
            for item in trigger.get("conditions", [])
            if isinstance(item, Mapping)
        )
        return cls(
            gate_id=str(body.get("gate_id", "")),
            schema_version=str(body.get("schema_version", "")),
            logic=str(body.get("logic", "AND")).upper(),
            trigger_conditions=conditions,
            capital_constraint=GateConstraint.from_mapping(body.get("capital_constraint")),
            risk_budget=GateConstraint.from_mapping(body.get("risk_budget")),
        )


@dataclass(frozen=True)
class GateEvaluationResult:
    gate_id: str
    status: str
    failed_conditions: tuple[str, ...]
    capital_check: str
    risk_check: str
    evaluated_condition_count: int


def compare(value: Any, operator: str, threshold: Any) -> bool:
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
    raise ValueError(f"Unknown operator: {operator}")


def load_gate_config(path_or_payload: str | Path | Mapping[str, Any]) -> GateConfig:
    if isinstance(path_or_payload, Mapping):
        return GateConfig.from_mapping(path_or_payload)
    path = Path(path_or_payload)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".yaml", ".yml"}:
        payload = _optional_yaml_load(path)
    else:
        raise ValueError(f"Unsupported gate config suffix: {path.suffix}")
    return GateConfig.from_mapping(payload)


def _resolve_source_value(
    source: str,
    ref: str,
    model_outputs: Mapping[str, Any],
    factor_outputs: Mapping[str, Any],
) -> Any:
    if source == "factor":
        return factor_outputs.get(ref)
    return model_outputs.get(ref)


def _evaluate_constraint(
    constraint: GateConstraint | None,
    state: Mapping[str, Any],
) -> tuple[str, str]:
    if constraint is None:
        return "not_applicable", ""
    lhs_value = state.get(constraint.lhs)
    rhs_value = state.get(constraint.rhs)
    if lhs_value is None or rhs_value is None:
        return "review", f"{constraint.lhs}:{lhs_value}|{constraint.rhs}:{rhs_value}"
    return (
        "pass" if compare(lhs_value, constraint.operator, rhs_value) else "fail",
        f"{constraint.lhs}:{lhs_value} {constraint.operator} {constraint.rhs}:{rhs_value}",
    )


def evaluate_gate(
    gate_config: GateConfig | Mapping[str, Any] | str | Path,
    model_outputs: Mapping[str, Any],
    factor_outputs: Mapping[str, Any] | None = None,
    capital_state: Mapping[str, Any] | None = None,
    risk_state: Mapping[str, Any] | None = None,
) -> GateEvaluationResult:
    config = gate_config if isinstance(gate_config, GateConfig) else load_gate_config(gate_config)
    factor_outputs = factor_outputs or {}
    capital_state = capital_state or {}
    risk_state = risk_state or {}

    failed_conditions: list[str] = []
    passed_count = 0
    for condition in config.trigger_conditions:
        value = _resolve_source_value(condition.source, condition.ref, model_outputs, factor_outputs)
        if value is None or not compare(value, condition.operator, condition.value):
            failed_conditions.append(f"{condition.source}:{condition.ref}")
        else:
            passed_count += 1

    if config.logic == "AND":
        trigger_status = "pass" if not failed_conditions else "fail"
    elif config.logic == "OR":
        trigger_status = "pass" if passed_count > 0 else "fail"
    else:
        raise ValueError(f"Unsupported gate logic: {config.logic}")

    capital_check, _ = _evaluate_constraint(config.capital_constraint, capital_state)
    risk_check, _ = _evaluate_constraint(config.risk_budget, risk_state)

    if trigger_status == "fail":
        status = "NO_GO"
    elif capital_check == "fail":
        status = "NO_GO_CAPITAL"
    elif risk_check == "fail":
        status = "NO_GO_RISK"
    elif capital_check == "review" or risk_check == "review":
        status = "REVIEW"
    else:
        status = "GO"

    return GateEvaluationResult(
        gate_id=config.gate_id,
        status=status,
        failed_conditions=tuple(failed_conditions),
        capital_check=capital_check,
        risk_check=risk_check,
        evaluated_condition_count=len(config.trigger_conditions),
    )
