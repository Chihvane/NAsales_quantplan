from __future__ import annotations

from math import sqrt
from statistics import mean, pstdev

from .stats_utils import percentile, safe_divide


def value_at_risk(
    values: list[float],
    confidence_level: float = 0.95,
    *,
    lower_tail: bool = True,
) -> float:
    if not values:
        return 0.0
    percentile_value = (1 - confidence_level) * 100 if lower_tail else confidence_level * 100
    return float(percentile(values, percentile_value))


def expected_shortfall(
    values: list[float],
    confidence_level: float = 0.95,
    *,
    lower_tail: bool = True,
) -> float:
    if not values:
        return 0.0
    cutoff = value_at_risk(values, confidence_level, lower_tail=lower_tail)
    if lower_tail:
        tail = [value for value in values if value <= cutoff]
    else:
        tail = [value for value in values if value >= cutoff]
    return float(mean(tail)) if tail else cutoff


def downside_deviation(values: list[float], threshold: float = 0.0) -> float:
    if not values:
        return 0.0
    downside = [(min(value - threshold, 0.0)) ** 2 for value in values]
    return sqrt(mean(downside)) if downside else 0.0


def sharpe_like(values: list[float], hurdle_rate: float = 0.0) -> float:
    if not values:
        return 0.0
    excess_values = [value - hurdle_rate for value in values]
    volatility = pstdev(excess_values) if len(excess_values) > 1 else 0.0
    return safe_divide(mean(excess_values), volatility, default=0.0)


def sortino_like(values: list[float], hurdle_rate: float = 0.0) -> float:
    if not values:
        return 0.0
    return safe_divide(
        mean(values) - hurdle_rate,
        downside_deviation(values, threshold=hurdle_rate),
        default=0.0,
    )


def tail_ratio(values: list[float], upper_percentile: float = 95.0, lower_percentile: float = 5.0) -> float:
    if not values:
        return 0.0
    upper = percentile(values, upper_percentile)
    lower = abs(percentile(values, lower_percentile))
    return safe_divide(upper, lower, default=0.0)


def max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    running_peak = values[0]
    worst_drawdown = 0.0
    for value in values:
        running_peak = max(running_peak, value)
        drawdown = value - running_peak
        worst_drawdown = min(worst_drawdown, drawdown)
    return float(worst_drawdown)


def drawdown_duration(values: list[float]) -> int:
    if not values:
        return 0
    running_peak = values[0]
    current_duration = 0
    max_duration = 0
    for value in values:
        if value >= running_peak:
            running_peak = value
            current_duration = 0
            continue
        current_duration += 1
        max_duration = max(max_duration, current_duration)
    return max_duration


def ulcer_index(values: list[float]) -> float:
    if not values:
        return 0.0
    running_peak = values[0]
    squared_drawdowns = []
    for value in values:
        running_peak = max(running_peak, value)
        drawdown_ratio = safe_divide(value - running_peak, abs(running_peak), default=0.0)
        squared_drawdowns.append(drawdown_ratio**2)
    return sqrt(mean(squared_drawdowns)) if squared_drawdowns else 0.0


def calmar_like(values: list[float]) -> float:
    if not values:
        return 0.0
    denominator = abs(max_drawdown(values))
    return safe_divide(mean(values), denominator, default=0.0)


def omega_ratio(values: list[float], threshold: float = 0.0) -> float:
    if not values:
        return 0.0
    gains = sum(max(value - threshold, 0.0) for value in values)
    losses = sum(max(threshold - value, 0.0) for value in values)
    return safe_divide(gains, losses, default=0.0)


def tail_shortfall_severity(values: list[float], threshold: float = 0.0) -> float:
    if not values:
        return 0.0
    shortfalls = [threshold - value for value in values if value < threshold]
    return float(mean(shortfalls)) if shortfalls else 0.0
