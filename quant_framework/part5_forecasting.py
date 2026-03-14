from __future__ import annotations

from collections import defaultdict
from statistics import mean

from .models import KPIDailySnapshotRecord
from .stats_utils import safe_divide


def _moving_average(series: dict[str, float], window: int) -> dict[str, float]:
    labels = list(series.keys())
    values = list(series.values())
    result = {}
    for index, label in enumerate(labels):
        start = max(0, index - window + 1)
        result[label] = round(mean(values[start : index + 1]), 2)
    return result


def summarize_kpi_trend(kpi_daily_snapshots: list[KPIDailySnapshotRecord]) -> dict:
    if not kpi_daily_snapshots:
        return {}

    revenue_by_day: dict[str, float] = defaultdict(float)
    profit_by_day: dict[str, float] = defaultdict(float)
    for record in kpi_daily_snapshots:
        revenue_by_day[record.date] += record.revenue
        profit_by_day[record.date] += record.contribution_profit

    ordered_dates = sorted(revenue_by_day)
    revenue_series = {day: round(revenue_by_day[day], 2) for day in ordered_dates}
    profit_series = {day: round(profit_by_day[day], 2) for day in ordered_dates}
    first_revenue = revenue_series[ordered_dates[0]]
    last_revenue = revenue_series[ordered_dates[-1]]
    slope = safe_divide(last_revenue - first_revenue, max(len(ordered_dates) - 1, 1))
    if slope > 0:
        direction = "up"
    elif slope < 0:
        direction = "down"
    else:
        direction = "flat"

    trailing_revenue = list(revenue_series.values())[-7:]
    trailing_profit = list(profit_series.values())[-7:]
    return {
        "daily_revenue": revenue_series,
        "daily_contribution_profit": profit_series,
        "revenue_ma_7d": _moving_average(revenue_series, 7),
        "profit_ma_7d": _moving_average(profit_series, 7),
        "trend_direction": direction,
        "average_daily_revenue_7d": round(mean(trailing_revenue), 2) if trailing_revenue else 0.0,
        "average_daily_profit_7d": round(mean(trailing_profit), 2) if trailing_profit else 0.0,
        "forecast_next_7d_revenue": round(sum(trailing_revenue), 2) if trailing_revenue else 0.0,
        "forecast_next_7d_profit": round(sum(trailing_profit), 2) if trailing_profit else 0.0,
    }
