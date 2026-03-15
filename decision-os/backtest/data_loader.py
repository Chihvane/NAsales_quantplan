from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path


def month_sequence(start_year: int, start_month: int, end_year: int, end_month: int) -> list[date]:
    months: list[date] = []
    year = start_year
    month = start_month
    while (year, month) <= (end_year, end_month):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def generate_demo_panel(seed: int = 42) -> list[dict[str, str | float]]:
    rng = random.Random(seed)
    months = month_sequence(2019, 1, 2024, 12)
    opportunities = [
        {
            "entity_id": "OPP-GEN-001",
            "segment": "Portable Generator",
            "tam": 155_000_000,
            "cagr": 0.10,
            "hhi": 2100,
            "volatility": 0.18,
            "landed_cost": 42,
            "expected_price": 82,
            "platform_fee": 9,
            "required_capital": 140_000,
        },
        {
            "entity_id": "OPP-AUTO-001",
            "segment": "Auto Parts",
            "tam": 175_000_000,
            "cagr": 0.11,
            "hhi": 2400,
            "volatility": 0.16,
            "landed_cost": 36,
            "expected_price": 74,
            "platform_fee": 8,
            "required_capital": 120_000,
        },
        {
            "entity_id": "OPP-CIGAR-001",
            "segment": "Cigar Accessories",
            "tam": 82_000_000,
            "cagr": 0.08,
            "hhi": 3000,
            "volatility": 0.22,
            "landed_cost": 19,
            "expected_price": 41,
            "platform_fee": 6,
            "required_capital": 80_000,
        },
        {
            "entity_id": "OPP-EDC-001",
            "segment": "EDC",
            "tam": 98_000_000,
            "cagr": 0.14,
            "hhi": 2600,
            "volatility": 0.20,
            "landed_cost": 26,
            "expected_price": 58,
            "platform_fee": 7,
            "required_capital": 90_000,
        },
        {
            "entity_id": "OPP-CAMP-001",
            "segment": "Camping Gear",
            "tam": 134_000_000,
            "cagr": 0.12,
            "hhi": 2200,
            "volatility": 0.19,
            "landed_cost": 31,
            "expected_price": 69,
            "platform_fee": 8,
            "required_capital": 110_000,
        },
        {
            "entity_id": "OPP-LIGHT-001",
            "segment": "Tactical Light",
            "tam": 88_000_000,
            "cagr": 0.09,
            "hhi": 2900,
            "volatility": 0.21,
            "landed_cost": 24,
            "expected_price": 52,
            "platform_fee": 7,
            "required_capital": 85_000,
        },
    ]

    rows: list[dict[str, str | float]] = []
    for month_index, month_value in enumerate(months):
        macro_shock = 0.0
        supply_shock = 0.0
        if date(2020, 3, 1) <= month_value <= date(2020, 9, 1):
            macro_shock = -0.06
            supply_shock = 0.08
        if date(2021, 6, 1) <= month_value <= date(2022, 2, 1):
            macro_shock = -0.03
            supply_shock = 0.12
        if date(2022, 6, 1) <= month_value <= date(2023, 3, 1):
            macro_shock = -0.02
            supply_shock = 0.05

        seasonal = 0.03 if month_value.month in {5, 6, 11, 12} else -0.01
        for index, opportunity in enumerate(opportunities):
            entity_bias = (index - 2) * 0.004
            tam = opportunity["tam"] * (1 + 0.002 * month_index + seasonal + rng.uniform(-0.015, 0.015))
            cagr = _clip(opportunity["cagr"] + rng.uniform(-0.012, 0.012), 0.02, 0.25)
            hhi = _clip(opportunity["hhi"] + rng.uniform(-180, 180), 1200, 4500)
            volatility = _clip(opportunity["volatility"] + rng.uniform(-0.03, 0.03), 0.08, 0.40)
            landed_cost = opportunity["landed_cost"] * (1 + supply_shock + rng.uniform(-0.06, 0.08))
            expected_price = opportunity["expected_price"] * (1 + macro_shock / 2 + rng.uniform(-0.04, 0.05))
            platform_fee = opportunity["platform_fee"] * (1 + rng.uniform(-0.03, 0.05))
            unit_margin = expected_price - landed_cost - platform_fee
            margin_rate = unit_margin / max(expected_price, 1)
            forecast_backtest_score = _clip(
                0.72
                + (opportunity["cagr"] - 0.10) * 0.8
                - (volatility - 0.16) * 0.9
                + seasonal * 0.6
                + rng.uniform(-0.05, 0.05),
                0.25,
                0.95,
            )
            signal_seasonality_confidence_score = _clip(
                0.48
                + seasonal * 3.2
                - abs(macro_shock) * 1.2
                - max(volatility - 0.18, 0.0) * 0.7
                + rng.uniform(-0.06, 0.06),
                0.02,
                0.98,
            )
            signal_spectral_entropy = _clip(
                0.44
                + abs(macro_shock) * 1.2
                + max(volatility - 0.18, 0.0) * 1.1
                - seasonal * 1.5
                + rng.uniform(-0.05, 0.05),
                0.02,
                0.98,
            )
            signal_approximate_entropy = _clip(
                0.18
                + abs(macro_shock) * 1.0
                + max(volatility - 0.18, 0.0) * 0.9
                - seasonal * 0.7
                + rng.uniform(-0.04, 0.04),
                0.01,
                0.95,
            )
            if signal_seasonality_confidence_score >= 0.32:
                signal_regime = "seasonal"
            elif signal_spectral_entropy >= 0.62 or signal_approximate_entropy >= 0.28:
                signal_regime = "noisy"
            else:
                signal_regime = "trend"
            signal_regime_score = {
                "seasonal": 0.85,
                "trend": 0.7,
                "noisy": 0.35,
            }[signal_regime]
            forecast_mape = _clip(
                0.16
                + max(volatility - 0.16, 0.0) * 0.35
                + abs(macro_shock) * 0.5
                + rng.uniform(-0.015, 0.015),
                0.04,
                0.40,
            )
            drift_score = _clip(
                0.82
                - abs(macro_shock) * 1.8
                - max(supply_shock, 0.0) * 1.2
                - max(volatility - 0.18, 0.0) * 0.6
                + rng.uniform(-0.04, 0.04),
                0.2,
                0.98,
            )
            drift_risk_score = _clip(
                1 - drift_score + rng.uniform(-0.03, 0.03),
                0.02,
                0.85,
            )
            calibration_brier_score = _clip(
                0.08
                + max(volatility - 0.15, 0.0) * 0.35
                + abs(entity_bias) * 0.8
                + rng.uniform(-0.012, 0.012),
                0.03,
                0.32,
            )
            threshold_alignment_ratio = _clip(
                0.88
                - abs(macro_shock) * 1.1
                - max(supply_shock, 0.0) * 0.5
                + rng.uniform(-0.05, 0.03),
                0.45,
                1.0,
            )
            gate_consistency_ratio = _clip(
                0.90
                - abs(macro_shock) * 1.0
                - max(volatility - 0.18, 0.0) * 0.8
                + rng.uniform(-0.04, 0.04),
                0.45,
                1.0,
            )
            governance_readiness_score = _clip(
                0.86
                + max(cagr - 0.10, 0.0) * 0.8
                - abs(macro_shock) * 1.0
                - max(volatility - 0.18, 0.0) * 0.6
                + rng.uniform(-0.05, 0.04),
                0.25,
                0.99,
            )
            localization_governance_score = _clip(
                0.82
                + seasonal * 0.8
                - abs(macro_shock) * 0.9
                - abs(entity_bias) * 0.5
                + rng.uniform(-0.05, 0.05),
                0.2,
                0.99,
            )
            master_data_health_score = _clip(
                0.90
                - abs(macro_shock) * 0.6
                - max(supply_shock, 0.0) * 0.4
                + rng.uniform(-0.04, 0.03),
                0.35,
                0.99,
            )
            audit_trace_score = _clip(
                0.91
                - abs(macro_shock) * 0.7
                - max(volatility - 0.18, 0.0) * 0.4
                + rng.uniform(-0.04, 0.03),
                0.35,
                0.99,
            )
            decision_gate_control_score = _clip(
                0.88
                - abs(macro_shock) * 0.7
                - max(volatility - 0.18, 0.0) * 0.5
                - max(supply_shock, 0.0) * 0.3
                + rng.uniform(-0.05, 0.04),
                0.3,
                0.99,
            )
            control_tower_score = _clip(
                master_data_health_score * 0.34
                + audit_trace_score * 0.33
                + decision_gate_control_score * 0.33,
                0.0,
                1.0,
            )
            supply_tail_risk_score = _clip(
                0.28
                + max(supply_shock, 0.0) * 1.7
                + max(volatility - 0.16, 0.0) * 0.9
                + abs(entity_bias) * 0.6
                + rng.uniform(-0.05, 0.05),
                0.05,
                0.95,
            )
            supply_loss_probability = _clip(
                0.05
                + max(supply_shock, 0.0) * 0.9
                + max(volatility - 0.16, 0.0) * 0.6
                + rng.uniform(-0.02, 0.03),
                0.01,
                0.45,
            )
            supply_margin_floor_breach_probability = _clip(
                0.06
                + max(supply_shock, 0.0) * 0.8
                + abs(macro_shock) * 0.4
                + rng.uniform(-0.02, 0.03),
                0.01,
                0.5,
            )
            supply_optimizer_feasible_ratio = _clip(
                0.82
                - max(supply_shock, 0.0) * 1.8
                - max(volatility - 0.18, 0.0) * 0.7
                + rng.uniform(-0.06, 0.04),
                0.05,
                1.0,
            )
            supply_execution_confidence_score = _clip(
                0.80
                - max(supply_shock, 0.0) * 1.4
                - abs(macro_shock) * 0.4
                - max(volatility - 0.18, 0.0) * 0.5
                + rng.uniform(-0.05, 0.05),
                0.15,
                0.98,
            )
            supply_optimizer_gate_pass = 1.0 if (
                supply_optimizer_feasible_ratio >= 0.25
                and supply_execution_confidence_score >= 0.6
                and supply_tail_risk_score <= 0.6
            ) else 0.0
            channel_portfolio_resilience_score = _clip(
                0.84
                - abs(macro_shock) * 1.0
                - max(volatility - 0.18, 0.0) * 0.7
                - max(supply_shock, 0.0) * 0.5
                + seasonal * 0.4
                + rng.uniform(-0.05, 0.05),
                0.15,
                0.99,
            )
            channel_execution_friction_factor = _clip(
                0.72
                - max(supply_shock, 0.0) * 0.8
                - max(volatility - 0.18, 0.0) * 0.6
                - abs(entity_bias) * 0.8
                + rng.uniform(-0.05, 0.05),
                0.05,
                0.98,
            )
            channel_scale_readiness_score = _clip(
                0.70
                + max(cagr - 0.10, 0.0) * 1.2
                - abs(macro_shock) * 0.8
                - max(supply_shock, 0.0) * 0.5
                + rng.uniform(-0.05, 0.05),
                0.08,
                0.99,
            )
            channel_optimizer_feasible_ratio = _clip(
                0.76
                - max(volatility - 0.18, 0.0) * 0.8
                - max(supply_shock, 0.0) * 0.6
                + seasonal * 0.2
                + rng.uniform(-0.05, 0.05),
                0.05,
                1.0,
            )
            channel_stress_robustness_score = _clip(
                0.78
                - abs(macro_shock) * 1.0
                - max(supply_shock, 0.0) * 0.6
                - max(volatility - 0.18, 0.0) * 0.6
                + rng.uniform(-0.04, 0.04),
                0.05,
                1.0,
            )
            channel_gate_flip_count = round(
                max(
                    0.0,
                    min(
                        3.0,
                        (1 - channel_stress_robustness_score) * 2.2
                        + (1 - channel_optimizer_feasible_ratio) * 1.4
                        + rng.uniform(-0.25, 0.35),
                    ),
                )
            )
            channel_portfolio_readiness_score = _clip(
                channel_portfolio_resilience_score * 0.30
                + channel_execution_friction_factor * 0.15
                + channel_scale_readiness_score * 0.25
                + channel_optimizer_feasible_ratio * 0.15
                + channel_stress_robustness_score * 0.15,
                0.05,
                1.0,
            )
            channel_loss_probability_weighted = _clip(
                0.07
                + max(volatility - 0.18, 0.0) * 0.8
                + max(supply_shock, 0.0) * 0.55
                + abs(macro_shock) * 0.35
                + rng.uniform(-0.02, 0.02),
                0.01,
                0.55,
            )
            channel_margin_rate_var_95 = _clip(
                margin_rate
                - 0.045
                - max(volatility - 0.18, 0.0) * 0.45
                - max(supply_shock, 0.0) * 0.18
                + rng.uniform(-0.01, 0.01),
                -0.08,
                0.35,
            )
            channel_margin_rate_es_95 = _clip(
                channel_margin_rate_var_95
                - 0.018
                - abs(macro_shock) * 0.08
                + rng.uniform(-0.008, 0.008),
                -0.12,
                0.3,
            )
            channel_tail_shortfall_severity = _clip(
                0.018
                + max(volatility - 0.18, 0.0) * 0.55
                + max(supply_shock, 0.0) * 0.2
                + abs(macro_shock) * 0.12
                + rng.uniform(-0.01, 0.01),
                0.0,
                0.2,
            )
            channel_risk_adjusted_profit = round(
                max(unit_margin, -5.0)
                * (1 - max(volatility - 0.10, 0.0))
                * max(channel_execution_friction_factor, 0.05)
                * 120,
                2,
            )
            channel_optimizer_gate_pass = 1.0 if (
                channel_optimizer_feasible_ratio >= 0.25
                and channel_scale_readiness_score >= 0.5
                and channel_stress_robustness_score >= 0.6
                and channel_gate_flip_count <= 1
            ) else 0.0
            operating_health_score = _clip(
                0.76
                + margin_rate * 0.45
                - abs(macro_shock) * 0.8
                - max(volatility - 0.18, 0.0) * 0.55
                + rng.uniform(-0.05, 0.05),
                0.1,
                0.99,
            )
            data_contract_score = _clip(
                0.84
                - abs(macro_shock) * 0.4
                - max(supply_shock, 0.0) * 0.4
                + rng.uniform(-0.05, 0.04),
                0.2,
                0.99,
            )
            experiment_confidence_score = _clip(
                forecast_backtest_score * 0.45
                + (1 - forecast_mape) * 0.20
                + drift_score * 0.20
                + gate_consistency_ratio * 0.15
                + rng.uniform(-0.03, 0.03),
                0.05,
                0.99,
            )
            scale_control_score = _clip(
                channel_scale_readiness_score * 0.35
                + channel_stress_robustness_score * 0.25
                + (1 - channel_loss_probability_weighted) * 0.20
                + operating_health_score * 0.20,
                0.05,
                0.99,
            )
            operating_system_readiness_score = _clip(
                operating_health_score * 0.3
                + data_contract_score * 0.2
                + experiment_confidence_score * 0.2
                + scale_control_score * 0.3,
                0.05,
                0.99,
            )
            operating_proxy_flag_count = float(
                round(
                    max(
                        0.0,
                        min(
                            6.0,
                            abs(macro_shock) * 10
                            + max(supply_shock, 0.0) * 8
                            + max(volatility - 0.18, 0.0) * 10
                            + rng.uniform(-0.4, 0.6),
                        ),
                    )
                )
            )
            forward_return_rate = _clip(
                margin_rate * 0.42 + seasonal + entity_bias + macro_shock - supply_shock / 2 + rng.uniform(-0.07, 0.07),
                -0.25,
                0.28,
            )
            benchmark_return_rate = _clip(
                0.035 + seasonal / 2 + macro_shock / 2 + rng.uniform(-0.04, 0.04),
                -0.18,
                0.18,
            )
            rows.append(
                {
                    "as_of_date": month_value.isoformat(),
                    "entity_id": opportunity["entity_id"],
                    "segment": opportunity["segment"],
                    "TAM": round(tam, 2),
                    "CAGR": round(cagr, 4),
                    "HHI": round(hhi, 2),
                    "volatility": round(volatility, 4),
                    "landed_cost": round(landed_cost, 2),
                    "expected_price": round(expected_price, 2),
                    "platform_fee": round(platform_fee, 2),
                    "forecast_backtest_score": round(forecast_backtest_score, 4),
                    "signal_regime": signal_regime,
                    "signal_regime_score": round(signal_regime_score, 4),
                    "signal_seasonality_confidence_score": round(signal_seasonality_confidence_score, 4),
                    "signal_spectral_entropy": round(signal_spectral_entropy, 4),
                    "signal_approximate_entropy": round(signal_approximate_entropy, 4),
                    "forecast_mape": round(forecast_mape, 4),
                    "drift_score": round(drift_score, 4),
                    "drift_risk_score": round(drift_risk_score, 4),
                    "calibration_brier_score": round(calibration_brier_score, 4),
                    "threshold_alignment_ratio": round(threshold_alignment_ratio, 4),
                    "gate_consistency_ratio": round(gate_consistency_ratio, 4),
                    "governance_readiness_score": round(governance_readiness_score, 4),
                    "localization_governance_score": round(localization_governance_score, 4),
                    "control_tower_score": round(control_tower_score, 4),
                    "master_data_health_score": round(master_data_health_score, 4),
                    "audit_trace_score": round(audit_trace_score, 4),
                    "decision_gate_control_score": round(decision_gate_control_score, 4),
                    "supply_tail_risk_score": round(supply_tail_risk_score, 4),
                    "supply_loss_probability": round(supply_loss_probability, 4),
                    "supply_margin_floor_breach_probability": round(supply_margin_floor_breach_probability, 4),
                    "supply_optimizer_feasible_ratio": round(supply_optimizer_feasible_ratio, 4),
                    "supply_execution_confidence_score": round(supply_execution_confidence_score, 4),
                    "supply_optimizer_gate_pass": round(supply_optimizer_gate_pass, 4),
                    "channel_portfolio_readiness_score": round(channel_portfolio_readiness_score, 4),
                    "channel_portfolio_resilience_score": round(channel_portfolio_resilience_score, 4),
                    "channel_execution_friction_factor": round(channel_execution_friction_factor, 4),
                    "channel_scale_readiness_score": round(channel_scale_readiness_score, 4),
                    "channel_optimizer_feasible_ratio": round(channel_optimizer_feasible_ratio, 4),
                    "channel_optimizer_gate_pass": round(channel_optimizer_gate_pass, 4),
                    "channel_risk_adjusted_profit": round(channel_risk_adjusted_profit, 2),
                    "channel_stress_robustness_score": round(channel_stress_robustness_score, 4),
                    "channel_gate_flip_count": round(float(channel_gate_flip_count), 4),
                    "channel_loss_probability_weighted": round(channel_loss_probability_weighted, 4),
                    "channel_margin_rate_var_95": round(channel_margin_rate_var_95, 4),
                    "channel_margin_rate_es_95": round(channel_margin_rate_es_95, 4),
                    "channel_tail_shortfall_severity": round(channel_tail_shortfall_severity, 4),
                    "operating_system_readiness_score": round(operating_system_readiness_score, 4),
                    "operating_health_score": round(operating_health_score, 4),
                    "data_contract_score": round(data_contract_score, 4),
                    "experiment_confidence_score": round(experiment_confidence_score, 4),
                    "scale_control_score": round(scale_control_score, 4),
                    "operating_proxy_flag_count": round(operating_proxy_flag_count, 4),
                    "required_capital": round(opportunity["required_capital"], 2),
                    "forward_return_rate": round(forward_return_rate, 4),
                    "benchmark_return_rate": round(benchmark_return_rate, 4),
                }
            )
    return rows


