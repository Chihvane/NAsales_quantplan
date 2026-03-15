from __future__ import annotations

from copy import deepcopy

from backtest.walk_forward_engine import run_walk_forward_backtest


DEFAULT_STRESS_SCENARIOS: dict[str, dict[str, float]] = {
    "freight_up_40": {
        "landed_cost_multiplier": 1.40,
        "governance_readiness_shift": -0.03,
        "localization_governance_shift": -0.04,
        "control_tower_shift": -0.05,
        "master_data_health_shift": -0.04,
        "audit_trace_shift": -0.03,
        "decision_gate_control_shift": -0.05,
        "signal_regime_score_shift": -0.04,
        "signal_seasonality_shift": -0.03,
        "signal_spectral_entropy_shift": 0.04,
        "signal_approximate_entropy_shift": 0.03,
        "drift_risk_shift": 0.06,
        "calibration_brier_multiplier": 1.10,
        "supply_tail_risk_shift": 0.14,
        "supply_loss_probability_shift": 0.08,
        "supply_margin_floor_breach_shift": 0.10,
        "supply_optimizer_feasible_ratio_shift": -0.16,
        "supply_execution_confidence_shift": -0.10,
        "supply_optimizer_gate_pass_shift": -0.35,
        "channel_resilience_shift": -0.12,
        "channel_execution_friction_shift": -0.08,
        "channel_scale_readiness_shift": -0.06,
        "channel_optimizer_feasible_ratio_shift": -0.16,
        "channel_stress_robustness_shift": -0.12,
        "channel_gate_flip_count_shift": 1.0,
        "channel_optimizer_gate_pass_shift": -0.35,
        "channel_loss_probability_weighted_shift": 0.08,
        "channel_margin_rate_var_shift": -0.012,
        "channel_margin_rate_es_shift": -0.016,
        "channel_tail_shortfall_severity_shift": 0.02,
        "operating_system_readiness_shift": -0.10,
        "operating_health_shift": -0.08,
        "data_contract_shift": -0.04,
        "experiment_confidence_shift": -0.04,
        "scale_control_shift": -0.08,
        "operating_proxy_flag_count_shift": 2.0,
    },
    "cpc_up_50": {
        "platform_fee_multiplier": 1.50,
        "governance_readiness_shift": -0.01,
        "control_tower_shift": -0.02,
        "forecast_score_shift": -0.04,
        "signal_regime_score_shift": -0.02,
        "signal_spectral_entropy_shift": 0.02,
        "calibration_brier_multiplier": 1.12,
        "supply_optimizer_feasible_ratio_shift": -0.03,
        "channel_execution_friction_shift": -0.12,
        "channel_optimizer_feasible_ratio_shift": -0.08,
        "channel_stress_robustness_shift": -0.06,
        "channel_gate_flip_count_shift": 0.5,
        "channel_loss_probability_weighted_shift": 0.04,
        "channel_margin_rate_var_shift": -0.005,
        "channel_margin_rate_es_shift": -0.008,
        "channel_tail_shortfall_severity_shift": 0.012,
        "operating_system_readiness_shift": -0.06,
        "operating_health_shift": -0.07,
        "experiment_confidence_shift": -0.02,
        "scale_control_shift": -0.04,
        "operating_proxy_flag_count_shift": 1.0,
    },
    "demand_drop_20": {
        "tam_multiplier": 0.80,
        "cagr_shift": -0.03,
        "expected_price_multiplier": 0.94,
        "volatility_multiplier": 1.15,
        "governance_readiness_shift": -0.08,
        "localization_governance_shift": -0.10,
        "control_tower_shift": -0.08,
        "master_data_health_shift": -0.05,
        "audit_trace_shift": -0.05,
        "decision_gate_control_shift": -0.08,
        "signal_regime_score_shift": -0.08,
        "signal_seasonality_shift": -0.12,
        "signal_spectral_entropy_shift": 0.08,
        "signal_approximate_entropy_shift": 0.06,
        "forward_return_shift": -0.04,
        "benchmark_return_shift": -0.02,
        "forecast_score_shift": -0.10,
        "forecast_mape_multiplier": 1.20,
        "drift_score_shift": -0.12,
        "drift_risk_shift": 0.10,
        "calibration_brier_multiplier": 1.18,
        "threshold_alignment_shift": -0.06,
        "gate_consistency_shift": -0.05,
        "supply_tail_risk_shift": 0.06,
        "supply_optimizer_feasible_ratio_shift": -0.05,
        "supply_execution_confidence_shift": -0.04,
        "channel_readiness_shift": -0.12,
        "channel_resilience_shift": -0.08,
        "channel_execution_friction_shift": -0.05,
        "channel_scale_readiness_shift": -0.12,
        "channel_optimizer_feasible_ratio_shift": -0.08,
        "channel_stress_robustness_shift": -0.12,
        "channel_gate_flip_count_shift": 0.75,
        "channel_loss_probability_weighted_shift": 0.06,
        "channel_margin_rate_var_shift": -0.01,
        "channel_margin_rate_es_shift": -0.012,
        "channel_tail_shortfall_severity_shift": 0.018,
        "operating_system_readiness_shift": -0.12,
        "operating_health_shift": -0.10,
        "data_contract_shift": -0.04,
        "experiment_confidence_shift": -0.08,
        "scale_control_shift": -0.12,
        "operating_proxy_flag_count_shift": 2.0,
    },
    "return_rate_shock": {
        "expected_price_multiplier": 0.96,
        "volatility_multiplier": 1.20,
        "governance_readiness_shift": -0.04,
        "control_tower_shift": -0.04,
        "signal_regime_score_shift": -0.05,
        "signal_spectral_entropy_shift": 0.05,
        "signal_approximate_entropy_shift": 0.05,
        "forward_return_shift": -0.06,
        "forecast_mape_multiplier": 1.10,
        "drift_risk_shift": 0.08,
        "calibration_brier_multiplier": 1.20,
        "gate_consistency_shift": -0.07,
        "supply_margin_floor_breach_shift": 0.05,
        "supply_execution_confidence_shift": -0.03,
        "channel_execution_friction_shift": -0.10,
        "channel_resilience_shift": -0.05,
        "channel_stress_robustness_shift": -0.10,
        "channel_gate_flip_count_shift": 0.8,
        "channel_loss_probability_weighted_shift": 0.07,
        "channel_margin_rate_var_shift": -0.012,
        "channel_margin_rate_es_shift": -0.014,
        "channel_tail_shortfall_severity_shift": 0.022,
        "operating_system_readiness_shift": -0.08,
        "operating_health_shift": -0.10,
        "experiment_confidence_shift": -0.04,
        "scale_control_shift": -0.08,
        "operating_proxy_flag_count_shift": 2.0,
    },
    "capital_cut_30": {
        "capital_multiplier": 0.70,
        "governance_readiness_shift": -0.02,
        "control_tower_shift": -0.03,
        "forecast_score_shift": -0.02,
        "signal_regime_score_shift": -0.03,
        "drift_score_shift": -0.03,
        "supply_optimizer_feasible_ratio_shift": -0.10,
        "supply_optimizer_gate_pass_shift": -0.25,
        "channel_optimizer_feasible_ratio_shift": -0.14,
        "channel_scale_readiness_shift": -0.05,
        "channel_stress_robustness_shift": -0.06,
        "channel_gate_flip_count_shift": 1.0,
        "channel_optimizer_gate_pass_shift": -0.25,
        "channel_loss_probability_weighted_shift": 0.03,
        "channel_margin_rate_var_shift": -0.006,
        "channel_margin_rate_es_shift": -0.008,
        "channel_tail_shortfall_severity_shift": 0.01,
        "operating_system_readiness_shift": -0.08,
        "operating_health_shift": -0.05,
        "data_contract_shift": -0.03,
        "experiment_confidence_shift": -0.03,
        "scale_control_shift": -0.06,
        "operating_proxy_flag_count_shift": 1.0,
    },
}


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def apply_stress_scenario(
    panel_rows: list[dict[str, str | float]],
    scenario_config: dict[str, float],
) -> list[dict[str, str | float]]:
    stressed_rows = deepcopy(panel_rows)
    for row in stressed_rows:
        if "tam_multiplier" in scenario_config:
            row["TAM"] = round(float(row["TAM"]) * scenario_config["tam_multiplier"], 2)
        if "cagr_shift" in scenario_config:
            row["CAGR"] = round(_clip(float(row["CAGR"]) + scenario_config["cagr_shift"], 0.0, 1.0), 6)
        if "volatility_multiplier" in scenario_config:
            row["volatility"] = round(
                _clip(float(row["volatility"]) * scenario_config["volatility_multiplier"], 0.01, 1.0),
                6,
            )
        if "landed_cost_multiplier" in scenario_config:
            row["landed_cost"] = round(float(row["landed_cost"]) * scenario_config["landed_cost_multiplier"], 2)
        if "expected_price_multiplier" in scenario_config:
            row["expected_price"] = round(float(row["expected_price"]) * scenario_config["expected_price_multiplier"], 2)
        if "platform_fee_multiplier" in scenario_config:
            row["platform_fee"] = round(float(row["platform_fee"]) * scenario_config["platform_fee_multiplier"], 2)
        if "forecast_score_shift" in scenario_config:
            row["forecast_backtest_score"] = round(
                _clip(float(row.get("forecast_backtest_score", 0.0)) + scenario_config["forecast_score_shift"], 0.0, 1.0),
                6,
            )
        if "governance_readiness_shift" in scenario_config:
            row["governance_readiness_score"] = round(
                _clip(
                    float(row.get("governance_readiness_score", 0.0))
                    + scenario_config["governance_readiness_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "localization_governance_shift" in scenario_config:
            row["localization_governance_score"] = round(
                _clip(
                    float(row.get("localization_governance_score", 0.0))
                    + scenario_config["localization_governance_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "control_tower_shift" in scenario_config:
            row["control_tower_score"] = round(
                _clip(float(row.get("control_tower_score", 0.0)) + scenario_config["control_tower_shift"], 0.0, 1.0),
                6,
            )
        if "master_data_health_shift" in scenario_config:
            row["master_data_health_score"] = round(
                _clip(
                    float(row.get("master_data_health_score", 0.0))
                    + scenario_config["master_data_health_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "audit_trace_shift" in scenario_config:
            row["audit_trace_score"] = round(
                _clip(float(row.get("audit_trace_score", 0.0)) + scenario_config["audit_trace_shift"], 0.0, 1.0),
                6,
            )
        if "decision_gate_control_shift" in scenario_config:
            row["decision_gate_control_score"] = round(
                _clip(
                    float(row.get("decision_gate_control_score", 0.0))
                    + scenario_config["decision_gate_control_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "signal_regime_score_shift" in scenario_config:
            row["signal_regime_score"] = round(
                _clip(float(row.get("signal_regime_score", 0.0)) + scenario_config["signal_regime_score_shift"], 0.0, 1.0),
                6,
            )
        if "signal_seasonality_shift" in scenario_config:
            row["signal_seasonality_confidence_score"] = round(
                _clip(
                    float(row.get("signal_seasonality_confidence_score", 0.0))
                    + scenario_config["signal_seasonality_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "signal_spectral_entropy_shift" in scenario_config:
            row["signal_spectral_entropy"] = round(
                _clip(
                    float(row.get("signal_spectral_entropy", 0.0))
                    + scenario_config["signal_spectral_entropy_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "signal_approximate_entropy_shift" in scenario_config:
            row["signal_approximate_entropy"] = round(
                _clip(
                    float(row.get("signal_approximate_entropy", 0.0))
                    + scenario_config["signal_approximate_entropy_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "forecast_mape_multiplier" in scenario_config:
            row["forecast_mape"] = round(
                _clip(float(row.get("forecast_mape", 0.0)) * scenario_config["forecast_mape_multiplier"], 0.0, 1.0),
                6,
            )
        if "drift_score_shift" in scenario_config:
            row["drift_score"] = round(
                _clip(float(row.get("drift_score", 0.0)) + scenario_config["drift_score_shift"], 0.0, 1.0),
                6,
            )
        if "drift_risk_shift" in scenario_config:
            row["drift_risk_score"] = round(
                _clip(float(row.get("drift_risk_score", 0.0)) + scenario_config["drift_risk_shift"], 0.0, 1.0),
                6,
            )
        if "calibration_brier_multiplier" in scenario_config:
            row["calibration_brier_score"] = round(
                _clip(float(row.get("calibration_brier_score", 0.0)) * scenario_config["calibration_brier_multiplier"], 0.0, 1.0),
                6,
            )
        if "threshold_alignment_shift" in scenario_config:
            row["threshold_alignment_ratio"] = round(
                _clip(float(row.get("threshold_alignment_ratio", 0.0)) + scenario_config["threshold_alignment_shift"], 0.0, 1.0),
                6,
            )
        if "gate_consistency_shift" in scenario_config:
            row["gate_consistency_ratio"] = round(
                _clip(float(row.get("gate_consistency_ratio", 0.0)) + scenario_config["gate_consistency_shift"], 0.0, 1.0),
                6,
            )
        if "supply_tail_risk_shift" in scenario_config:
            row["supply_tail_risk_score"] = round(
                _clip(float(row.get("supply_tail_risk_score", 0.0)) + scenario_config["supply_tail_risk_shift"], 0.0, 1.0),
                6,
            )
        if "supply_loss_probability_shift" in scenario_config:
            row["supply_loss_probability"] = round(
                _clip(
                    float(row.get("supply_loss_probability", 0.0)) + scenario_config["supply_loss_probability_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "supply_margin_floor_breach_shift" in scenario_config:
            row["supply_margin_floor_breach_probability"] = round(
                _clip(
                    float(row.get("supply_margin_floor_breach_probability", 0.0))
                    + scenario_config["supply_margin_floor_breach_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "supply_optimizer_feasible_ratio_shift" in scenario_config:
            row["supply_optimizer_feasible_ratio"] = round(
                _clip(
                    float(row.get("supply_optimizer_feasible_ratio", 0.0))
                    + scenario_config["supply_optimizer_feasible_ratio_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "supply_execution_confidence_shift" in scenario_config:
            row["supply_execution_confidence_score"] = round(
                _clip(
                    float(row.get("supply_execution_confidence_score", 0.0))
                    + scenario_config["supply_execution_confidence_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "supply_optimizer_gate_pass_shift" in scenario_config:
            row["supply_optimizer_gate_pass"] = round(
                _clip(
                    float(row.get("supply_optimizer_gate_pass", 0.0))
                    + scenario_config["supply_optimizer_gate_pass_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_readiness_shift" in scenario_config:
            row["channel_portfolio_readiness_score"] = round(
                _clip(
                    float(row.get("channel_portfolio_readiness_score", 0.0))
                    + scenario_config["channel_readiness_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_resilience_shift" in scenario_config:
            row["channel_portfolio_resilience_score"] = round(
                _clip(
                    float(row.get("channel_portfolio_resilience_score", 0.0))
                    + scenario_config["channel_resilience_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_execution_friction_shift" in scenario_config:
            row["channel_execution_friction_factor"] = round(
                _clip(
                    float(row.get("channel_execution_friction_factor", 0.0))
                    + scenario_config["channel_execution_friction_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_scale_readiness_shift" in scenario_config:
            row["channel_scale_readiness_score"] = round(
                _clip(
                    float(row.get("channel_scale_readiness_score", 0.0))
                    + scenario_config["channel_scale_readiness_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_optimizer_feasible_ratio_shift" in scenario_config:
            row["channel_optimizer_feasible_ratio"] = round(
                _clip(
                    float(row.get("channel_optimizer_feasible_ratio", 0.0))
                    + scenario_config["channel_optimizer_feasible_ratio_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_optimizer_gate_pass_shift" in scenario_config:
            row["channel_optimizer_gate_pass"] = round(
                _clip(
                    float(row.get("channel_optimizer_gate_pass", 0.0))
                    + scenario_config["channel_optimizer_gate_pass_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_stress_robustness_shift" in scenario_config:
            row["channel_stress_robustness_score"] = round(
                _clip(
                    float(row.get("channel_stress_robustness_score", 0.0))
                    + scenario_config["channel_stress_robustness_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_gate_flip_count_shift" in scenario_config:
            row["channel_gate_flip_count"] = round(
                _clip(
                    float(row.get("channel_gate_flip_count", 0.0))
                    + scenario_config["channel_gate_flip_count_shift"],
                    0.0,
                    6.0,
                ),
                6,
            )
        if "channel_loss_probability_weighted_shift" in scenario_config:
            row["channel_loss_probability_weighted"] = round(
                _clip(
                    float(row.get("channel_loss_probability_weighted", 0.0))
                    + scenario_config["channel_loss_probability_weighted_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "channel_margin_rate_var_shift" in scenario_config:
            row["channel_margin_rate_var_95"] = round(
                _clip(
                    float(row.get("channel_margin_rate_var_95", 0.0))
                    + scenario_config["channel_margin_rate_var_shift"],
                    -1.0,
                    1.0,
                ),
                6,
            )
        if "channel_margin_rate_es_shift" in scenario_config:
            row["channel_margin_rate_es_95"] = round(
                _clip(
                    float(row.get("channel_margin_rate_es_95", 0.0))
                    + scenario_config["channel_margin_rate_es_shift"],
                    -1.0,
                    1.0,
                ),
                6,
            )
        if "channel_tail_shortfall_severity_shift" in scenario_config:
            row["channel_tail_shortfall_severity"] = round(
                _clip(
                    float(row.get("channel_tail_shortfall_severity", 0.0))
                    + scenario_config["channel_tail_shortfall_severity_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "operating_system_readiness_shift" in scenario_config:
            row["operating_system_readiness_score"] = round(
                _clip(
                    float(row.get("operating_system_readiness_score", 0.0))
                    + scenario_config["operating_system_readiness_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "operating_health_shift" in scenario_config:
            row["operating_health_score"] = round(
                _clip(
                    float(row.get("operating_health_score", 0.0)) + scenario_config["operating_health_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "data_contract_shift" in scenario_config:
            row["data_contract_score"] = round(
                _clip(float(row.get("data_contract_score", 0.0)) + scenario_config["data_contract_shift"], 0.0, 1.0),
                6,
            )
        if "experiment_confidence_shift" in scenario_config:
            row["experiment_confidence_score"] = round(
                _clip(
                    float(row.get("experiment_confidence_score", 0.0))
                    + scenario_config["experiment_confidence_shift"],
                    0.0,
                    1.0,
                ),
                6,
            )
        if "scale_control_shift" in scenario_config:
            row["scale_control_score"] = round(
                _clip(float(row.get("scale_control_score", 0.0)) + scenario_config["scale_control_shift"], 0.0, 1.0),
                6,
            )
        if "operating_proxy_flag_count_shift" in scenario_config:
            row["operating_proxy_flag_count"] = round(
                _clip(
                    float(row.get("operating_proxy_flag_count", 0.0))
                    + scenario_config["operating_proxy_flag_count_shift"],
                    0.0,
                    12.0,
                ),
                6,
            )
        if "forward_return_shift" in scenario_config:
            row["forward_return_rate"] = round(
                _clip(float(row["forward_return_rate"]) + scenario_config["forward_return_shift"], -0.99, 2.0),
                6,
            )
        if "benchmark_return_shift" in scenario_config:
            row["benchmark_return_rate"] = round(
                _clip(float(row["benchmark_return_rate"]) + scenario_config["benchmark_return_shift"], -0.99, 2.0),
                6,
            )
    return stressed_rows


def _scenario_score(summary: dict[str, float | int | list[float]]) -> float:
    alpha = float(summary.get("alpha", 0.0))
    drawdown = abs(float(summary.get("strategy_max_drawdown", 0.0)))
    hit_rate = float(summary.get("decision_hit_rate", 0.0))
    selectivity = 1.0 - min(abs(float(summary.get("go_ratio", 0.0)) - 0.55) / 0.55, 1.0)

    alpha_score = 1.0 if alpha >= 0 else max(0.0, 1.0 + alpha)
    drawdown_score = max(0.0, 1.0 - drawdown / 0.35)
    return round(
        alpha_score * 0.4 + drawdown_score * 0.3 + hit_rate * 0.2 + selectivity * 0.1,
        6,
    )


def run_stress_suite(
    panel_rows: list[dict[str, str | float]],
    *,
    gate_params: dict[str, float] | None = None,
    initial_capital: float = 1_000_000,
    max_loss_probability: float = 0.30,
    max_drawdown: float = 0.20,
    simulations: int = 1200,
    seed: int = 42,
    scenario_library: dict[str, dict[str, float]] | None = None,
) -> dict[str, object]:
    scenario_library = scenario_library or DEFAULT_STRESS_SCENARIOS
    scenario_rows: list[dict[str, object]] = []

    for scenario_index, (scenario_id, scenario_config) in enumerate(scenario_library.items()):
        stressed_panel = apply_stress_scenario(panel_rows, scenario_config)
        stressed_capital = initial_capital * scenario_config.get("capital_multiplier", 1.0)
        result = run_walk_forward_backtest(
            stressed_panel,
            initial_capital=stressed_capital,
            max_loss_probability=max_loss_probability,
            max_drawdown=max_drawdown,
            simulations=simulations,
            seed=seed + (scenario_index + 1) * 500,
            gate_params=gate_params,
        )
        summary = result["summary"]
        scenario_rows.append(
            {
                "scenario_id": scenario_id,
                "capital_multiplier": scenario_config.get("capital_multiplier", 1.0),
                "summary": summary,
                "scenario_score": _scenario_score(summary),
            }
        )

    robustness_score = (
        round(sum(float(row["scenario_score"]) for row in scenario_rows) / len(scenario_rows), 6)
        if scenario_rows
        else 0.0
    )
    return {
        "scenario_count": len(scenario_rows),
        "robustness_score": robustness_score,
        "scenarios": scenario_rows,
    }
