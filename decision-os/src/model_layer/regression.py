from __future__ import annotations


def regression_stub(features: list[float]) -> float:
    return sum(features) / len(features) if features else 0.0
