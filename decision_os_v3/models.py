from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GateConditionV3:
    source: str
    ref: str
    operator: str
    value: Any | None = None
    budget_ref: str = ""


@dataclass(frozen=True)
class GateDecisionOutputV3:
    on_pass: str = "GO"
    on_fail: str = "NO_GO"


@dataclass(frozen=True)
class GateSpecV3:
    gate_id: str
    schema_version: str
    logic: str = "AND"
    conditions: tuple[GateConditionV3, ...] = field(default_factory=tuple)
    decision_output: GateDecisionOutputV3 = GateDecisionOutputV3()


@dataclass(frozen=True)
class CapitalPoolStateV3:
    capital_pool_id: str
    schema_version: str
    total_capital: float
    allocated_capital: float
    free_capital: float
    cost_of_capital: float


@dataclass(frozen=True)
class RiskBudgetStateV3:
    risk_budget_id: str
    schema_version: str
    max_loss_probability: float
    max_drawdown: float
    max_inventory_exposure: float
    max_channel_dependency: float


@dataclass(frozen=True)
class PortfolioOpportunityV3:
    opportunity_id: str
    portfolio_id: str
    channel: str
    required_capital: float
    expected_return: float
    expected_loss_probability: float
    expected_drawdown: float
    channel_dependency: float
    priority_score: float = 0.0


@dataclass(frozen=True)
class GateEvaluationV3:
    gate_id: str
    status: str
    failed_conditions: tuple[str, ...]
    evaluated_condition_count: int
    capital_blocked: bool = False
    risk_blocked: bool = False


@dataclass(frozen=True)
class DecisionRecordV3:
    decision_id: str
    gate_id: str
    model_version: str
    capital_version: str
    risk_version: str
    status: str
    failed_conditions: tuple[str, ...]
    portfolio_id: str = ""
    approved_by: str = ""
    approved_at: str = ""
    notes: str = ""
    hash_signature: str = ""


@dataclass(frozen=True)
class PortfolioAllocationV3:
    portfolio_id: str
    opportunity_id: str
    channel: str
    allocated_capital: float
    expected_return: float
    expected_drawdown: float
    objective_score: float
    accepted: bool
    reject_reason: str = ""


@dataclass(frozen=True)
class FeedbackRecordV3:
    decision_id: str
    portfolio_id: str
    predicted_profit: float
    actual_profit: float
    predicted_loss_probability: float
    actual_loss_probability: float
    predicted_drawdown: float
    actual_drawdown: float
    model_prediction_error: float
    loss_probability_gap: float
    drawdown_gap: float
    recalibration_required: bool

