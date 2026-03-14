from __future__ import annotations

from .models import FeedbackRecordV2


def evaluate_feedback_record(
    decision_id: str,
    predicted_profit: float,
    actual_profit: float,
    predicted_loss_probability: float,
    actual_loss_probability: float,
    profit_error_tolerance: float = 0.2,
    loss_probability_tolerance: float = 0.05,
) -> FeedbackRecordV2:
    prediction_error = actual_profit - predicted_profit
    profit_error_ratio = abs(prediction_error) / max(abs(predicted_profit), 1.0)
    loss_probability_gap = abs(actual_loss_probability - predicted_loss_probability)
    recalibration_required = (
        profit_error_ratio > profit_error_tolerance
        or loss_probability_gap > loss_probability_tolerance
    )
    return FeedbackRecordV2(
        decision_id=decision_id,
        predicted_profit=predicted_profit,
        actual_profit=actual_profit,
        predicted_loss_probability=predicted_loss_probability,
        actual_loss_probability=actual_loss_probability,
        model_prediction_error=round(prediction_error, 4),
        recalibration_required=recalibration_required,
    )
