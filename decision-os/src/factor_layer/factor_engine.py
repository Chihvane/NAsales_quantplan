from __future__ import annotations

from factor_layer.normalization import bounded_score


def weighted_factor(components: list[tuple[float, float]]) -> float:
    total = sum(value * weight for value, weight in components)
    return bounded_score(total)
