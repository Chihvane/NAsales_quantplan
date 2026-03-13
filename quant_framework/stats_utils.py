from __future__ import annotations

from statistics import mean


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if not denominator:
        return default
    return numerator / denominator


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (percentile_value / 100)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]
    return lower_value + (upper_value - lower_value) * fraction


def percentile_band(values: list[float], digits: int = 4) -> dict[str, float]:
    if not values:
        return {"p10": 0.0, "p50": 0.0, "p90": 0.0}
    return {
        "p10": round(percentile(values, 10), digits),
        "p50": round(percentile(values, 50), digits),
        "p90": round(percentile(values, 90), digits),
    }


def score_level(
    score: float,
    high_threshold: float = 0.75,
    medium_threshold: float = 0.5,
) -> str:
    if score >= high_threshold:
        return "high"
    if score >= medium_threshold:
        return "medium"
    return "low"


def normalize_reverse_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 1.0
    return 1 - ((value - min_value) / (max_value - min_value))


def mean_or_zero(values: list[float]) -> float:
    return mean(values) if values else 0.0


def clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def round_mapping(values: dict[str, float], digits: int = 4) -> dict[str, float]:
    return {key: round(value, digits) for key, value in values.items()}
