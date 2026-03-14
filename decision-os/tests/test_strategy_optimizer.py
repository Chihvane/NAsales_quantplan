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


if __name__ == "__main__":
    unittest.main()
