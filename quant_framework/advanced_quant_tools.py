from __future__ import annotations

from statistics import mean

from .stats_utils import clip, safe_divide
from .time_series_metrics import shannon_entropy


def fibonacci_retracement_levels(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    high = max(values)
    low = min(values)
    span = max(high - low, 1e-9)
    latest = values[-1]
    return {
        "high": round(high, 4),
        "low": round(low, 4),
        "level_236": round(high - span * 0.236, 4),
        "level_382": round(high - span * 0.382, 4),
        "level_500": round(high - span * 0.5, 4),
        "level_618": round(high - span * 0.618, 4),
        "level_786": round(high - span * 0.786, 4),
        "latest_position_ratio": round(safe_divide(latest - low, span, default=0.0), 4),
    }


def recursive_ewma(values: list[float], alpha: float = 0.35) -> dict[str, object]:
    if not values:
        return {"alpha": alpha, "series": [], "stability_score": 0.0, "trend_score": 0.0}
    recursive_series: list[float] = [float(values[0])]
    for value in values[1:]:
        recursive_series.append(alpha * float(value) + (1 - alpha) * recursive_series[-1])
    absolute_shifts = [abs(curr - prev) for prev, curr in zip(recursive_series, recursive_series[1:])]
    normalized_shift = safe_divide(mean(absolute_shifts), max(mean(values), 1e-9), default=0.0) if absolute_shifts else 0.0
    trend_score = safe_divide(recursive_series[-1] - recursive_series[0], max(abs(recursive_series[0]), 1.0), default=0.0)
    return {
        "alpha": alpha,
        "series": [round(value, 4) for value in recursive_series],
        "stability_score": round(clip(1 - normalized_shift, 0.0, 1.0), 4),
        "trend_score": round(clip((trend_score + 1) / 2, 0.0, 1.0), 4),
    }


def bayesian_shrinkage_mean(
    observed_mean: float,
    *,
    prior_mean: float,
    prior_strength: float,
    sample_size: float,
) -> float:
    posterior = safe_divide(
        prior_mean * prior_strength + observed_mean * sample_size,
        prior_strength + sample_size,
        default=prior_mean,
    )
    return round(posterior, 4)


def entropy_growth_profile(values: list[float]) -> dict[str, float]:
    if len(values) < 4:
        entropy = shannon_entropy(values) if values else 0.0
        return {
            "base_entropy": round(entropy, 4),
            "recent_entropy": round(entropy, 4),
            "entropy_delta": 0.0,
            "entropy_growth_score": round(clip(1 - entropy, 0.0, 1.0), 4),
        }
    midpoint = max(len(values) // 2, 1)
    early = values[:midpoint]
    late = values[midpoint:]
    base_entropy = shannon_entropy(early)
    recent_entropy = shannon_entropy(late)
    entropy_delta = recent_entropy - base_entropy
    entropy_growth_score = clip(1 - max(entropy_delta, 0.0), 0.0, 1.0)
    return {
        "base_entropy": round(base_entropy, 4),
        "recent_entropy": round(recent_entropy, 4),
        "entropy_delta": round(entropy_delta, 4),
        "entropy_growth_score": round(entropy_growth_score, 4),
    }

