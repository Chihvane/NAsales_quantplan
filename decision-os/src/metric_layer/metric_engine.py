from __future__ import annotations


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
