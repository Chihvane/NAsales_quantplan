from __future__ import annotations

from itertools import product
from pathlib import Path
import random

from backtest.report_generator import write_json
from backtest.stress_test import run_stress_suite
from backtest.walk_forward_engine import run_walk_forward_backtest
from backend.oss_integrations.mlflow_adapter import log_tracking_payload
from backend.oss_integrations.optuna_adapter import get_optuna_status


def _band_score(value: float, lower: float, upper: float) -> float:
    if lower <= value <= upper:
        return 1.0
    if value < lower:
        return max(0.0, 1.0 - ((lower - value) / max(lower, 1e-9)))
    return max(0.0, 1.0 - ((value - upper) / max(1.0 - upper, 1e-9)))


def _composite_score(summary: dict[str, float | int | list[float]], stress_summary: dict[str, object] | None = None) -> float:
    alpha = float(summary.get("alpha", 0.0))
    hit_rate = float(summary.get("decision_hit_rate", 0.0))
    rejection_precision = float(summary.get("rejection_precision", 0.0))
    go_ratio = float(summary.get("go_ratio", 0.0))
    drawdown = abs(float(summary.get("strategy_max_drawdown", 0.0)))
    deployed_capital_ratio = float(summary.get("average_deployed_capital_ratio", 0.0))
    forecast_backtest_score = float(summary.get("average_forecast_backtest_score", 0.0))
    signal_regime_score = float(summary.get("average_signal_regime_score", 0.0))
    signal_seasonality_confidence_score = float(summary.get("average_signal_seasonality_confidence_score", 0.0))
    signal_spectral_entropy = float(summary.get("average_signal_spectral_entropy", 1.0))
    signal_approximate_entropy = float(summary.get("average_signal_approximate_entropy", 1.0))
    forecast_mape = float(summary.get("average_forecast_mape", 0.0))
    drift_score = float(summary.get("average_drift_score", 0.0))
    drift_risk_score = float(summary.get("average_drift_risk_score", 0.0))
    calibration_brier_score = float(summary.get("average_calibration_brier_score", 1.0))
    governance_readiness_score = float(summary.get("average_governance_readiness_score", 0.0))
    localization_governance_score = float(summary.get("average_localization_governance_score", 0.0))
    control_tower_score = float(summary.get("average_control_tower_score", 0.0))
    master_data_health_score = float(summary.get("average_master_data_health_score", 0.0))
    audit_trace_score = float(summary.get("average_audit_trace_score", 0.0))
    decision_gate_control_score = float(summary.get("average_decision_gate_control_score", 0.0))
    threshold_alignment_ratio = float(summary.get("average_threshold_alignment_ratio", 0.0))
    gate_consistency_ratio = float(summary.get("average_gate_consistency_ratio", 0.0))
    supply_tail_risk_score = float(summary.get("average_supply_tail_risk_score", 1.0))
    supply_loss_probability = float(summary.get("average_supply_loss_probability", 1.0))
    supply_margin_floor_breach_probability = float(summary.get("average_supply_margin_floor_breach_probability", 1.0))
    supply_optimizer_feasible_ratio = float(summary.get("average_supply_optimizer_feasible_ratio", 0.0))
    supply_execution_confidence_score = float(summary.get("average_supply_execution_confidence_score", 0.0))
    supply_optimizer_gate_pass = float(summary.get("average_supply_optimizer_gate_pass", 0.0))
    channel_portfolio_readiness_score = float(summary.get("average_channel_portfolio_readiness_score", 0.0))
    channel_portfolio_resilience_score = float(summary.get("average_channel_portfolio_resilience_score", 0.0))
    channel_execution_friction_factor = float(summary.get("average_channel_execution_friction_factor", 0.0))
    channel_scale_readiness_score = float(summary.get("average_channel_scale_readiness_score", 0.0))
    channel_optimizer_feasible_ratio = float(summary.get("average_channel_optimizer_feasible_ratio", 0.0))
    channel_optimizer_gate_pass = float(summary.get("average_channel_optimizer_gate_pass", 0.0))
    channel_risk_adjusted_profit = float(summary.get("average_channel_risk_adjusted_profit", 0.0))
    channel_stress_robustness_score = float(summary.get("average_channel_stress_robustness_score", 0.0))
    channel_gate_flip_count = float(summary.get("average_channel_gate_flip_count", 0.0))
    channel_loss_probability_weighted = float(summary.get("average_channel_loss_probability_weighted", 1.0))
    channel_margin_rate_var_95 = float(summary.get("average_channel_margin_rate_var_95", 0.0))
    channel_margin_rate_es_95 = float(summary.get("average_channel_margin_rate_es_95", 0.0))
    channel_tail_shortfall_severity = float(summary.get("average_channel_tail_shortfall_severity", 1.0))
    operating_system_readiness_score = float(summary.get("average_operating_system_readiness_score", 0.0))
    operating_health_score = float(summary.get("average_operating_health_score", 0.0))
    data_contract_score = float(summary.get("average_data_contract_score", 0.0))
    experiment_confidence_score = float(summary.get("average_experiment_confidence_score", 0.0))
    scale_control_score = float(summary.get("average_scale_control_score", 0.0))
    operating_proxy_flag_count = float(summary.get("average_operating_proxy_flag_count", 0.0))
    stress_robustness = float(stress_summary.get("robustness_score", 0.5)) if stress_summary else 0.5
    channel_gate_flip_score = _band_score(channel_gate_flip_count, 0.0, 0.8)
    channel_risk_adjusted_profit_score = _band_score(channel_risk_adjusted_profit, 1000.0, 6000.0)
    signal_entropy_score = _band_score(signal_spectral_entropy, 0.0, 0.75)
    signal_complexity_score = _band_score(signal_approximate_entropy, 0.0, 0.3)
    channel_tail_shortfall_score = _band_score(channel_tail_shortfall_severity, 0.0, 0.06)
    channel_weighted_loss_score = _band_score(channel_loss_probability_weighted, 0.0, 0.18)
    channel_margin_tail_score = (
        _band_score(channel_margin_rate_var_95, 0.015, 0.12) * 0.55
        + _band_score(channel_margin_rate_es_95, 0.005, 0.08) * 0.45
    )

    selectivity_score = _band_score(go_ratio, 0.30, 0.70)
    deployed_capital_score = _band_score(deployed_capital_ratio, 0.35, 0.85)
    forecast_accuracy_score = _band_score(forecast_mape, 0.0, 0.18)
    calibration_quality_score = _band_score(calibration_brier_score, 0.0, 0.18)
    composite = (
        alpha * 1.1
        + hit_rate * 0.35
        + rejection_precision * 0.35
        + selectivity_score * 0.25
        + deployed_capital_score * 0.20
        + forecast_backtest_score * 0.20
        + signal_regime_score * 0.12
        + signal_seasonality_confidence_score * 0.10
        + signal_entropy_score * 0.08
        + signal_complexity_score * 0.06
        + forecast_accuracy_score * 0.15
        + drift_score * 0.15
        + (1 - drift_risk_score) * 0.15
        + calibration_quality_score * 0.15
        + governance_readiness_score * 0.14
        + localization_governance_score * 0.12
        + control_tower_score * 0.12
        + master_data_health_score * 0.08
        + audit_trace_score * 0.08
        + decision_gate_control_score * 0.08
        + threshold_alignment_ratio * 0.10
        + gate_consistency_ratio * 0.10
        + (1 - supply_tail_risk_score) * 0.18
        + (1 - supply_loss_probability) * 0.12
        + (1 - supply_margin_floor_breach_probability) * 0.12
        + supply_optimizer_feasible_ratio * 0.15
        + supply_execution_confidence_score * 0.15
        + supply_optimizer_gate_pass * 0.10
        + channel_portfolio_readiness_score * 0.15
        + channel_portfolio_resilience_score * 0.15
        + channel_execution_friction_factor * 0.12
        + channel_scale_readiness_score * 0.12
        + channel_optimizer_feasible_ratio * 0.15
        + channel_optimizer_gate_pass * 0.10
        + channel_risk_adjusted_profit_score * 0.10
        + channel_weighted_loss_score * 0.08
        + channel_margin_tail_score * 0.10
        + channel_tail_shortfall_score * 0.10
        + operating_system_readiness_score * 0.18
        + operating_health_score * 0.12
        + data_contract_score * 0.12
        + experiment_confidence_score * 0.10
        + scale_control_score * 0.10
        + channel_stress_robustness_score * 0.15
        + channel_gate_flip_score * 0.08
        + stress_robustness * 0.30
        - max(operating_proxy_flag_count - 1.0, 0.0) * 0.04
        - drawdown * 0.75
    )
    return round(composite, 6)


