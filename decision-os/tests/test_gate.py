from __future__ import annotations

import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.gate_engine.gate_engine import evaluate_market_gate  # noqa: E402


class GateTests(unittest.TestCase):
    def test_gate_pass(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.7,
            model_outputs={
                "profit_p10": 0.08,
                "profit_p50": 0.18,
                "margin_p50_ratio": 0.22,
                "loss_probability": 0.1,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=500000,
        )
        self.assertEqual(result, "GO")

    def test_gate_rejects_high_volatility_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.72,
            model_outputs={
                "profit_p10": 0.1,
                "profit_p50": 0.22,
                "margin_p50_ratio": 0.24,
                "loss_probability": 0.08,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=300000,
            candidate_features={"volatility": 0.28, "hhi": 2200},
            thresholds={"max_volatility": 0.2},
        )
        self.assertEqual(result, "NO_GO_VOLATILITY")

    def test_gate_rejects_weak_forecast_signal_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.74,
            model_outputs={
                "profit_p10": 0.1,
                "profit_p50": 0.22,
                "margin_p50_ratio": 0.24,
                "loss_probability": 0.08,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=300000,
            candidate_features={"forecast_backtest_score": 0.42, "drift_score": 0.72, "drift_risk_score": 0.22},
            thresholds={"min_forecast_backtest_score": 0.55},
        )
        self.assertEqual(result, "NO_GO_FORECAST")

    def test_gate_rejects_noisy_signal_regime_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.74,
            model_outputs={
                "profit_p10": 0.1,
                "profit_p50": 0.22,
                "margin_p50_ratio": 0.24,
                "loss_probability": 0.08,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=300000,
            candidate_features={
                "signal_regime_score": 0.35,
                "signal_seasonality_confidence_score": 0.12,
                "signal_spectral_entropy": 0.82,
                "signal_approximate_entropy": 0.33,
            },
            thresholds={"min_signal_regime_score": 0.5},
        )
        self.assertEqual(result, "NO_GO_SIGNAL_REGIME")

    def test_gate_rejects_supply_tail_risk_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.76,
            model_outputs={
                "profit_p10": 0.12,
                "profit_p50": 0.24,
                "margin_p50_ratio": 0.26,
                "loss_probability": 0.07,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=250000,
            candidate_features={
                "supply_tail_risk_score": 0.62,
                "supply_optimizer_feasible_ratio": 0.5,
                "supply_execution_confidence_score": 0.8,
                "supply_optimizer_gate_pass": 1.0,
            },
            thresholds={"max_supply_tail_risk_score": 0.55},
        )
        self.assertEqual(result, "NO_GO_SUPPLY_TAIL_RISK")

    def test_gate_rejects_channel_stress_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.78,
            model_outputs={
                "profit_p10": 0.12,
                "profit_p50": 0.24,
                "margin_p50_ratio": 0.26,
                "loss_probability": 0.07,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=250000,
            candidate_features={
                "channel_portfolio_readiness_score": 0.62,
                "channel_portfolio_resilience_score": 0.74,
                "channel_execution_friction_factor": 0.52,
                "channel_scale_readiness_score": 0.66,
                "channel_optimizer_feasible_ratio": 0.5,
                "channel_optimizer_gate_pass": 1.0,
                "channel_stress_robustness_score": 0.54,
                "channel_gate_flip_count": 2.0,
            },
            thresholds={"min_channel_stress_robustness_score": 0.65},
        )
        self.assertEqual(result, "NO_GO_CHANNEL_STRESS")

    def test_gate_rejects_channel_tail_shortfall_when_threshold_present(self) -> None:
        result = evaluate_market_gate(
            factor_score=0.78,
            model_outputs={
                "profit_p10": 0.12,
                "profit_p50": 0.24,
                "margin_p50_ratio": 0.26,
                "loss_probability": 0.07,
            },
            capital_state={"free_capital": 800000, "total_capital": 1000000},
            risk_state={"max_loss_probability": 0.3},
            required_capital=250000,
            candidate_features={
                "channel_portfolio_readiness_score": 0.62,
                "channel_portfolio_resilience_score": 0.74,
                "channel_execution_friction_factor": 0.52,
                "channel_scale_readiness_score": 0.66,
                "channel_optimizer_feasible_ratio": 0.5,
                "channel_optimizer_gate_pass": 1.0,
                "channel_stress_robustness_score": 0.8,
                "channel_gate_flip_count": 0.0,
                "channel_loss_probability_weighted": 0.11,
                "channel_margin_rate_var_95": 0.025,
                "channel_margin_rate_es_95": 0.012,
                "channel_tail_shortfall_severity": 0.12,
            },
            thresholds={"max_channel_tail_shortfall_severity": 0.08},
        )
        self.assertEqual(result, "NO_GO_CHANNEL_TAIL_SHORTFALL")


if __name__ == "__main__":
    unittest.main()
