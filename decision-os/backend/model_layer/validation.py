from __future__ import annotations


def within_tolerance(actual: float, expected: float, tolerance: float = 0.2) -> bool:
    return abs(actual - expected) / max(abs(expected), 1.0) <= tolerance
