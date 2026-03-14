from __future__ import annotations

from .models import FeedbackRecordV3


def evaluate_feedback_v3(
    decision_id: str,
    portfolio_id: str,
    predicted_profit: float,
    actual_profit: float,
    predicted_loss_probability: float,
    actual_loss_probability: float,
    predicted_drawdown: float,
    actual_drawdown: float,
    profit_error_tolerance: float = 0.2,
    probability_tolerance: float = 0.05,
    drawdown_tolerance: float = 0.05,
) -> FeedbackRecordV3:
    prediction_error = actual_profit - predicted_profit
    profit_error_ratio = abs(prediction_error) / max(abs(predicted_profit), 1.0)
    loss_probability_gap = abs(actual_loss_probability - predicted_loss_probability)
    drawdown_gap = abs(actual_drawdown - predicted_drawdown)
    recalibration_required = (
        profit_error_ratio > profit_error_tolerance
        or loss_probability_gap > probability_tolerance
        or drawdown_gap > drawdown_tolerance
    )
    return FeedbackRecordV3(
        decision_id=decision_id,
        portfolio_id=portfolio_id,
        predicted_profit=predicted_profit,
        actual_profit=actual_profit,
        predicted_loss_probability=predicted_loss_probability,
        actual_loss_probability=actual_loss_probability,
        predicted_drawdown=predicted_drawdown,
        actual_drawdown=actual_drawdown,
        model_prediction_error=round(prediction_error, 4),
        loss_probability_gap=round(loss_probability_gap, 4),
        drawdown_gap=round(drawdown_gap, 4),
        recalibration_required=recalibration_required,
    )
