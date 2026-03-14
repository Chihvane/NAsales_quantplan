from __future__ import annotations


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _build_cumulative_curve(period_returns: list[float]) -> list[float]:
    curve: list[float] = []
    value = 1.0
    for period_return in period_returns:
        value *= 1 + period_return
        curve.append(round(value, 6))
    return curve


def _build_drawdown_curve(curve: list[float]) -> list[float]:
    peak = 1.0
    drawdowns: list[float] = []
    for value in curve:
        peak = max(peak, value)
        drawdowns.append(round((value / peak) - 1, 6))
    return drawdowns


def _max_drawdown(curve: list[float]) -> float:
    drawdowns = _build_drawdown_curve(curve)
    return round(min(drawdowns) if drawdowns else 0.0, 6)


def calculate_performance_summary(period_records: list[dict[str, float | str]], decisions: list[dict[str, float | str]]) -> dict[str, float | int | list[float]]:
    strategy_returns = [float(record["strategy_return"]) for record in period_records]
    benchmark_returns = [float(record["benchmark_return"]) for record in period_records]
    strategy_curve = _build_cumulative_curve(strategy_returns)
    benchmark_curve = _build_cumulative_curve(benchmark_returns)
    strategy_drawdown_curve = _build_drawdown_curve(strategy_curve)
    benchmark_drawdown_curve = _build_drawdown_curve(benchmark_curve)

    go_decisions = [row for row in decisions if row["decision"] == "GO"]
    reject_decisions = [row for row in decisions if row["decision"] != "GO"]
    hit_rate = sum(1 for row in go_decisions if float(row["forward_return_rate"]) > 0) / len(go_decisions) if go_decisions else 0.0
    reject_precision = (
        sum(1 for row in reject_decisions if float(row["forward_return_rate"]) <= 0) / len(reject_decisions)
        if reject_decisions
        else 0.0
    )
    go_ratio = _safe_divide(len(go_decisions), len(decisions))
    average_positions_per_period = _safe_divide(
        sum(float(record.get("positions_taken", 0.0)) for record in period_records),
        len(period_records),
    )
    average_deployed_capital_ratio = _safe_divide(
        sum(
            _safe_divide(
                float(record.get("deployed_capital", 0.0)),
                float(record.get("starting_capital", 0.0)),
            )
            for record in period_records
        ),
        len(period_records),
    )

    return {
        "periods": len(period_records),
        "decision_count": len(decisions),
        "go_count": len(go_decisions),
        "reject_count": len(reject_decisions),
        "go_ratio": round(go_ratio, 6),
        "strategy_cumulative_return": round(strategy_curve[-1] - 1 if strategy_curve else 0.0, 6),
        "benchmark_cumulative_return": round(benchmark_curve[-1] - 1 if benchmark_curve else 0.0, 6),
        "alpha": round((strategy_curve[-1] - benchmark_curve[-1]) if strategy_curve and benchmark_curve else 0.0, 6),
        "strategy_max_drawdown": _max_drawdown(strategy_curve),
        "benchmark_max_drawdown": _max_drawdown(benchmark_curve),
        "decision_hit_rate": round(hit_rate, 6),
        "rejection_precision": round(reject_precision, 6),
        "average_positions_per_period": round(average_positions_per_period, 6),
        "average_deployed_capital_ratio": round(average_deployed_capital_ratio, 6),
        "strategy_curve": strategy_curve,
        "benchmark_curve": benchmark_curve,
        "strategy_drawdown_curve": strategy_drawdown_curve,
        "benchmark_drawdown_curve": benchmark_drawdown_curve,
    }
