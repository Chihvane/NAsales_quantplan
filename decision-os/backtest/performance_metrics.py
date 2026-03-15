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
    governance_rows = go_decisions or decisions
    average_forecast_backtest_score = _safe_divide(
        sum(float(row.get("forecast_backtest_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_signal_regime_score = _safe_divide(
        sum(float(row.get("signal_regime_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_signal_seasonality_confidence_score = _safe_divide(
        sum(float(row.get("signal_seasonality_confidence_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_signal_spectral_entropy = _safe_divide(
        sum(float(row.get("signal_spectral_entropy", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_signal_approximate_entropy = _safe_divide(
        sum(float(row.get("signal_approximate_entropy", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_forecast_mape = _safe_divide(
        sum(float(row.get("forecast_mape", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_drift_score = _safe_divide(
        sum(float(row.get("drift_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_drift_risk_score = _safe_divide(
        sum(float(row.get("drift_risk_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_calibration_brier_score = _safe_divide(
        sum(float(row.get("calibration_brier_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_governance_readiness_score = _safe_divide(
        sum(float(row.get("governance_readiness_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_localization_governance_score = _safe_divide(
        sum(float(row.get("localization_governance_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_control_tower_score = _safe_divide(
        sum(float(row.get("control_tower_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_master_data_health_score = _safe_divide(
        sum(float(row.get("master_data_health_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_audit_trace_score = _safe_divide(
        sum(float(row.get("audit_trace_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_decision_gate_control_score = _safe_divide(
        sum(float(row.get("decision_gate_control_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_threshold_alignment_ratio = _safe_divide(
        sum(float(row.get("threshold_alignment_ratio", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_gate_consistency_ratio = _safe_divide(
        sum(float(row.get("gate_consistency_ratio", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_tail_risk_score = _safe_divide(
        sum(float(row.get("supply_tail_risk_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_loss_probability = _safe_divide(
        sum(float(row.get("supply_loss_probability", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_margin_floor_breach_probability = _safe_divide(
        sum(float(row.get("supply_margin_floor_breach_probability", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_optimizer_feasible_ratio = _safe_divide(
        sum(float(row.get("supply_optimizer_feasible_ratio", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_execution_confidence_score = _safe_divide(
        sum(float(row.get("supply_execution_confidence_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_supply_optimizer_gate_pass = _safe_divide(
        sum(float(row.get("supply_optimizer_gate_pass", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_portfolio_readiness_score = _safe_divide(
        sum(float(row.get("channel_portfolio_readiness_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_portfolio_resilience_score = _safe_divide(
        sum(float(row.get("channel_portfolio_resilience_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_execution_friction_factor = _safe_divide(
        sum(float(row.get("channel_execution_friction_factor", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_scale_readiness_score = _safe_divide(
        sum(float(row.get("channel_scale_readiness_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_optimizer_feasible_ratio = _safe_divide(
        sum(float(row.get("channel_optimizer_feasible_ratio", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_optimizer_gate_pass = _safe_divide(
        sum(float(row.get("channel_optimizer_gate_pass", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_risk_adjusted_profit = _safe_divide(
        sum(float(row.get("channel_risk_adjusted_profit", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_stress_robustness_score = _safe_divide(
        sum(float(row.get("channel_stress_robustness_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_gate_flip_count = _safe_divide(
        sum(float(row.get("channel_gate_flip_count", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_loss_probability_weighted = _safe_divide(
        sum(float(row.get("channel_loss_probability_weighted", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_margin_rate_var_95 = _safe_divide(
        sum(float(row.get("channel_margin_rate_var_95", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_margin_rate_es_95 = _safe_divide(
        sum(float(row.get("channel_margin_rate_es_95", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_channel_tail_shortfall_severity = _safe_divide(
        sum(float(row.get("channel_tail_shortfall_severity", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_operating_system_readiness_score = _safe_divide(
        sum(float(row.get("operating_system_readiness_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_operating_health_score = _safe_divide(
        sum(float(row.get("operating_health_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_data_contract_score = _safe_divide(
        sum(float(row.get("data_contract_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_experiment_confidence_score = _safe_divide(
        sum(float(row.get("experiment_confidence_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_scale_control_score = _safe_divide(
        sum(float(row.get("scale_control_score", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
    average_operating_proxy_flag_count = _safe_divide(
        sum(float(row.get("operating_proxy_flag_count", 0.0)) for row in governance_rows),
        len(governance_rows),
    )
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
        "average_forecast_backtest_score": round(average_forecast_backtest_score, 6),
        "average_signal_regime_score": round(average_signal_regime_score, 6),
        "average_signal_seasonality_confidence_score": round(average_signal_seasonality_confidence_score, 6),
        "average_signal_spectral_entropy": round(average_signal_spectral_entropy, 6),
        "average_signal_approximate_entropy": round(average_signal_approximate_entropy, 6),
        "average_forecast_mape": round(average_forecast_mape, 6),
        "average_drift_score": round(average_drift_score, 6),
        "average_drift_risk_score": round(average_drift_risk_score, 6),
        "average_calibration_brier_score": round(average_calibration_brier_score, 6),
        "average_governance_readiness_score": round(average_governance_readiness_score, 6),
        "average_localization_governance_score": round(average_localization_governance_score, 6),
        "average_control_tower_score": round(average_control_tower_score, 6),
        "average_master_data_health_score": round(average_master_data_health_score, 6),
        "average_audit_trace_score": round(average_audit_trace_score, 6),
        "average_decision_gate_control_score": round(average_decision_gate_control_score, 6),
        "average_threshold_alignment_ratio": round(average_threshold_alignment_ratio, 6),
        "average_gate_consistency_ratio": round(average_gate_consistency_ratio, 6),
        "average_supply_tail_risk_score": round(average_supply_tail_risk_score, 6),
        "average_supply_loss_probability": round(average_supply_loss_probability, 6),
        "average_supply_margin_floor_breach_probability": round(average_supply_margin_floor_breach_probability, 6),
        "average_supply_optimizer_feasible_ratio": round(average_supply_optimizer_feasible_ratio, 6),
        "average_supply_execution_confidence_score": round(average_supply_execution_confidence_score, 6),
        "average_supply_optimizer_gate_pass": round(average_supply_optimizer_gate_pass, 6),
        "average_channel_portfolio_readiness_score": round(average_channel_portfolio_readiness_score, 6),
        "average_channel_portfolio_resilience_score": round(average_channel_portfolio_resilience_score, 6),
        "average_channel_execution_friction_factor": round(average_channel_execution_friction_factor, 6),
        "average_channel_scale_readiness_score": round(average_channel_scale_readiness_score, 6),
        "average_channel_optimizer_feasible_ratio": round(average_channel_optimizer_feasible_ratio, 6),
        "average_channel_optimizer_gate_pass": round(average_channel_optimizer_gate_pass, 6),
        "average_channel_risk_adjusted_profit": round(average_channel_risk_adjusted_profit, 6),
        "average_channel_stress_robustness_score": round(average_channel_stress_robustness_score, 6),
        "average_channel_gate_flip_count": round(average_channel_gate_flip_count, 6),
        "average_channel_loss_probability_weighted": round(average_channel_loss_probability_weighted, 6),
        "average_channel_margin_rate_var_95": round(average_channel_margin_rate_var_95, 6),
        "average_channel_margin_rate_es_95": round(average_channel_margin_rate_es_95, 6),
        "average_channel_tail_shortfall_severity": round(average_channel_tail_shortfall_severity, 6),
        "average_operating_system_readiness_score": round(average_operating_system_readiness_score, 6),
        "average_operating_health_score": round(average_operating_health_score, 6),
        "average_data_contract_score": round(average_data_contract_score, 6),
        "average_experiment_confidence_score": round(average_experiment_confidence_score, 6),
        "average_scale_control_score": round(average_scale_control_score, 6),
        "average_operating_proxy_flag_count": round(average_operating_proxy_flag_count, 6),
        "average_positions_per_period": round(average_positions_per_period, 6),
        "average_deployed_capital_ratio": round(average_deployed_capital_ratio, 6),
        "strategy_curve": strategy_curve,
        "benchmark_curve": benchmark_curve,
        "strategy_drawdown_curve": strategy_drawdown_curve,
        "benchmark_drawdown_curve": benchmark_drawdown_curve,
    }
