from __future__ import annotations


def feedback_error(actual: float, predicted: float) -> float:
    return round(actual - predicted, 4)
