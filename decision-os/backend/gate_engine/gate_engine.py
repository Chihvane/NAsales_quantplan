from __future__ import annotations

from backend.gate_engine.rule_parser import compare


def evaluate_market_gate(
    factor_score: float,
    model_outputs: dict[str, float],
    capital_state: dict[str, float],
    risk_state: dict[str, float],
    required_capital: float,
    candidate_features: dict[str, float] | None = None,
    thresholds: dict[str, float] | None = None,
) -> str:
    candidate_features = candidate_features or {}
    thresholds = thresholds or {}
    min_profit_p50 = thresholds.get("min_profit_p50", 0.0)
    min_factor_score = thresholds.get("min_factor_score", 0.5)
    max_loss_probability = thresholds.get(
        "max_loss_probability",
        risk_state["max_loss_probability"],
    )
    min_profit_p10 = thresholds.get("min_profit_p10")
    min_margin_p50_ratio = thresholds.get("min_margin_p50_ratio")
    max_volatility = thresholds.get("max_volatility")
    max_hhi = thresholds.get("max_hhi")
    max_required_capital_ratio = thresholds.get("max_required_capital_ratio")
    min_governance_readiness_score = thresholds.get("min_governance_readiness_score")
    min_localization_governance_score = thresholds.get("min_localization_governance_score")
    min_control_tower_score = thresholds.get("min_control_tower_score")
    min_master_data_health_score = thresholds.get("min_master_data_health_score")
    min_audit_trace_score = thresholds.get("min_audit_trace_score")
    min_decision_gate_control_score = thresholds.get("min_decision_gate_control_score")
    min_forecast_backtest_score = thresholds.get("min_forecast_backtest_score")
    max_forecast_mape = thresholds.get("max_forecast_mape")
    min_signal_regime_score = thresholds.get("min_signal_regime_score")
    min_signal_seasonality_confidence_score = thresholds.get("min_signal_seasonality_confidence_score")
    max_signal_spectral_entropy = thresholds.get("max_signal_spectral_entropy")
    max_signal_approximate_entropy = thresholds.get("max_signal_approximate_entropy")
    min_drift_score = thresholds.get("min_drift_score")
    max_drift_risk_score = thresholds.get("max_drift_risk_score")
    max_calibration_brier_score = thresholds.get("max_calibration_brier_score")
    min_threshold_alignment_ratio = thresholds.get("min_threshold_alignment_ratio")
    min_gate_consistency_ratio = thresholds.get("min_gate_consistency_ratio")
    max_supply_tail_risk_score = thresholds.get("max_supply_tail_risk_score")
    max_supply_loss_probability = thresholds.get("max_supply_loss_probability")
    max_supply_margin_floor_breach_probability = thresholds.get("max_supply_margin_floor_breach_probability")
    min_supply_optimizer_feasible_ratio = thresholds.get("min_supply_optimizer_feasible_ratio")
    min_supply_execution_confidence_score = thresholds.get("min_supply_execution_confidence_score")
    min_supply_optimizer_gate_pass = thresholds.get("min_supply_optimizer_gate_pass")
    min_channel_portfolio_readiness_score = thresholds.get("min_channel_portfolio_readiness_score")
    min_channel_portfolio_resilience_score = thresholds.get("min_channel_portfolio_resilience_score")
    min_channel_execution_friction_factor = thresholds.get("min_channel_execution_friction_factor")
    min_channel_scale_readiness_score = thresholds.get("min_channel_scale_readiness_score")
    min_channel_optimizer_feasible_ratio = thresholds.get("min_channel_optimizer_feasible_ratio")
    min_channel_optimizer_gate_pass = thresholds.get("min_channel_optimizer_gate_pass")
    min_channel_stress_robustness_score = thresholds.get("min_channel_stress_robustness_score")
    max_channel_gate_flip_count = thresholds.get("max_channel_gate_flip_count")
    max_channel_loss_probability_weighted = thresholds.get("max_channel_loss_probability_weighted")
    min_channel_margin_rate_var_95 = thresholds.get("min_channel_margin_rate_var_95")
    min_channel_margin_rate_es_95 = thresholds.get("min_channel_margin_rate_es_95")
    max_channel_tail_shortfall_severity = thresholds.get("max_channel_tail_shortfall_severity")
    min_operating_system_readiness_score = thresholds.get("min_operating_system_readiness_score")
    min_operating_health_score = thresholds.get("min_operating_health_score")
    min_data_contract_score = thresholds.get("min_data_contract_score")
    min_experiment_confidence_score = thresholds.get("min_experiment_confidence_score")
    min_scale_control_score = thresholds.get("min_scale_control_score")
    max_operating_proxy_flag_count = thresholds.get("max_operating_proxy_flag_count")

    total_capital = float(
        capital_state.get(
            "total_capital",
            capital_state.get("free_capital", required_capital),
        )
    )

    if not compare(model_outputs["profit_p50"], ">=", min_profit_p50):
        return "NO_GO_PROFIT"
    if min_profit_p10 is not None and not compare(model_outputs.get("profit_p10", 0.0), ">=", min_profit_p10):
        return "NO_GO_PROFIT_TAIL"
    if min_margin_p50_ratio is not None and not compare(
        model_outputs.get("margin_p50_ratio", 0.0),
        ">=",
        min_margin_p50_ratio,
    ):
        return "NO_GO_MARGIN"
    if not compare(model_outputs["loss_probability"], "<=", max_loss_probability):
        return "NO_GO_RISK"
    if not compare(factor_score, ">=", min_factor_score):
        return "NO_GO_FACTOR"
    if max_volatility is not None and "volatility" in candidate_features:
        if not compare(float(candidate_features["volatility"]), "<=", max_volatility):
            return "NO_GO_VOLATILITY"
    if max_hhi is not None and "hhi" in candidate_features:
        if not compare(float(candidate_features["hhi"]), "<=", max_hhi):
            return "NO_GO_CONCENTRATION"
    if min_governance_readiness_score is not None and "governance_readiness_score" in candidate_features:
        if not compare(float(candidate_features["governance_readiness_score"]), ">=", min_governance_readiness_score):
            return "NO_GO_GOVERNANCE"
    if min_localization_governance_score is not None and "localization_governance_score" in candidate_features:
        if not compare(
            float(candidate_features["localization_governance_score"]),
            ">=",
            min_localization_governance_score,
        ):
            return "NO_GO_LOCALIZATION"
    if min_control_tower_score is not None and "control_tower_score" in candidate_features:
        if not compare(float(candidate_features["control_tower_score"]), ">=", min_control_tower_score):
            return "NO_GO_CONTROL_TOWER"
    if min_master_data_health_score is not None and "master_data_health_score" in candidate_features:
        if not compare(float(candidate_features["master_data_health_score"]), ">=", min_master_data_health_score):
            return "NO_GO_MASTER_DATA"
    if min_audit_trace_score is not None and "audit_trace_score" in candidate_features:
        if not compare(float(candidate_features["audit_trace_score"]), ">=", min_audit_trace_score):
            return "NO_GO_AUDIT_TRACE"
    if min_decision_gate_control_score is not None and "decision_gate_control_score" in candidate_features:
        if not compare(
            float(candidate_features["decision_gate_control_score"]),
            ">=",
            min_decision_gate_control_score,
        ):
            return "NO_GO_RULE_CONTROL"
    if min_forecast_backtest_score is not None and "forecast_backtest_score" in candidate_features:
        if not compare(float(candidate_features["forecast_backtest_score"]), ">=", min_forecast_backtest_score):
            return "NO_GO_FORECAST"
    if max_forecast_mape is not None and "forecast_mape" in candidate_features:
        if not compare(float(candidate_features["forecast_mape"]), "<=", max_forecast_mape):
            return "NO_GO_FORECAST_ERROR"
    if min_signal_regime_score is not None and "signal_regime_score" in candidate_features:
        if not compare(float(candidate_features["signal_regime_score"]), ">=", min_signal_regime_score):
            return "NO_GO_SIGNAL_REGIME"
    if (
        min_signal_seasonality_confidence_score is not None
        and "signal_seasonality_confidence_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["signal_seasonality_confidence_score"]),
            ">=",
            min_signal_seasonality_confidence_score,
        ):
            return "NO_GO_SIGNAL_SEASONALITY"
    if max_signal_spectral_entropy is not None and "signal_spectral_entropy" in candidate_features:
        if not compare(float(candidate_features["signal_spectral_entropy"]), "<=", max_signal_spectral_entropy):
            return "NO_GO_SIGNAL_ENTROPY"
    if max_signal_approximate_entropy is not None and "signal_approximate_entropy" in candidate_features:
        if not compare(float(candidate_features["signal_approximate_entropy"]), "<=", max_signal_approximate_entropy):
            return "NO_GO_SIGNAL_COMPLEXITY"
    if min_drift_score is not None and "drift_score" in candidate_features:
        if not compare(float(candidate_features["drift_score"]), ">=", min_drift_score):
            return "NO_GO_DRIFT"
    if max_drift_risk_score is not None and "drift_risk_score" in candidate_features:
        if not compare(float(candidate_features["drift_risk_score"]), "<=", max_drift_risk_score):
            return "NO_GO_DRIFT_RISK"
    if max_calibration_brier_score is not None and "calibration_brier_score" in candidate_features:
        if not compare(float(candidate_features["calibration_brier_score"]), "<=", max_calibration_brier_score):
            return "NO_GO_CALIBRATION"
    if min_threshold_alignment_ratio is not None and "threshold_alignment_ratio" in candidate_features:
        if not compare(float(candidate_features["threshold_alignment_ratio"]), ">=", min_threshold_alignment_ratio):
            return "NO_GO_THRESHOLD_ALIGNMENT"
    if min_gate_consistency_ratio is not None and "gate_consistency_ratio" in candidate_features:
        if not compare(float(candidate_features["gate_consistency_ratio"]), ">=", min_gate_consistency_ratio):
            return "NO_GO_GATE_CONSISTENCY"
    if max_supply_tail_risk_score is not None and "supply_tail_risk_score" in candidate_features:
        if not compare(float(candidate_features["supply_tail_risk_score"]), "<=", max_supply_tail_risk_score):
            return "NO_GO_SUPPLY_TAIL_RISK"
    if max_supply_loss_probability is not None and "supply_loss_probability" in candidate_features:
        if not compare(float(candidate_features["supply_loss_probability"]), "<=", max_supply_loss_probability):
            return "NO_GO_SUPPLY_LOSS"
    if (
        max_supply_margin_floor_breach_probability is not None
        and "supply_margin_floor_breach_probability" in candidate_features
    ):
        if not compare(
            float(candidate_features["supply_margin_floor_breach_probability"]),
            "<=",
            max_supply_margin_floor_breach_probability,
        ):
            return "NO_GO_SUPPLY_MARGIN_FLOOR"
    if min_supply_optimizer_feasible_ratio is not None and "supply_optimizer_feasible_ratio" in candidate_features:
        if not compare(
            float(candidate_features["supply_optimizer_feasible_ratio"]),
            ">=",
            min_supply_optimizer_feasible_ratio,
        ):
            return "NO_GO_SUPPLY_FEASIBILITY"
    if (
        min_supply_execution_confidence_score is not None
        and "supply_execution_confidence_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["supply_execution_confidence_score"]),
            ">=",
            min_supply_execution_confidence_score,
        ):
            return "NO_GO_SUPPLY_EXECUTION"
    if min_supply_optimizer_gate_pass is not None and "supply_optimizer_gate_pass" in candidate_features:
        if not compare(
            float(candidate_features["supply_optimizer_gate_pass"]),
            ">=",
            min_supply_optimizer_gate_pass,
        ):
            return "NO_GO_SUPPLY_OPTIMIZER"
    if (
        min_channel_portfolio_readiness_score is not None
        and "channel_portfolio_readiness_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_portfolio_readiness_score"]),
            ">=",
            min_channel_portfolio_readiness_score,
        ):
            return "NO_GO_CHANNEL_READINESS"
    if (
        min_channel_portfolio_resilience_score is not None
        and "channel_portfolio_resilience_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_portfolio_resilience_score"]),
            ">=",
            min_channel_portfolio_resilience_score,
        ):
            return "NO_GO_CHANNEL_RESILIENCE"
    if (
        min_channel_execution_friction_factor is not None
        and "channel_execution_friction_factor" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_execution_friction_factor"]),
            ">=",
            min_channel_execution_friction_factor,
        ):
            return "NO_GO_CHANNEL_FRICTION"
    if (
        min_channel_scale_readiness_score is not None
        and "channel_scale_readiness_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_scale_readiness_score"]),
            ">=",
            min_channel_scale_readiness_score,
        ):
            return "NO_GO_CHANNEL_SCALE"
    if (
        min_channel_optimizer_feasible_ratio is not None
        and "channel_optimizer_feasible_ratio" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_optimizer_feasible_ratio"]),
            ">=",
            min_channel_optimizer_feasible_ratio,
        ):
            return "NO_GO_CHANNEL_FEASIBILITY"
    if min_channel_optimizer_gate_pass is not None and "channel_optimizer_gate_pass" in candidate_features:
        if not compare(
            float(candidate_features["channel_optimizer_gate_pass"]),
            ">=",
            min_channel_optimizer_gate_pass,
        ):
            return "NO_GO_CHANNEL_OPTIMIZER"
    if (
        min_channel_stress_robustness_score is not None
        and "channel_stress_robustness_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_stress_robustness_score"]),
            ">=",
            min_channel_stress_robustness_score,
        ):
            return "NO_GO_CHANNEL_STRESS"
    if max_channel_gate_flip_count is not None and "channel_gate_flip_count" in candidate_features:
        if not compare(
            float(candidate_features["channel_gate_flip_count"]),
            "<=",
            max_channel_gate_flip_count,
        ):
            return "NO_GO_CHANNEL_GATE_FLIP"
    if (
        max_channel_loss_probability_weighted is not None
        and "channel_loss_probability_weighted" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_loss_probability_weighted"]),
            "<=",
            max_channel_loss_probability_weighted,
        ):
            return "NO_GO_CHANNEL_WEIGHTED_LOSS"
    if min_channel_margin_rate_var_95 is not None and "channel_margin_rate_var_95" in candidate_features:
        if not compare(
            float(candidate_features["channel_margin_rate_var_95"]),
            ">=",
            min_channel_margin_rate_var_95,
        ):
            return "NO_GO_CHANNEL_TAIL_VAR"
    if min_channel_margin_rate_es_95 is not None and "channel_margin_rate_es_95" in candidate_features:
        if not compare(
            float(candidate_features["channel_margin_rate_es_95"]),
            ">=",
            min_channel_margin_rate_es_95,
        ):
            return "NO_GO_CHANNEL_TAIL_ES"
    if (
        max_channel_tail_shortfall_severity is not None
        and "channel_tail_shortfall_severity" in candidate_features
    ):
        if not compare(
            float(candidate_features["channel_tail_shortfall_severity"]),
            "<=",
            max_channel_tail_shortfall_severity,
        ):
            return "NO_GO_CHANNEL_TAIL_SHORTFALL"
    if (
        min_operating_system_readiness_score is not None
        and "operating_system_readiness_score" in candidate_features
    ):
        if not compare(
            float(candidate_features["operating_system_readiness_score"]),
            ">=",
            min_operating_system_readiness_score,
        ):
            return "NO_GO_OPERATING_SYSTEM"
    if min_operating_health_score is not None and "operating_health_score" in candidate_features:
        if not compare(float(candidate_features["operating_health_score"]), ">=", min_operating_health_score):
            return "NO_GO_OPERATING_HEALTH"
    if min_data_contract_score is not None and "data_contract_score" in candidate_features:
        if not compare(float(candidate_features["data_contract_score"]), ">=", min_data_contract_score):
            return "NO_GO_DATA_CONTRACT"
    if min_experiment_confidence_score is not None and "experiment_confidence_score" in candidate_features:
        if not compare(
            float(candidate_features["experiment_confidence_score"]),
            ">=",
            min_experiment_confidence_score,
        ):
            return "NO_GO_EXPERIMENT_CONFIDENCE"
    if min_scale_control_score is not None and "scale_control_score" in candidate_features:
        if not compare(float(candidate_features["scale_control_score"]), ">=", min_scale_control_score):
            return "NO_GO_SCALE_CONTROL"
    if max_operating_proxy_flag_count is not None and "operating_proxy_flag_count" in candidate_features:
        if not compare(
            float(candidate_features["operating_proxy_flag_count"]),
            "<=",
            max_operating_proxy_flag_count,
        ):
            return "NO_GO_OPERATING_PROXY"
    if max_required_capital_ratio is not None and total_capital > 0:
        required_capital_ratio = required_capital / total_capital
        if not compare(required_capital_ratio, "<=", max_required_capital_ratio):
            return "NO_GO_CAPITAL_SHARE"
    if not compare(required_capital, "<=", capital_state["free_capital"]):
        return "NO_GO_CAPITAL"
    return "GO"
