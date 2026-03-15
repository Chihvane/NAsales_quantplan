from __future__ import annotations

from pathlib import Path

from .io_utils import write_csv_rows, write_json


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _signal_regime_score(signal_regime: str) -> float:
    normalized = str(signal_regime or "").strip().lower()
    if normalized == "seasonal":
        return 0.85
    if normalized == "trend":
        return 0.7
    if normalized == "noisy":
        return 0.35
    return 0.5


def _extract_factor_rows(
    report: dict,
    *,
    tenant_id: str,
    as_of_date: str,
    module: str,
) -> list[dict[str, str]]:
    rows = []
    for factor_id, payload in sorted(report.get("factor_snapshots", {}).items()):
        rows.append(
            {
                "tenant_id": tenant_id,
                "as_of_date": as_of_date,
                "module": module,
                "factor_id": factor_id,
                "factor_label": str(payload.get("label", "")),
                "value": f"{_safe_float(payload.get('value')):.6f}",
                "source_section": str(payload.get("source_section", "")),
            }
        )
    return rows


def _manual_factor_row(
    *,
    tenant_id: str,
    as_of_date: str,
    module: str,
    factor_id: str,
    factor_label: str,
    value: object,
    source_section: str,
) -> dict[str, str]:
    return {
        "tenant_id": tenant_id,
        "as_of_date": as_of_date,
        "module": module,
        "factor_id": factor_id,
        "factor_label": factor_label,
        "value": f"{_safe_float(value):.6f}",
        "source_section": source_section,
    }


