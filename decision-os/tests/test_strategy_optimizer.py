from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data_loader import generate_demo_panel  # noqa: E402
from backtest.strategy_optimizer import optimize_gate_thresholds  # noqa: E402


class StrategyOptimizerTests(unittest.TestCase):
    def test_strategy_optimizer_returns_best_gate_params(self) -> None:
        panel = generate_demo_panel(seed=42)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = optimize_gate_thresholds(
                panel,
                output_dir=Path(temp_dir),
                search_space={
                    "min_factor_score": [0.55, 0.65],
                    "max_loss_probability": [0.15, 0.2],
                    "min_profit_p50": [0.0, 2.0],
                    "min_margin_p50_ratio": [0.18],
                    "max_volatility": [0.2, 0.24],
                    "min_governance_readiness_score": [0.6],
                    "min_control_tower_score": [0.65],
                    "min_forecast_backtest_score": [0.55],
                    "max_forecast_mape": [0.2],
                    "min_signal_regime_score": [0.45],
                    "max_signal_spectral_entropy": [0.9],
                    "min_drift_score": [0.55],
                    "max_drift_risk_score": [0.45],
                    "max_calibration_brier_score": [0.18],
                    "min_threshold_alignment_ratio": [0.9],
                    "min_gate_consistency_ratio": [0.9],
                    "max_supply_tail_risk_score": [0.45],
                    "min_supply_optimizer_feasible_ratio": [0.25],
                    "min_channel_optimizer_feasible_ratio": [0.25],
                    "min_channel_stress_robustness_score": [0.6],
                    "max_channel_tail_shortfall_severity": [0.08],
                    "min_operating_system_readiness_score": [0.5],
                    "min_data_contract_score": [0.55],
                    "min_scale_control_score": [0.5],
                    "max_operating_proxy_flag_count": [4.0],
                    "max_positions_per_period": [2],
                },
                simulations=300,
            )
            self.assertIn("best_gate_params", result)
            self.assertIn("train_summary", result)
            self.assertIn("test_summary", result)
            self.assertIn("train_stress_summary", result)
            self.assertIn("test_stress_summary", result)
            self.assertIn("test_score", result)
            self.assertEqual(result["candidate_count"], 16)
            self.assertLessEqual(result["best_gate_params"]["max_positions_per_period"], 2)
            self.assertIn("min_forecast_backtest_score", result["best_gate_params"])
            self.assertIn("max_forecast_mape", result["best_gate_params"])
            self.assertIn("min_drift_score", result["best_gate_params"])
            self.assertIn("max_drift_risk_score", result["best_gate_params"])
            self.assertIn("max_calibration_brier_score", result["best_gate_params"])
            self.assertIn("min_threshold_alignment_ratio", result["best_gate_params"])
            self.assertIn("min_gate_consistency_ratio", result["best_gate_params"])
            self.assertIn("min_governance_readiness_score", result["best_gate_params"])
            self.assertIn("min_control_tower_score", result["best_gate_params"])
            self.assertIn("min_operating_system_readiness_score", result["best_gate_params"])
            self.assertIn("average_signal_regime_score", result["test_summary"])
            self.assertIn("average_supply_tail_risk_score", result["test_summary"])
            self.assertIn("average_channel_optimizer_feasible_ratio", result["test_summary"])
            self.assertIn("average_channel_tail_shortfall_severity", result["test_summary"])
            self.assertIn("average_governance_readiness_score", result["test_summary"])
            self.assertIn("average_operating_system_readiness_score", result["test_summary"])


if __name__ == "__main__":
    unittest.main()
