from __future__ import annotations

from typing import Any, Generator

from backend.capital_engine.capital_allocator import compute_capital_state
from backend.capital_engine.risk_monitor import build_risk_state
from backend.factor_layer.factor_engine import compute_market_factor
from backend.field_layer.field_loader import load_sample_market_fields
from backend.gate_engine.gate_engine import evaluate_market_gate
from backend.integrations.quant_bridge import load_quant_bridge_bundle
from backend.model_layer.monte_carlo import run_profit_simulation
from backend.portfolio_engine.portfolio_optimizer import rank_portfolio_rows


def get_db_session() -> Generator:
    from database.connection import session_scope

    with session_scope() as session:
        yield session


def get_current_tenant_id(claims: dict[str, Any]) -> str:
    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise ValueError("tenant_id is missing from claims")
    return tenant_id


def build_market_snapshot() -> dict[str, Any]:
    bridge_bundle = load_quant_bridge_bundle()
    field_data = bridge_bundle.get("field_data_proxy") if bridge_bundle else load_sample_market_fields()
    factor_score = (
        float(bridge_bundle["gate_inputs"]["integrated_factor_score"])
        if bridge_bundle
        else compute_market_factor(field_data)
    )
    model_outputs = run_profit_simulation(field_data)
    capital_state = compute_capital_state(total=2_000_000, allocated=1_200_000)
    risk_state = build_risk_state(max_loss_probability=0.3, max_drawdown=0.2)
    required_capital = 500_000
    candidate_features = {
        "volatility": float(field_data.get("volatility", 0.2)),
        "hhi": float(field_data.get("HHI", 2000)),
    }
    thresholds = None
    if bridge_bundle:
        gate_inputs = bridge_bundle.get("gate_inputs", {})
        required_capital = min(
            500_000,
            max(80_000, float(field_data.get("TAM", 0.0)) * 0.0025),
        )
        candidate_features.update(
            {
                "governance_readiness_score": float(gate_inputs.get("governance_readiness_score", 0.0)),
                "localization_governance_score": float(gate_inputs.get("localization_governance_score", 0.0)),
                "control_tower_score": float(gate_inputs.get("control_tower_score", 0.0)),
                "master_data_health_score": float(gate_inputs.get("master_data_health_score", 0.0)),
                "audit_trace_score": float(gate_inputs.get("audit_trace_score", 0.0)),
                "decision_gate_control_score": float(gate_inputs.get("decision_gate_control_score", 0.0)),
                "forecast_backtest_score": float(gate_inputs.get("forecast_backtest_score", 0.0)),
                "forecast_mape": float(gate_inputs.get("forecast_mape", 1.0)),
                "signal_regime_score": float(gate_inputs.get("signal_regime_score", 0.0)),
                "signal_seasonality_confidence_score": float(
                    gate_inputs.get("signal_seasonality_confidence_score", 0.0)
                ),
                "signal_spectral_entropy": float(gate_inputs.get("signal_spectral_entropy", 1.0)),
                "signal_approximate_entropy": float(gate_inputs.get("signal_approximate_entropy", 1.0)),
                "drift_score": float(gate_inputs.get("drift_score", 0.0)),
                "drift_risk_score": float(gate_inputs.get("drift_risk_score", 1.0)),
                "calibration_brier_score": float(gate_inputs.get("calibration_brier_score", 1.0)),
                "threshold_alignment_ratio": float(gate_inputs.get("threshold_alignment_ratio", 0.0)),
                "gate_consistency_ratio": float(gate_inputs.get("gate_consistency_ratio", 0.0)),
                "supply_tail_risk_score": float(gate_inputs.get("supply_tail_risk_score", 1.0)),
                "supply_loss_probability": float(gate_inputs.get("supply_loss_probability", 1.0)),
                "supply_margin_floor_breach_probability": float(
                    gate_inputs.get("supply_margin_floor_breach_probability", 1.0)
                ),
                "supply_optimizer_feasible_ratio": float(gate_inputs.get("supply_optimizer_feasible_ratio", 0.0)),
                "supply_execution_confidence_score": float(
                    gate_inputs.get("supply_execution_confidence_score", 0.0)
                ),
                "supply_optimizer_gate_pass": float(gate_inputs.get("supply_optimizer_gate_pass", 0.0)),
                "channel_portfolio_readiness_score": float(gate_inputs.get("channel_portfolio_readiness_score", 0.0)),
                "channel_portfolio_resilience_score": float(
                    gate_inputs.get("channel_portfolio_resilience_score", 0.0)
                ),
                "channel_execution_friction_factor": float(
                    gate_inputs.get("channel_execution_friction_factor", 0.0)
                ),
                "channel_scale_readiness_score": float(gate_inputs.get("channel_scale_readiness_score", 0.0)),
                "channel_optimizer_feasible_ratio": float(
                    gate_inputs.get("channel_optimizer_feasible_ratio", 0.0)
                ),
                "channel_optimizer_gate_pass": float(gate_inputs.get("channel_optimizer_gate_pass", 0.0)),
                "channel_risk_adjusted_profit": float(gate_inputs.get("channel_risk_adjusted_profit", 0.0)),
                "channel_stress_robustness_score": float(
                    gate_inputs.get("channel_stress_robustness_score", 0.0)
                ),
                "channel_gate_flip_count": float(gate_inputs.get("channel_gate_flip_count", 0.0)),
                "channel_loss_probability_weighted": float(
                    gate_inputs.get("channel_loss_probability_weighted", 1.0)
                ),
                "channel_margin_rate_var_95": float(gate_inputs.get("channel_margin_rate_var_95", 0.0)),
                "channel_margin_rate_es_95": float(gate_inputs.get("channel_margin_rate_es_95", 0.0)),
                "channel_tail_shortfall_severity": float(
                    gate_inputs.get("channel_tail_shortfall_severity", 1.0)
                ),
                "channel_roi_sharpe_like": float(gate_inputs.get("channel_roi_sharpe_like", 0.0)),
                "operating_system_readiness_score": float(gate_inputs.get("operating_system_readiness_score", 0.0)),
                "operating_health_score": float(gate_inputs.get("operating_health_score", 0.0)),
                "data_contract_score": float(gate_inputs.get("data_contract_score", 0.0)),
                "experiment_confidence_score": float(gate_inputs.get("experiment_confidence_score", 0.0)),
                "scale_control_score": float(gate_inputs.get("scale_control_score", 0.0)),
                "operating_proxy_flag_count": float(gate_inputs.get("operating_proxy_flag_count", 0.0)),
            }
        )
        thresholds = {
            "min_factor_score": 0.55,
            "max_loss_probability": 0.15,
            "min_profit_p50": 0.0,
            "max_volatility": 0.25,
            "max_hhi": 2500,
            "min_governance_readiness_score": 0.65,
            "min_localization_governance_score": 0.7,
            "min_control_tower_score": 0.7,
            "min_master_data_health_score": 0.8,
            "min_audit_trace_score": 0.8,
            "min_decision_gate_control_score": 0.75,
            "min_forecast_backtest_score": 0.55,
            "max_forecast_mape": 0.20,
            "min_signal_regime_score": 0.5,
            "min_signal_seasonality_confidence_score": 0.2,
            "max_signal_spectral_entropy": 0.8,
            "max_signal_approximate_entropy": 0.35,
            "min_drift_score": 0.55,
            "max_drift_risk_score": 0.45,
            "max_supply_tail_risk_score": 0.55,
            "max_supply_loss_probability": 0.18,
            "max_supply_margin_floor_breach_probability": 0.25,
            "min_supply_optimizer_feasible_ratio": 0.25,
            "min_supply_execution_confidence_score": 0.6,
            "min_supply_optimizer_gate_pass": 1.0,
            "min_channel_portfolio_readiness_score": 0.45,
            "min_channel_portfolio_resilience_score": 0.55,
            "min_channel_execution_friction_factor": 0.35,
            "min_channel_scale_readiness_score": 0.5,
            "min_channel_optimizer_feasible_ratio": 0.25,
            "min_channel_optimizer_gate_pass": 1.0,
            "min_channel_stress_robustness_score": 0.65,
            "max_channel_gate_flip_count": 1.0,
            "max_channel_loss_probability_weighted": 0.2,
            "min_channel_margin_rate_var_95": 0.015,
            "min_channel_margin_rate_es_95": 0.005,
            "max_channel_tail_shortfall_severity": 0.08,
            "min_operating_system_readiness_score": 0.55,
            "min_operating_health_score": 0.55,
            "min_data_contract_score": 0.6,
            "min_experiment_confidence_score": 0.5,
            "min_scale_control_score": 0.55,
            "max_operating_proxy_flag_count": 4.0,
        }
    decision = evaluate_market_gate(
        factor_score=factor_score,
        model_outputs=model_outputs,
        capital_state=capital_state,
        risk_state=risk_state,
        required_capital=required_capital,
        candidate_features=candidate_features,
        thresholds=thresholds,
    )
    portfolio_rows = rank_portfolio_rows(
        [
            {"channel": "Amazon", "score": model_outputs["profit_p50"] / 32, "allocated_capital": 240000},
            {"channel": "DTC", "score": model_outputs["profit_p50"] / 29, "allocated_capital": 180000},
            {"channel": "TikTok Shop", "score": model_outputs["profit_p50"] / 35, "allocated_capital": 140000},
        ]
    )
    return {
        "field_data": field_data,
        "factor_score": factor_score,
        "model_outputs": model_outputs,
        "capital_state": capital_state,
        "risk_state": risk_state,
        "required_capital": required_capital,
        "decision": decision,
        "portfolio_rows": portfolio_rows,
        "candidate_features": candidate_features,
        "gate_thresholds": thresholds or {},
        "source_mode": "quant_bridge" if bridge_bundle else "sample_market_fields",
        "bridge_bundle": bridge_bundle,
    }
