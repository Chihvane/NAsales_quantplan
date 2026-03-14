from __future__ import annotations

from .capital_risk import CapitalState, RiskBudget


class GateEngine:
    def evaluate(
        self,
        factor_score: float,
        model_outputs: dict[str, float],
        capital_state: CapitalState,
        risk_budget: RiskBudget,
        required_capital: float,
    ) -> str:
        if model_outputs["profit_p50"] < 0:
            return "NO-GO: Expected profit negative"

        if model_outputs["loss_probability"] > risk_budget.max_loss_probability:
            return "NO-GO: Risk too high"

        if factor_score < 0.5:
            return "NO-GO: Market attractiveness too low"

        if required_capital > capital_state.free:
            return "NO-GO: Not enough capital"

        return "GO"
