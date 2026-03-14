from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GateConditionSpec:
    source: str
    ref: str
    operator: str
    value: Any | None = None
    budget_ref: str = ""


@dataclass(frozen=True)
class GateDecisionOutput:
    on_pass: str = "GO"
    on_fail: str = "NO_GO"


@dataclass(frozen=True)
class GateSpecV2:
    gate_id: str
    schema_version: str
    logic: str = "AND"
    conditions: tuple[GateConditionSpec, ...] = field(default_factory=tuple)
    decision_output: GateDecisionOutput = GateDecisionOutput()


@dataclass(frozen=True)
class CapitalPoolState:
    capital_id: str
    schema_version: str
    total_capital: float
    allocated_capital: float
    free_capital: float
    cost_of_capital: float


@dataclass(frozen=True)
class RiskBudgetState:
    risk_id: str
    schema_version: str
    max_loss_probability: float
    max_drawdown: float
    max_inventory_exposure: float
    max_channel_dependency: float


@dataclass(frozen=True)
class OpportunitySpec:
    opportunity_id: str
    channel: str
    required_capital: float
    expected_return: float
    expected_loss_probability: float
    expected_drawdown: float
    priority_score: float = 0.0


@dataclass(frozen=True)
class PortfolioAllocationRow:
    opportunity_id: str
    channel: str
    allocated_capital: float
    expected_return: float
    objective_score: float
    accepted: bool
    reject_reason: str = ""


@dataclass(frozen=True)
class GateEvaluationResultV2:
    gate_id: str
    status: str
    failed_conditions: tuple[str, ...]
    evaluated_condition_count: int


@dataclass(frozen=True)
class DecisionRecordV2:
    decision_id: str
    gate_id: str
    model_version: str
    capital_version: str
    risk_version: str
    status: str
    failed_conditions: tuple[str, ...]
    approved_by: str = ""
    approved_at: str = ""
    hash_signature: str = ""


@dataclass(frozen=True)
class FeedbackRecordV2:
    decision_id: str
    predicted_profit: float
    actual_profit: float
    predicted_loss_probability: float
    actual_loss_probability: float
    model_prediction_error: float
    recalibration_required: bool
