from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data_loader import generate_demo_panel  # noqa: E402
from backtest.walk_forward_engine import run_walk_forward_backtest  # noqa: E402


class BacktestTests(unittest.TestCase):
    def test_walk_forward_backtest_generates_summary(self) -> None:
        panel = generate_demo_panel(seed=42)
        result = run_walk_forward_backtest(panel, initial_capital=750000)
        self.assertIn("summary", result)
        self.assertIn("period_records", result)
        self.assertIn("decisions", result)
        self.assertGreater(result["summary"]["periods"], 12)
        self.assertGreater(result["summary"]["decision_count"], 50)
        self.assertIn("alpha", result["summary"])
        self.assertIn("gate_breakdown", result["summary"])
        self.assertIn("average_forecast_backtest_score", result["summary"])
        self.assertIn("average_signal_regime_score", result["summary"])
        self.assertIn("average_signal_seasonality_confidence_score", result["summary"])
        self.assertIn("average_drift_score", result["summary"])
        self.assertIn("average_calibration_brier_score", result["summary"])
        self.assertIn("average_governance_readiness_score", result["summary"])
        self.assertIn("average_control_tower_score", result["summary"])
        self.assertIn("average_supply_tail_risk_score", result["summary"])
        self.assertIn("average_supply_optimizer_feasible_ratio", result["summary"])
        self.assertIn("average_supply_execution_confidence_score", result["summary"])
        self.assertIn("average_channel_portfolio_resilience_score", result["summary"])
        self.assertIn("average_channel_optimizer_feasible_ratio", result["summary"])
        self.assertIn("average_channel_stress_robustness_score", result["summary"])
        self.assertIn("average_channel_margin_rate_var_95", result["summary"])
        self.assertIn("average_channel_tail_shortfall_severity", result["summary"])
        self.assertIn("average_operating_system_readiness_score", result["summary"])
        self.assertIn("average_scale_control_score", result["summary"])


if __name__ == "__main__":
    unittest.main()