def write_panel_csv(output_path: str | Path, rows: list[dict[str, str | float]]) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("rows cannot be empty")
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def load_panel_csv(path: str | Path) -> list[dict[str, str | float]]:
    path = Path(path)
    rows: list[dict[str, str | float]] = []
    numeric_fields = {
        "TAM",
        "CAGR",
        "HHI",
        "volatility",
        "landed_cost",
        "expected_price",
        "platform_fee",
        "forecast_backtest_score",
        "signal_regime_score",
        "signal_seasonality_confidence_score",
        "signal_spectral_entropy",
        "signal_approximate_entropy",
        "forecast_mape",
        "drift_score",
        "drift_risk_score",
        "calibration_brier_score",
        "threshold_alignment_ratio",
        "gate_consistency_ratio",
        "governance_readiness_score",
        "localization_governance_score",
        "control_tower_score",
        "master_data_health_score",
        "audit_trace_score",
        "decision_gate_control_score",
        "supply_tail_risk_score",
        "supply_loss_probability",
        "supply_margin_floor_breach_probability",
        "supply_optimizer_feasible_ratio",
        "supply_execution_confidence_score",
        "supply_optimizer_gate_pass",
        "channel_portfolio_readiness_score",
        "channel_portfolio_resilience_score",
        "channel_execution_friction_factor",
        "channel_scale_readiness_score",
        "channel_optimizer_feasible_ratio",
        "channel_optimizer_gate_pass",
        "channel_risk_adjusted_profit",
        "channel_stress_robustness_score",
        "channel_gate_flip_count",
        "channel_loss_probability_weighted",
        "channel_margin_rate_var_95",
        "channel_margin_rate_es_95",
        "channel_tail_shortfall_severity",
        "operating_system_readiness_score",
        "operating_health_score",
        "data_contract_score",
        "experiment_confidence_score",
        "scale_control_score",
        "operating_proxy_flag_count",
        "required_capital",
        "forward_return_rate",
        "benchmark_return_rate",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized: dict[str, str | float] = {}
            for key, value in row.items():
                if key in numeric_fields:
                    normalized[key] = float(value)
                else:
                    normalized[key] = value
            rows.append(normalized)
    return rows
