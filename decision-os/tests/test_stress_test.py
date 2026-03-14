from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data_loader import generate_demo_panel  # noqa: E402
from backtest.stress_test import run_stress_suite  # noqa: E402


class StressTestTests(unittest.TestCase):
    def test_stress_suite_returns_robustness_summary(self) -> None:
        panel = generate_demo_panel(seed=42)
        result = run_stress_suite(
            panel,
            gate_params={
                "min_factor_score": 0.65,
                "max_loss_probability": 0.15,
                "min_profit_p50": 2.0,
                "min_margin_p50_ratio": 0.18,
                "max_volatility": 0.24,
                "max_positions_per_period": 3,
            },
            simulations=200,
            seed=42,
        )
        self.assertEqual(result["scenario_count"], 5)
        self.assertIn("robustness_score", result)
        self.assertTrue(result["scenarios"])


if __name__ == "__main__":
    unittest.main()