def build_decision_os_bridge_bundle(
    part1_report: dict,
    part2_report: dict,
    part3_report: dict | None = None,
    part4_report: dict | None = None,
    part0_report: dict | None = None,
    horizontal_report: dict | None = None,
    part5_report: dict | None = None,
    *,
    tenant_id: str = "TENANT-DEMO",
    as_of_date: str = "",
) -> dict:
    as_of_date = as_of_date or str(part1_report.get("metadata", {}).get("generated_at", ""))[:10]
    part1_factors = part1_report.get("factor_snapshots", {})
    part2_factors = part2_report.get("factor_snapshots", {})

    part1_section_13 = part1_report.get("sections", {}).get("1.3", {}).get("metrics", {})
    part1_section_11 = part1_report.get("sections", {}).get("1.1", {}).get("metrics", {})
    part1_section_14 = part1_report.get("sections", {}).get("1.4", {}).get("metrics", {})
    part2_section_22 = part2_report.get("sections", {}).get("2.2", {}).get("metrics", {})
    advanced_time_series = part1_section_11.get("advanced_time_series", {})
    spectral_features = advanced_time_series.get("spectral_features", {})
    forecast_engine = part1_report.get("part1_forecast_engine", {})
    drift_report = part1_report.get("part1_drift_report", {})
    calibration_report = part1_report.get("part1_calibration_report", {})
    market_destination_engine = part1_report.get("part1_market_destination_engine", {})
    part3_report = part3_report or {}
    part3_section_35 = part3_report.get("sections", {}).get("3.5", {}).get("metrics", {})
    part3_section_37 = part3_report.get("sections", {}).get("3.7", {}).get("metrics", {})
    part3_risk_metrics = part3_section_35.get("part3_risk_metrics", {})
    part3_optimizer = part3_section_37.get("optimizer", {})
    part4_report = part4_report or {}
    part4_factors = part4_report.get("factor_snapshots", {})
    part4_section_45 = part4_report.get("sections", {}).get("4.5", {}).get("metrics", {})
    part4_section_47 = part4_report.get("sections", {}).get("4.7", {}).get("metrics", {})
    part4_channel_performance = part4_section_45.get("channel_performance_metrics", {})
    part4_monte_carlo = part4_section_45.get("monte_carlo", {})
    part4_monte_carlo_overall = part4_monte_carlo.get("overall", {})
    part4_tail_risk = part4_monte_carlo_overall.get("tail_risk", {})
    part4_risk_adjusted = part4_monte_carlo_overall.get("risk_adjusted", {})
    part4_stress_suite = part4_section_45.get("stress_suite", {})
    part4_optimizer = part4_section_47.get("optimizer", {})
    part0_report = part0_report or {}
    part0_overview = part0_report.get("overview", {})
    part0_section_08 = part0_report.get("sections", {}).get("0.8", {}).get("metrics", {})
    horizontal_report = horizontal_report or {}
    horizontal_section_h1 = horizontal_report.get("sections", {}).get("H1", {}).get("metrics", {})
    horizontal_section_h2 = horizontal_report.get("sections", {}).get("H2", {}).get("metrics", {})
    horizontal_section_h3 = horizontal_report.get("sections", {}).get("H3", {}).get("metrics", {})
    horizontal_overview = horizontal_report.get("overview", {})
    part5_report = part5_report or {}
    part5_factors = part5_report.get("factor_snapshots", {})
    part5_section_51 = part5_report.get("sections", {}).get("5.1", {}).get("metrics", {})
    part5_section_52 = part5_report.get("sections", {}).get("5.2", {}).get("metrics", {})
    part5_section_56 = part5_report.get("sections", {}).get("5.6", {}).get("metrics", {})
    part5_section_57 = part5_report.get("sections", {}).get("5.7", {}).get("metrics", {})
    part5_data_contract = part5_report.get("overview", {}).get("data_contract", {})
    part5_confidence_band = part5_report.get("confidence_band", {})

    forecast_backtest = forecast_engine.get("backtest", {})
    lead_lag_stability = forecast_engine.get("lead_lag_stability", {})
    event_window_stability = forecast_engine.get("event_window_stability", {})
    drift_summary = drift_report.get("summary", {})
    factor_drift_report = drift_report.get("factor_drift_report", {})
    source_drift_report = drift_report.get("source_drift_report", {})
    calibration_summary = calibration_report.get("summary", {})
    market_destination_summary = market_destination_engine.get("summary", {})
    governance_readiness_score = round(
        _safe_float(part0_overview.get("decision_score"))
        or _safe_float(part0_section_08.get("localization_governance_score")),
        4,
    )
    localization_governance_score = round(
        _safe_float(part0_section_08.get("localization_governance_score")),
        4,
    )
    control_tower_score = round(
        _safe_float(horizontal_overview.get("decision_score"))
        or (
            _safe_float(horizontal_section_h1.get("master_data_health_score")) * 0.34
            + _safe_float(horizontal_section_h2.get("audit_trace_score")) * 0.33
            + _safe_float(horizontal_section_h3.get("decision_gate_control_score")) * 0.33
        ),
        4,
    )
    master_data_health_score = round(_safe_float(horizontal_section_h1.get("master_data_health_score")), 4)
    audit_trace_score = round(_safe_float(horizontal_section_h2.get("audit_trace_score")), 4)
    decision_gate_control_score = round(_safe_float(horizontal_section_h3.get("decision_gate_control_score")), 4)
    operating_health_score = round(
        _safe_float(part5_factors.get("FAC-OPERATING-HEALTH", {}).get("value"))
        or _safe_float(part5_section_51.get("operating_health_score")),
        4,
    )
    data_contract_score = round(
        _safe_float(part5_factors.get("FAC-DATA-CONTRACT", {}).get("value"))
        or _safe_float(part5_section_52.get("data_coverage_score")),
        4,
    )
    experiment_confidence_score = round(
        _safe_float(part5_factors.get("FAC-EXPERIMENT-CONFIDENCE", {}).get("value"))
        or _safe_float(part5_section_56.get("causal_confidence_score")),
        4,
    )
    scale_control_score = round(
        _safe_float(part5_factors.get("FAC-SCALE-CONTROL", {}).get("value"))
        or _safe_float(part5_section_57.get("scale_readiness_score")),
        4,
    )
    part5_proxy_flag_count = float(
        len(part5_confidence_band.get("proxy_usage_flags", [])) + len(part5_data_contract.get("model_blockers", []))
    )
    operating_system_readiness_score = round(
        _safe_float(part5_factors.get("FAC-OPERATING-HEALTH", {}).get("value")) * 0.26
        + _safe_float(part5_factors.get("FAC-DATA-CONTRACT", {}).get("value")) * 0.16
        + _safe_float(part5_factors.get("FAC-GROWTH-LEVERAGE", {}).get("value")) * 0.10
        + _safe_float(part5_factors.get("FAC-MARGIN-PROTECTION", {}).get("value")) * 0.12
        + _safe_float(part5_factors.get("FAC-CASH-DISCIPLINE", {}).get("value")) * 0.12
        + _safe_float(part5_factors.get("FAC-EXPERIMENT-CONFIDENCE", {}).get("value")) * 0.10
        + _safe_float(part5_factors.get("FAC-SCALE-CONTROL", {}).get("value")) * 0.14,
        4,
    )

    market_entry_readiness_score = round(
        _safe_float(part1_factors.get("FAC-MARKET-ATTRACT", {}).get("value")) * 0.30
        + _safe_float(part1_factors.get("FAC-DEMAND-STABILITY", {}).get("value")) * 0.20
        + _safe_float(part1_factors.get("FAC-CUSTOMER-FIT", {}).get("value")) * 0.10
        + _safe_float(part1_factors.get("FAC-CHANNEL-EFFICIENCY", {}).get("value")) * 0.15
        + _safe_float(part1_factors.get("FAC-CHANNEL-RISK", {}).get("value")) * 0.10
        + _safe_float(part1_factors.get("FAC-PRICE-REALIZATION", {}).get("value")) * 0.15,
        4,
    )
    product_viability_score = round(
        _safe_float(part2_factors.get("FAC-COMPETITION-HEADROOM", {}).get("value")) * 0.30
        + _safe_float(part2_factors.get("FAC-PRICING-FIT", {}).get("value")) * 0.30
        + _safe_float(part2_factors.get("FAC-WHITESPACE-DEPTH", {}).get("value")) * 0.20
        + _safe_float(part2_factors.get("FAC-SHELF-STABILITY", {}).get("value")) * 0.20,
        4,
    )
    channel_portfolio_readiness_score = round(
        _safe_float(part4_factors.get("FAC-CHANNEL-FIT", {}).get("value")) * 0.15
        + _safe_float(part4_factors.get("FAC-TRAFFIC-EFFICIENCY", {}).get("value")) * 0.10
        + _safe_float(part4_factors.get("FAC-UNIT-ECONOMICS", {}).get("value")) * 0.20
        + _safe_float(part4_factors.get("FAC-PORTFOLIO-RESILIENCE", {}).get("value")) * 0.25
        + _safe_float(part4_factors.get("FAC-EXECUTION-FRICTION", {}).get("value")) * 0.10
        + _safe_float(part4_factors.get("FAC-SCALE-READINESS", {}).get("value")) * 0.20,
        4,
    )
    integrated_factor_score = round(
        market_entry_readiness_score * 0.32
        + product_viability_score * 0.22
        + governance_readiness_score * 0.12
        + control_tower_score * 0.12
        + operating_system_readiness_score * 0.22,
        4,
    )

    average_realized_price = _safe_float(part2_section_22.get("average_realized_price"))
    price_realization_rate = _safe_float(part2_section_22.get("price_realization_rate"), default=0.9)
    landed_cost_proxy = round(max(average_realized_price * 0.55, 1.0), 2)
    platform_fee_proxy = round(max(average_realized_price * 0.12, 1.0), 2)

    field_data_proxy = {
        "TAM": round(_safe_float(part1_section_13.get("top_down", {}).get("sam")), 2),
        "CAGR": round(_safe_float(part1_section_11.get("trend", {}).get("cagr")), 4),
        "HHI": round(_safe_float(part1_section_13.get("bottom_up", {}).get("hhi")), 2),
        "volatility": round(_safe_float(part1_section_11.get("trend", {}).get("heat_volatility_coefficient")), 4),
        "expected_price": round(average_realized_price, 2),
        "landed_cost": landed_cost_proxy,
        "platform_fee": platform_fee_proxy,
    }

    factor_rows = _extract_factor_rows(part1_report, tenant_id=tenant_id, as_of_date=as_of_date, module="part1")
    factor_rows.extend(_extract_factor_rows(part2_report, tenant_id=tenant_id, as_of_date=as_of_date, module="part2"))
    if part0_report:
        factor_rows.extend(
            [
                _manual_factor_row(
                    tenant_id=tenant_id,
                    as_of_date=as_of_date,
                    module="part0",
                    factor_id="FAC-GOVERNANCE-READINESS",
                    factor_label="治理内核就绪因子",
                    value=governance_readiness_score,
                    source_section="0.1-0.8",
                ),
                _manual_factor_row(
                    tenant_id=tenant_id,
                    as_of_date=as_of_date,
                    module="part0",
                    factor_id="FAC-LOCALIZATION-GOVERNANCE",
                    factor_label="本地化治理因子",
                    value=localization_governance_score,
                    source_section="0.8",
                ),
            ]
        )
    if horizontal_report:
        factor_rows.extend(
            [
                _manual_factor_row(
                    tenant_id=tenant_id,
                    as_of_date=as_of_date,
                    module="horizontal",
                    factor_id="FAC-CONTROL-TOWER",
                    factor_label="横向控制塔因子",
                    value=control_tower_score,
                    source_section="H1-H3",
                ),
                _manual_factor_row(
                    tenant_id=tenant_id,
                    as_of_date=as_of_date,
                    module="horizontal",
                    factor_id="FAC-AUDIT-TRACEABILITY",
                    factor_label="审计追溯因子",
                    value=audit_trace_score,
                    source_section="H2",
                ),
            ]
        )
    if part3_report:
        supply_factor_rows = [
            {
                "tenant_id": tenant_id,
                "as_of_date": as_of_date,
                "module": "part3",
                "factor_id": "FAC-SUPPLY-TAIL-RISK",
                "factor_label": "供应链尾部风险因子",
                "value": f"{max(0.0, 1 - _safe_float(part3_risk_metrics.get('tail_risk_score'))):.6f}",
                "source_section": "3.5-3.6",
            },
            {
                "tenant_id": tenant_id,
                "as_of_date": as_of_date,
                "module": "part3",
                "factor_id": "FAC-SUPPLY-EXECUTION-CONFIDENCE",
                "factor_label": "供应链执行信心因子",
                "value": f"{_safe_float(part3_section_37.get('execution_confidence_score')):.6f}",
                "source_section": "3.7",
            },
            {
                "tenant_id": tenant_id,
                "as_of_date": as_of_date,
                "module": "part3",
                "factor_id": "FAC-SUPPLY-FEASIBILITY",
                "factor_label": "供应链可行性因子",
                "value": f"{_safe_float(part3_optimizer.get('feasible_ratio')):.6f}",
                "source_section": "3.7",
            },
        ]
        factor_rows.extend(supply_factor_rows)
    if part4_report:
        factor_rows.extend(_extract_factor_rows(part4_report, tenant_id=tenant_id, as_of_date=as_of_date, module="part4"))
    if part5_report:
        factor_rows.extend(_extract_factor_rows(part5_report, tenant_id=tenant_id, as_of_date=as_of_date, module="part5"))

    return {
        "tenant_id": tenant_id,
        "as_of_date": as_of_date,
        "report_refs": {
            "part0_report_id": part0_report.get("metadata", {}).get("report_id") if part0_report else "",
            "horizontal_report_id": horizontal_report.get("metadata", {}).get("report_id") if horizontal_report else "",
            "part1_report_id": part1_report.get("metadata", {}).get("report_id"),
            "part2_report_id": part2_report.get("metadata", {}).get("report_id"),
            "part3_report_id": part3_report.get("metadata", {}).get("report_id") if part3_report else "",
            "part4_report_id": part4_report.get("metadata", {}).get("report_id") if part4_report else "",
            "part5_report_id": part5_report.get("metadata", {}).get("report_id") if part5_report else "",
        },
        "field_data_proxy": field_data_proxy,
        "gate_inputs": {
            "governance_readiness_score": governance_readiness_score,
            "localization_governance_score": localization_governance_score,
            "control_tower_score": control_tower_score,
            "master_data_health_score": master_data_health_score,
            "audit_trace_score": audit_trace_score,
            "decision_gate_control_score": decision_gate_control_score,
            "market_entry_readiness_score": market_entry_readiness_score,
            "product_viability_score": product_viability_score,
            "channel_portfolio_readiness_score": channel_portfolio_readiness_score,
            "operating_system_readiness_score": operating_system_readiness_score,
            "operating_health_score": operating_health_score,
            "data_contract_score": data_contract_score,
            "experiment_confidence_score": experiment_confidence_score,
            "scale_control_score": scale_control_score,
            "operating_proxy_flag_count": round(part5_proxy_flag_count, 4),
            "integrated_factor_score": integrated_factor_score,
            "forecast_backtest_score": round(_safe_float(forecast_backtest.get("score")), 4),
            "forecast_mape": round(_safe_float(forecast_backtest.get("mape")), 4),
            "signal_regime_score": round(
                _signal_regime_score(advanced_time_series.get("signal_regime", "")),
                4,
            ),
            "signal_regime": str(advanced_time_series.get("signal_regime", "")),
            "signal_seasonality_confidence_score": round(
                _safe_float(spectral_features.get("seasonality_confidence_score")),
                4,
            ),
            "signal_spectral_entropy": round(_safe_float(spectral_features.get("spectral_entropy")), 4),
            "signal_approximate_entropy": round(_safe_float(advanced_time_series.get("approximate_entropy")), 4),
            "lead_lag_stability_score": round(_safe_float(lead_lag_stability.get("stability_score")), 4),
            "event_window_stability_score": round(_safe_float(event_window_stability.get("stability_score")), 4),
            "drift_score": round(_safe_float(drift_summary.get("drift_score")), 4),
            "drift_risk_score": round(_safe_float(factor_drift_report.get("drift_risk_score")), 4),
            "source_drift_score": round(_safe_float(source_drift_report.get("source_drift_score")), 4),
            "calibration_brier_score": round(_safe_float(calibration_summary.get("brier_score")), 4),
            "threshold_alignment_ratio": round(_safe_float(calibration_summary.get("threshold_alignment_ratio")), 4),
            "gate_consistency_ratio": round(_safe_float(calibration_summary.get("gate_consistency_ratio")), 4),
            "localized_market_selection_score": round(_safe_float(market_destination_summary.get("top_market_score")), 4),
            "market_localization_coverage_ratio": round(
                min(
                    _safe_float(market_destination_summary.get("habit_vector_coverage_ratio")) * 0.5
                    + _safe_float(market_destination_summary.get("weight_profile_coverage_ratio")) * 0.5,
                    1.0,
                ),
                4,
            ),
            "channel_dependency_score": round(
                _safe_float(part1_section_14.get("channel_dependency_score")),
                4,
            ),
            "price_realization_rate": round(price_realization_rate, 4),
            "top_sku_share": round(
                _safe_float(part2_report.get("sections", {}).get("2.1", {}).get("metrics", {}).get("top_sku_share")),
                4,
            ),
            "supply_tail_risk_score": round(_safe_float(part3_risk_metrics.get("tail_risk_score")), 4),
            "supply_loss_probability": round(_safe_float(part3_risk_metrics.get("loss_probability")), 4),
            "supply_margin_floor_breach_probability": round(
                _safe_float(part3_risk_metrics.get("margin_floor_breach_probability")),
                4,
            ),
            "supply_value_at_risk_95": round(_safe_float(part3_risk_metrics.get("value_at_risk_95")), 4),
            "supply_optimizer_feasible_ratio": round(_safe_float(part3_optimizer.get("feasible_ratio")), 4),
            "supply_execution_confidence_score": round(
                _safe_float(part3_section_37.get("execution_confidence_score")),
                4,
            ),
            "supply_optimizer_gate_pass": 1.0 if part3_optimizer.get("optimizer_gate_result") == "pass" else 0.0,
            "channel_portfolio_resilience_score": round(
                _safe_float(part4_factors.get("FAC-PORTFOLIO-RESILIENCE", {}).get("value")),
                4,
            ),
            "channel_execution_friction_factor": round(
                _safe_float(part4_factors.get("FAC-EXECUTION-FRICTION", {}).get("value")),
                4,
            ),
            "channel_scale_readiness_score": round(
                _safe_float(part4_factors.get("FAC-SCALE-READINESS", {}).get("value")),
                4,
            ),
            "channel_optimizer_feasible_ratio": round(_safe_float(part4_optimizer.get("feasible_ratio")), 4),
            "channel_optimizer_gate_pass": 1.0 if part4_optimizer.get("optimizer_gate_result") == "pass" else 0.0,
            "channel_risk_adjusted_profit": round(_safe_float(part4_optimizer.get("risk_adjusted_profit")), 4),
            "channel_stress_robustness_score": round(_safe_float(part4_stress_suite.get("robustness_score")), 4),
            "channel_gate_flip_count": round(
                _safe_float(part4_stress_suite.get("gate_flip_report", {}).get("flip_count")),
                4,
            ),
            "channel_loss_probability_weighted": round(
                _safe_float(part4_monte_carlo_overall.get("loss_probability_weighted_channels")),
                4,
            ),
            "channel_margin_rate_var_95": round(_safe_float(part4_tail_risk.get("margin_rate_var_95")), 4),
            "channel_margin_rate_es_95": round(_safe_float(part4_tail_risk.get("margin_rate_es_95")), 4),
            "channel_tail_shortfall_severity": round(
                _safe_float(part4_tail_risk.get("tail_shortfall_severity")),
                4,
            ),
            "channel_roi_sharpe_like": round(_safe_float(part4_risk_adjusted.get("roi_sharpe_like")), 4),
        },
        "part1_continuous_signals": {
            "forecast_engine": {
                "score": round(_safe_float(forecast_backtest.get("score")), 4),
                "mape": round(_safe_float(forecast_backtest.get("mape")), 4),
                "rmse": round(_safe_float(forecast_backtest.get("rmse")), 4),
                "lead_lag_stability_score": round(_safe_float(lead_lag_stability.get("stability_score")), 4),
                "event_window_stability_score": round(_safe_float(event_window_stability.get("stability_score")), 4),
            },
            "drift_report": {
                "drift_score": round(_safe_float(drift_summary.get("drift_score")), 4),
                "drift_level": str(drift_summary.get("drift_level", "")),
                "drift_risk_score": round(_safe_float(factor_drift_report.get("drift_risk_score")), 4),
                "source_drift_score": round(_safe_float(source_drift_report.get("source_drift_score")), 4),
            },
            "calibration_report": {
                "brier_score": round(_safe_float(calibration_summary.get("brier_score")), 4),
                "threshold_alignment_ratio": round(_safe_float(calibration_summary.get("threshold_alignment_ratio")), 4),
                "gate_consistency_ratio": round(_safe_float(calibration_summary.get("gate_consistency_ratio")), 4),
                "flip_candidate_count": int(_safe_float(calibration_summary.get("flip_candidate_count"))),
            },
            "advanced_time_series": {
                "signal_regime": str(advanced_time_series.get("signal_regime", "")),
                "signal_regime_score": round(
                    _signal_regime_score(advanced_time_series.get("signal_regime", "")),
                    4,
                ),
                "seasonality_confidence_score": round(
                    _safe_float(spectral_features.get("seasonality_confidence_score")),
                    4,
                ),
                "spectral_entropy": round(_safe_float(spectral_features.get("spectral_entropy")), 4),
                "approximate_entropy": round(_safe_float(advanced_time_series.get("approximate_entropy")), 4),
            },
            "market_destination": {
                "market_count": int(_safe_float(market_destination_summary.get("market_count"))),
                "top_market_code": str(market_destination_summary.get("top_market_code", "")),
                "top_market_score": round(_safe_float(market_destination_summary.get("top_market_score")), 4),
                "habit_vector_coverage_ratio": round(
                    _safe_float(market_destination_summary.get("habit_vector_coverage_ratio")),
                    4,
                ),
                "weight_profile_coverage_ratio": round(
                    _safe_float(market_destination_summary.get("weight_profile_coverage_ratio")),
                    4,
                ),
            },
        },
        "part0_governance_signals": {
            "governance": {
                "decision_signal": str(part0_overview.get("decision_signal", "")),
                "decision_score": governance_readiness_score,
                "localization_governance_score": localization_governance_score,
                "active_market_count": int(_safe_float(part0_section_08.get("active_market_count"))),
                "market_localization_coverage_ratio": round(
                    _safe_float(part0_section_08.get("habit_vector_coverage_ratio")) * 0.5
                    + _safe_float(part0_section_08.get("weight_profile_coverage_ratio")) * 0.5,
                    4,
                ),
            }
        },
        "horizontal_control_signals": {
            "control_tower": {
                "decision_signal": str(horizontal_overview.get("decision_signal", "")),
                "decision_score": control_tower_score,
                "master_data_health_score": master_data_health_score,
                "audit_trace_score": audit_trace_score,
                "decision_gate_control_score": decision_gate_control_score,
            }
        },
        "part3_supply_signals": {
            "risk_metrics": {
                "tail_risk_score": round(_safe_float(part3_risk_metrics.get("tail_risk_score")), 4),
                "loss_probability": round(_safe_float(part3_risk_metrics.get("loss_probability")), 4),
                "margin_floor_breach_probability": round(
                    _safe_float(part3_risk_metrics.get("margin_floor_breach_probability")),
                    4,
                ),
                "value_at_risk_95": round(_safe_float(part3_risk_metrics.get("value_at_risk_95")), 4),
                "expected_shortfall_95": round(_safe_float(part3_risk_metrics.get("expected_shortfall_95")), 4),
            },
            "optimizer": {
                "feasible_ratio": round(_safe_float(part3_optimizer.get("feasible_ratio")), 4),
                "optimizer_gate_result": str(part3_optimizer.get("optimizer_gate_result", "")),
                "optimizer_confidence_level": str(part3_optimizer.get("optimizer_confidence_level", "")),
                "execution_confidence_score": round(
                    _safe_float(part3_section_37.get("execution_confidence_score")),
                    4,
                ),
            },
        },
        "part4_channel_signals": {
            "performance": {
                "portfolio_resilience_score": round(
                    _safe_float(part4_factors.get("FAC-PORTFOLIO-RESILIENCE", {}).get("value")),
                    4,
                ),
                "execution_friction_factor": round(
                    _safe_float(part4_factors.get("FAC-EXECUTION-FRICTION", {}).get("value")),
                    4,
                ),
                "scale_readiness_score": round(
                    _safe_float(part4_factors.get("FAC-SCALE-READINESS", {}).get("value")),
                    4,
                ),
                "benchmark_coverage_ratio": round(
                    _safe_float(part4_channel_performance.get("benchmark_coverage_ratio")),
                    4,
                ),
            },
            "optimizer": {
                "feasible_ratio": round(_safe_float(part4_optimizer.get("feasible_ratio")), 4),
                "optimizer_gate_result": str(part4_optimizer.get("optimizer_gate_result", "")),
                "optimizer_confidence_level": str(part4_optimizer.get("optimizer_confidence_level", "")),
                "risk_adjusted_profit": round(_safe_float(part4_optimizer.get("risk_adjusted_profit")), 4),
            },
            "stress_suite": {
                "robustness_score": round(_safe_float(part4_stress_suite.get("robustness_score")), 4),
                "robustness_level": str(part4_stress_suite.get("robustness_level", "")),
                "gate_flip_count": int(_safe_float(part4_stress_suite.get("gate_flip_report", {}).get("flip_count"))),
                "scenario_count": int(_safe_float(part4_stress_suite.get("scenario_count"))),
            },
            "tail_risk": {
                "loss_probability_weighted": round(
                    _safe_float(part4_monte_carlo_overall.get("loss_probability_weighted_channels")),
                    4,
                ),
                "margin_rate_var_95": round(_safe_float(part4_tail_risk.get("margin_rate_var_95")), 4),
                "margin_rate_es_95": round(_safe_float(part4_tail_risk.get("margin_rate_es_95")), 4),
                "tail_shortfall_severity": round(
                    _safe_float(part4_tail_risk.get("tail_shortfall_severity")),
                    4,
                ),
                "roi_sharpe_like": round(_safe_float(part4_risk_adjusted.get("roi_sharpe_like")), 4),
            },
        },
        "part5_operating_signals": {
            "operating": {
                "decision_signal": str(part5_report.get("overview", {}).get("decision_signal", "")),
                "operating_health_score": operating_health_score,
                "operating_system_readiness_score": operating_system_readiness_score,
                "data_contract_score": data_contract_score,
                "experiment_confidence_score": experiment_confidence_score,
                "scale_control_score": scale_control_score,
                "confidence_label": str(part5_confidence_band.get("label", "")),
            },
            "proxy_usage_flags": sorted(set(part5_confidence_band.get("proxy_usage_flags", []))),
        },
        "proxy_flags": {
            "landed_cost_proxy": True,
            "platform_fee_proxy": True,
            "price_source": "part2_average_realized_price",
            "part5_proxy_usage_flags": sorted(set(part5_confidence_band.get("proxy_usage_flags", []))),
        },
        "factor_panel": factor_rows,
    }


def export_decision_os_bridge_bundle(
    part1_report: dict,
    part2_report: dict,
    output_dir: str | Path,
    part3_report: dict | None = None,
    part4_report: dict | None = None,
    part0_report: dict | None = None,
    horizontal_report: dict | None = None,
    part5_report: dict | None = None,
    *,
    tenant_id: str = "TENANT-DEMO",
    as_of_date: str = "",
) -> dict[str, str]:
    output_dir = Path(output_dir)
    bundle = build_decision_os_bridge_bundle(
        part1_report,
        part2_report,
        part3_report,
        part4_report,
        part0_report,
        horizontal_report,
        part5_report,
        tenant_id=tenant_id,
        as_of_date=as_of_date,
    )
    json_path = write_json(output_dir / "integrated_market_product_bundle.json", bundle)
    factor_rows = bundle["factor_panel"]
    csv_path = output_dir / "integrated_factor_panel.csv"
    write_csv_rows(
        csv_path,
        ["tenant_id", "as_of_date", "module", "factor_id", "factor_label", "value", "source_section"],
        factor_rows,
    )
    return {
        "bundle_json": str(json_path),
        "factor_panel_csv": str(csv_path),
    }