def _build_candidate_params(
    search_space: dict[str, list[float]],
    *,
    max_candidates: int,
    seed: int,
) -> list[dict[str, float]]:
    keys = list(search_space.keys())
    total_candidates = 1
    for key in keys:
        total_candidates *= max(1, len(search_space[key]))
    if total_candidates <= max_candidates:
        return [dict(zip(keys, values)) for values in product(*(search_space[key] for key in keys))]

    rng = random.Random(seed)
    sampled: list[dict[str, float]] = []
    seen: set[tuple[tuple[str, float], ...]] = set()

    anchors = [
        {key: values[0] for key, values in search_space.items()},
        {key: values[-1] for key, values in search_space.items()},
    ]
    midpoint = {
        key: values[min(len(values) // 2, len(values) - 1)]
        for key, values in search_space.items()
    }
    anchors.append(midpoint)

    for candidate in anchors:
        signature = tuple(sorted(candidate.items()))
        if signature not in seen:
            sampled.append(candidate)
            seen.add(signature)

    while len(sampled) < max_candidates:
        candidate = {key: rng.choice(search_space[key]) for key in keys}
        signature = tuple(sorted(candidate.items()))
        if signature in seen:
            continue
        sampled.append(candidate)
        seen.add(signature)
    return sampled


def optimize_gate_thresholds(
    panel_rows: list[dict[str, str | float]],
    *,
    output_dir: str | Path,
    search_space: dict[str, list[float]] | None = None,
    optimization_metric: str = "composite_score",
    train_ratio: float = 0.7,
    initial_capital: float = 1_000_000,
    simulations: int = 800,
    seed: int = 42,
    enable_stress_test: bool = True,
    max_candidates: int = 256,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    search_space = search_space or {
        "min_factor_score": [0.55, 0.65],
        "max_loss_probability": [0.10, 0.15],
        "min_profit_p50": [0.0, 2.0, 4.0],
        "min_margin_p50_ratio": [0.18, 0.22],
        "max_volatility": [0.20, 0.24],
        "min_governance_readiness_score": [0.6, 0.7],
        "min_localization_governance_score": [0.6, 0.75],
        "min_control_tower_score": [0.65, 0.75],
        "min_master_data_health_score": [0.75, 0.85],
        "min_audit_trace_score": [0.75, 0.85],
        "min_decision_gate_control_score": [0.7, 0.8],
        "min_forecast_backtest_score": [0.55, 0.65],
        "max_forecast_mape": [0.15, 0.22],
        "min_signal_regime_score": [0.45, 0.55],
        "min_signal_seasonality_confidence_score": [0.2, 0.35],
        "max_signal_spectral_entropy": [0.75, 0.9],
        "max_signal_approximate_entropy": [0.25, 0.35],
        "min_drift_score": [0.55, 0.7],
        "max_drift_risk_score": [0.35, 0.45],
        "max_calibration_brier_score": [0.12, 0.2],
        "min_threshold_alignment_ratio": [0.85, 1.0],
        "min_gate_consistency_ratio": [0.85, 1.0],
        "max_supply_tail_risk_score": [0.45, 0.55],
        "max_supply_margin_floor_breach_probability": [0.18, 0.25],
        "min_supply_optimizer_feasible_ratio": [0.25, 0.4],
        "min_supply_execution_confidence_score": [0.55, 0.65],
        "min_channel_portfolio_readiness_score": [0.45, 0.55],
        "min_channel_portfolio_resilience_score": [0.55, 0.7],
        "min_channel_execution_friction_factor": [0.3, 0.4],
        "min_channel_scale_readiness_score": [0.45, 0.55],
        "min_channel_optimizer_feasible_ratio": [0.25, 0.4],
        "min_channel_stress_robustness_score": [0.6, 0.75],
        "max_channel_gate_flip_count": [0.0, 1.0],
        "max_channel_loss_probability_weighted": [0.12, 0.2],
        "min_channel_margin_rate_var_95": [0.015, 0.03],
        "min_channel_margin_rate_es_95": [0.005, 0.01],
        "max_channel_tail_shortfall_severity": [0.04, 0.08],
        "min_operating_system_readiness_score": [0.5, 0.6],
        "min_operating_health_score": [0.5, 0.6],
        "min_data_contract_score": [0.55, 0.65],
        "min_experiment_confidence_score": [0.45, 0.55],
        "min_scale_control_score": [0.5, 0.6],
        "max_operating_proxy_flag_count": [2.0, 4.0],
        "max_positions_per_period": [2, 3],
    }

    ordered_dates = sorted({str(row["as_of_date"]) for row in panel_rows})
    split_index = max(1, int(len(ordered_dates) * train_ratio))
    train_dates = set(ordered_dates[:split_index])
    test_dates = set(ordered_dates[split_index:])
    train_rows = [row for row in panel_rows if str(row["as_of_date"]) in train_dates]
    test_rows = [row for row in panel_rows if str(row["as_of_date"]) in test_dates]

    best_candidate: dict[str, object] | None = None
    candidate_rows: list[dict[str, object]] = []

    for gate_params in _build_candidate_params(search_space, max_candidates=max_candidates, seed=seed):
        train_result = run_walk_forward_backtest(
            train_rows,
            initial_capital=initial_capital,
            simulations=simulations,
            seed=seed,
            gate_params=gate_params,
        )
        train_stress_summary = (
            run_stress_suite(
                train_rows,
                gate_params=gate_params,
                initial_capital=initial_capital,
                simulations=max(300, simulations // 2),
                seed=seed + 3000,
            )
            if enable_stress_test
            else None
        )
        if optimization_metric == "composite_score":
            score = _composite_score(train_result["summary"], train_stress_summary)
        else:
            score = float(train_result["summary"].get(optimization_metric, 0.0))
        candidate_payload = {
            "gate_params": gate_params,
            "train_summary": train_result["summary"],
            "train_stress_summary": train_stress_summary,
            "train_score": score,
        }
        candidate_rows.append(candidate_payload)
        if best_candidate is None or score > float(best_candidate["train_score"]):
            best_candidate = candidate_payload

    if best_candidate is None:
        raise ValueError("No optimization candidates were generated")

    test_result = run_walk_forward_backtest(
        test_rows,
        initial_capital=initial_capital,
        simulations=simulations,
        seed=seed + 1000,
        gate_params=best_candidate["gate_params"],
    )
    test_stress_summary = (
        run_stress_suite(
            test_rows,
            gate_params=best_candidate["gate_params"],
            initial_capital=initial_capital,
            simulations=max(300, simulations // 2),
            seed=seed + 5000,
        )
        if enable_stress_test
        else None
    )
    test_score = (
        _composite_score(test_result["summary"], test_stress_summary)
        if optimization_metric == "composite_score"
        else float(test_result["summary"].get(optimization_metric, 0.0))
    )
    payload = {
        "optimizer": "optuna" if get_optuna_status()["available"] else "grid_search_fallback",
        "optimization_metric": optimization_metric,
        "search_space": search_space,
        "max_candidates": max_candidates,
        "best_gate_params": best_candidate["gate_params"],
        "train_summary": best_candidate["train_summary"],
        "train_stress_summary": best_candidate["train_stress_summary"],
        "train_score": best_candidate["train_score"],
        "test_summary": test_result["summary"],
        "test_stress_summary": test_stress_summary,
        "test_score": test_score,
        "candidate_count": len(candidate_rows),
    }

    write_json(output_dir / "strategy_optimization.json", payload)
    write_json(output_dir / "strategy_optimization_candidates.json", {"candidates": candidate_rows})
    log_tracking_payload(
        output_dir / "strategy_optimization_mlflow.json",
        run_name="decision_os_backtest_optimization",
        params=best_candidate["gate_params"],
        metrics={
            "train_alpha": best_candidate["train_summary"]["alpha"],
            "test_alpha": test_result["summary"]["alpha"],
            "train_composite_score": best_candidate["train_score"],
            "test_composite_score": test_score,
            "train_hit_rate": best_candidate["train_summary"]["decision_hit_rate"],
            "test_hit_rate": test_result["summary"]["decision_hit_rate"],
            "train_forecast_backtest_score": best_candidate["train_summary"]["average_forecast_backtest_score"],
            "test_forecast_backtest_score": test_result["summary"]["average_forecast_backtest_score"],
            "train_signal_regime_score": best_candidate["train_summary"]["average_signal_regime_score"],
            "test_signal_regime_score": test_result["summary"]["average_signal_regime_score"],
            "train_signal_seasonality_confidence_score": best_candidate["train_summary"]["average_signal_seasonality_confidence_score"],
            "test_signal_seasonality_confidence_score": test_result["summary"]["average_signal_seasonality_confidence_score"],
            "train_calibration_brier_score": best_candidate["train_summary"]["average_calibration_brier_score"],
            "test_calibration_brier_score": test_result["summary"]["average_calibration_brier_score"],
            "train_governance_readiness_score": best_candidate["train_summary"]["average_governance_readiness_score"],
            "test_governance_readiness_score": test_result["summary"]["average_governance_readiness_score"],
            "train_control_tower_score": best_candidate["train_summary"]["average_control_tower_score"],
            "test_control_tower_score": test_result["summary"]["average_control_tower_score"],
            "train_supply_tail_risk_score": best_candidate["train_summary"]["average_supply_tail_risk_score"],
            "test_supply_tail_risk_score": test_result["summary"]["average_supply_tail_risk_score"],
            "train_supply_feasible_ratio": best_candidate["train_summary"]["average_supply_optimizer_feasible_ratio"],
            "test_supply_feasible_ratio": test_result["summary"]["average_supply_optimizer_feasible_ratio"],
            "train_channel_resilience_score": best_candidate["train_summary"]["average_channel_portfolio_resilience_score"],
            "test_channel_resilience_score": test_result["summary"]["average_channel_portfolio_resilience_score"],
            "train_channel_feasible_ratio": best_candidate["train_summary"]["average_channel_optimizer_feasible_ratio"],
            "test_channel_feasible_ratio": test_result["summary"]["average_channel_optimizer_feasible_ratio"],
            "train_channel_stress_robustness_score": best_candidate["train_summary"]["average_channel_stress_robustness_score"],
            "test_channel_stress_robustness_score": test_result["summary"]["average_channel_stress_robustness_score"],
            "train_channel_tail_shortfall_severity": best_candidate["train_summary"]["average_channel_tail_shortfall_severity"],
            "test_channel_tail_shortfall_severity": test_result["summary"]["average_channel_tail_shortfall_severity"],
            "train_operating_system_readiness_score": best_candidate["train_summary"]["average_operating_system_readiness_score"],
            "test_operating_system_readiness_score": test_result["summary"]["average_operating_system_readiness_score"],
            "train_scale_control_score": best_candidate["train_summary"]["average_scale_control_score"],
            "test_scale_control_score": test_result["summary"]["average_scale_control_score"],
        },
    )
    return payload
