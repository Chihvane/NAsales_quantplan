from __future__ import annotations

from collections import defaultdict

from backtest.capital_tracker import CapitalTracker
from backtest.performance_metrics import calculate_performance_summary
from backtest.state_reconstructor import reconstruct_state
from backend.factor_layer.factor_engine import compute_market_factor
from backend.gate_engine.gate_engine import evaluate_market_gate
from backend.model_layer.monte_carlo import run_profit_simulation


def _group_dates(panel_rows: list[dict[str, str | float]]) -> list[str]:
    return sorted({str(row["as_of_date"]) for row in panel_rows})


def run_walk_forward_backtest(
    panel_rows: list[dict[str, str | float]],
    *,
    initial_capital: float = 1_000_000,
    max_loss_probability: float = 0.30,
    max_drawdown: float = 0.20,
    simulations: int = 1200,
    seed: int = 42,
    gate_params: dict[str, float] | None = None,
) -> dict:
    dates = _group_dates(panel_rows)
    tracker = CapitalTracker(total_capital=initial_capital)
    risk_state = {
        "max_loss_probability": max_loss_probability,
        "max_drawdown": max_drawdown,
    }
    gate_params = gate_params or {}
    max_positions_per_period = int(gate_params.get("max_positions_per_period", 999999))
    gate_thresholds = {
        key: value
        for key, value in gate_params.items()
        if key != "max_positions_per_period"
    }

    decisions: list[dict[str, str | float]] = []
    period_records: list[dict[str, str | float]] = []
    gating_counts: dict[str, int] = defaultdict(int)

    for period_index, as_of_date in enumerate(dates):
        tracker.reset_period()
        state_rows = reconstruct_state(panel_rows, as_of_date)
        ranked_candidates: list[dict[str, str | float]] = []

        for candidate_index, state in enumerate(state_rows):
            factor_score = compute_market_factor(
                {
                    "TAM": float(state["TAM"]),
                    "CAGR": float(state["CAGR"]),
                    "HHI": float(state["HHI"]),
                    "volatility": float(state["volatility"]),
                }
            )
            model_outputs = run_profit_simulation(
                {
                    "expected_price": float(state["expected_price"]),
                    "landed_cost": float(state["landed_cost"]),
                    "platform_fee": float(state["platform_fee"]),
                },
                simulations=simulations,
                seed=seed + period_index * 100 + candidate_index,
            )
            ranked_candidates.append(
                {
                    **state,
                    "factor_score": round(factor_score, 6),
                    **model_outputs,
                }
            )

        ranked_candidates.sort(key=lambda item: (float(item["factor_score"]), float(item["profit_p50"])), reverse=True)
        period_profit = 0.0
        period_deployed = 0.0
        positions_taken = 0
        benchmark_returns: list[float] = []

        for candidate in ranked_candidates:
            required_capital = float(candidate["required_capital"])
            capital_state = {
                "total_capital": tracker.total_capital,
                "allocated_capital": tracker.allocated_capital,
                "free_capital": tracker.free_capital,
            }
            decision = evaluate_market_gate(
                factor_score=float(candidate["factor_score"]),
                model_outputs={
                    "profit_p10": float(candidate["profit_p10"]),
                    "profit_p50": float(candidate["profit_p50"]),
                    "profit_p90": float(candidate["profit_p90"]),
                    "margin_p50_ratio": float(candidate["margin_p50_ratio"]),
                    "loss_probability": float(candidate["loss_probability"]),
                },
                capital_state=capital_state,
                risk_state=risk_state,
                required_capital=required_capital,
                candidate_features={
                    "volatility": float(candidate["volatility"]),
                    "hhi": float(candidate["HHI"]),
                    "governance_readiness_score": float(candidate.get("governance_readiness_score", 0.0)),
                    "localization_governance_score": float(candidate.get("localization_governance_score", 0.0)),
                    "control_tower_score": float(candidate.get("control_tower_score", 0.0)),
                    "master_data_health_score": float(candidate.get("master_data_health_score", 0.0)),
                    "audit_trace_score": float(candidate.get("audit_trace_score", 0.0)),
                    "decision_gate_control_score": float(candidate.get("decision_gate_control_score", 0.0)),
                    "forecast_backtest_score": float(candidate.get("forecast_backtest_score", 0.0)),
                    "signal_regime_score": float(candidate.get("signal_regime_score", 0.0)),
                    "signal_seasonality_confidence_score": float(
                        candidate.get("signal_seasonality_confidence_score", 0.0)
                    ),
                    "signal_spectral_entropy": float(candidate.get("signal_spectral_entropy", 1.0)),
                    "signal_approximate_entropy": float(candidate.get("signal_approximate_entropy", 1.0)),
                    "forecast_mape": float(candidate.get("forecast_mape", 0.0)),
                    "drift_score": float(candidate.get("drift_score", 0.0)),
                    "drift_risk_score": float(candidate.get("drift_risk_score", 0.0)),
                    "calibration_brier_score": float(candidate.get("calibration_brier_score", 0.0)),
                    "threshold_alignment_ratio": float(candidate.get("threshold_alignment_ratio", 0.0)),
                    "gate_consistency_ratio": float(candidate.get("gate_consistency_ratio", 0.0)),
                    "supply_tail_risk_score": float(candidate.get("supply_tail_risk_score", 0.0)),
                    "supply_loss_probability": float(candidate.get("supply_loss_probability", 0.0)),
                    "supply_margin_floor_breach_probability": float(candidate.get("supply_margin_floor_breach_probability", 0.0)),
                    "supply_optimizer_feasible_ratio": float(candidate.get("supply_optimizer_feasible_ratio", 0.0)),
                    "supply_execution_confidence_score": float(candidate.get("supply_execution_confidence_score", 0.0)),
                    "supply_optimizer_gate_pass": float(candidate.get("supply_optimizer_gate_pass", 0.0)),
                    "channel_portfolio_readiness_score": float(candidate.get("channel_portfolio_readiness_score", 0.0)),
                    "channel_portfolio_resilience_score": float(candidate.get("channel_portfolio_resilience_score", 0.0)),
                    "channel_execution_friction_factor": float(candidate.get("channel_execution_friction_factor", 0.0)),
                    "channel_scale_readiness_score": float(candidate.get("channel_scale_readiness_score", 0.0)),
                    "channel_optimizer_feasible_ratio": float(candidate.get("channel_optimizer_feasible_ratio", 0.0)),
                    "channel_optimizer_gate_pass": float(candidate.get("channel_optimizer_gate_pass", 0.0)),
                    "channel_stress_robustness_score": float(candidate.get("channel_stress_robustness_score", 0.0)),
                    "channel_gate_flip_count": float(candidate.get("channel_gate_flip_count", 0.0)),
                    "channel_loss_probability_weighted": float(
                        candidate.get("channel_loss_probability_weighted", 0.0)
                    ),
                    "channel_margin_rate_var_95": float(candidate.get("channel_margin_rate_var_95", 0.0)),
                    "channel_margin_rate_es_95": float(candidate.get("channel_margin_rate_es_95", 0.0)),
                    "channel_tail_shortfall_severity": float(
                        candidate.get("channel_tail_shortfall_severity", 0.0)
                    ),
                    "operating_system_readiness_score": float(candidate.get("operating_system_readiness_score", 0.0)),
                    "operating_health_score": float(candidate.get("operating_health_score", 0.0)),
                    "data_contract_score": float(candidate.get("data_contract_score", 0.0)),
                    "experiment_confidence_score": float(candidate.get("experiment_confidence_score", 0.0)),
                    "scale_control_score": float(candidate.get("scale_control_score", 0.0)),
                    "operating_proxy_flag_count": float(candidate.get("operating_proxy_flag_count", 0.0)),
                },
                thresholds=gate_thresholds,
            )

            if decision == "GO" and positions_taken >= max_positions_per_period:
                decision = "NO_GO_PORTFOLIO_CAP"

            realized_profit = 0.0
            if decision == "GO":
                if not tracker.allocate(required_capital):
                    decision = "NO_GO_CAPITAL"
                else:
                    positions_taken += 1
                    realized_profit = required_capital * float(candidate["forward_return_rate"])
                    period_profit += realized_profit
                    period_deployed += required_capital

            if decision != "GO":
                realized_profit = 0.0

            benchmark_returns.append(float(candidate["benchmark_return_rate"]))
            gating_counts[decision] += 1
            decisions.append(
                {
                    "as_of_date": as_of_date,
                    "entity_id": candidate["entity_id"],
                    "segment": candidate["segment"],
                    "decision": decision,
                    "factor_score": round(float(candidate["factor_score"]), 6),
                    "signal_regime": str(candidate.get("signal_regime", "")),
                    "signal_regime_score": round(float(candidate.get("signal_regime_score", 0.0)), 4),
                    "signal_seasonality_confidence_score": round(
                        float(candidate.get("signal_seasonality_confidence_score", 0.0)),
                        4,
                    ),
                    "signal_spectral_entropy": round(float(candidate.get("signal_spectral_entropy", 0.0)), 4),
                    "signal_approximate_entropy": round(
                        float(candidate.get("signal_approximate_entropy", 0.0)),
                        4,
                    ),
                    "profit_p10": round(float(candidate["profit_p10"]), 4),
                    "profit_p50": round(float(candidate["profit_p50"]), 4),
                    "margin_p50_ratio": round(float(candidate["margin_p50_ratio"]), 6),
                    "loss_probability": round(float(candidate["loss_probability"]), 6),
                    "volatility": round(float(candidate["volatility"]), 6),
                    "hhi": round(float(candidate["HHI"]), 2),
                    "forecast_backtest_score": round(float(candidate.get("forecast_backtest_score", 0.0)), 4),
                    "forecast_mape": round(float(candidate.get("forecast_mape", 0.0)), 4),
                    "drift_score": round(float(candidate.get("drift_score", 0.0)), 4),
                    "drift_risk_score": round(float(candidate.get("drift_risk_score", 0.0)), 4),
                    "calibration_brier_score": round(float(candidate.get("calibration_brier_score", 0.0)), 4),
                    "threshold_alignment_ratio": round(float(candidate.get("threshold_alignment_ratio", 0.0)), 4),
                    "gate_consistency_ratio": round(float(candidate.get("gate_consistency_ratio", 0.0)), 4),
                    "governance_readiness_score": round(float(candidate.get("governance_readiness_score", 0.0)), 4),
                    "localization_governance_score": round(
                        float(candidate.get("localization_governance_score", 0.0)),
                        4,
                    ),
                    "control_tower_score": round(float(candidate.get("control_tower_score", 0.0)), 4),
                    "master_data_health_score": round(float(candidate.get("master_data_health_score", 0.0)), 4),
                    "audit_trace_score": round(float(candidate.get("audit_trace_score", 0.0)), 4),
                    "decision_gate_control_score": round(
                        float(candidate.get("decision_gate_control_score", 0.0)),
                        4,
                    ),
                    "supply_tail_risk_score": round(float(candidate.get("supply_tail_risk_score", 0.0)), 4),
                    "supply_loss_probability": round(float(candidate.get("supply_loss_probability", 0.0)), 4),
                    "supply_margin_floor_breach_probability": round(
                        float(candidate.get("supply_margin_floor_breach_probability", 0.0)),
                        4,
                    ),
                    "supply_optimizer_feasible_ratio": round(
                        float(candidate.get("supply_optimizer_feasible_ratio", 0.0)),
                        4,
                    ),
                    "supply_execution_confidence_score": round(
                        float(candidate.get("supply_execution_confidence_score", 0.0)),
                        4,
                    ),
                    "supply_optimizer_gate_pass": round(float(candidate.get("supply_optimizer_gate_pass", 0.0)), 4),
                    "channel_portfolio_readiness_score": round(
                        float(candidate.get("channel_portfolio_readiness_score", 0.0)),
                        4,
                    ),
                    "channel_portfolio_resilience_score": round(
                        float(candidate.get("channel_portfolio_resilience_score", 0.0)),
                        4,
                    ),
                    "channel_execution_friction_factor": round(
                        float(candidate.get("channel_execution_friction_factor", 0.0)),
                        4,
                    ),
                    "channel_scale_readiness_score": round(
                        float(candidate.get("channel_scale_readiness_score", 0.0)),
                        4,
                    ),
                    "channel_optimizer_feasible_ratio": round(
                        float(candidate.get("channel_optimizer_feasible_ratio", 0.0)),
                        4,
                    ),
                    "channel_optimizer_gate_pass": round(
                        float(candidate.get("channel_optimizer_gate_pass", 0.0)),
                        4,
                    ),
                    "channel_risk_adjusted_profit": round(
                        float(candidate.get("channel_risk_adjusted_profit", 0.0)),
                        2,
                    ),
                    "channel_stress_robustness_score": round(
                        float(candidate.get("channel_stress_robustness_score", 0.0)),
                        4,
                    ),
                    "channel_gate_flip_count": round(float(candidate.get("channel_gate_flip_count", 0.0)), 4),
                    "channel_loss_probability_weighted": round(
                        float(candidate.get("channel_loss_probability_weighted", 0.0)),
                        4,
                    ),
                    "channel_margin_rate_var_95": round(float(candidate.get("channel_margin_rate_var_95", 0.0)), 4),
                    "channel_margin_rate_es_95": round(float(candidate.get("channel_margin_rate_es_95", 0.0)), 4),
                    "channel_tail_shortfall_severity": round(
                        float(candidate.get("channel_tail_shortfall_severity", 0.0)),
                        4,
                    ),
                    "operating_system_readiness_score": round(
                        float(candidate.get("operating_system_readiness_score", 0.0)),
                        4,
                    ),
                    "operating_health_score": round(float(candidate.get("operating_health_score", 0.0)), 4),
                    "data_contract_score": round(float(candidate.get("data_contract_score", 0.0)), 4),
                    "experiment_confidence_score": round(
                        float(candidate.get("experiment_confidence_score", 0.0)),
                        4,
                    ),
                    "scale_control_score": round(float(candidate.get("scale_control_score", 0.0)), 4),
                    "operating_proxy_flag_count": round(float(candidate.get("operating_proxy_flag_count", 0.0)), 4),
                    "required_capital": round(required_capital, 2),
                    "forward_return_rate": round(float(candidate["forward_return_rate"]), 6),
                    "realized_profit": round(realized_profit, 2),
                }
            )

        starting_capital = tracker.total_capital
        tracker.close_period(as_of_date, period_profit)
        strategy_return = period_profit / starting_capital if starting_capital else 0.0
        benchmark_return = sum(benchmark_returns) / len(benchmark_returns) if benchmark_returns else 0.0
        period_records.append(
            {
                "as_of_date": as_of_date,
                "starting_capital": round(starting_capital, 2),
                "ending_capital": round(tracker.total_capital, 2),
                "period_profit": round(period_profit, 2),
                "deployed_capital": round(period_deployed, 2),
                "positions_taken": positions_taken,
                "strategy_return": round(strategy_return, 6),
                "benchmark_return": round(benchmark_return, 6),
            }
        )

    summary = calculate_performance_summary(period_records, decisions)
    summary["initial_capital"] = round(initial_capital, 2)
    summary["ending_capital"] = round(tracker.total_capital, 2)
    summary["gate_breakdown"] = dict(sorted(gating_counts.items()))
    summary["gate_params"] = gate_params or {
        "min_profit_p50": 0.0,
        "max_loss_probability": max_loss_probability,
        "min_factor_score": 0.5,
        "max_positions_per_period": 999999,
    }
    return {
        "summary": summary,
        "period_records": period_records,
        "decisions": decisions,
    }
