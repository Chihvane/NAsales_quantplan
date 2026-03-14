from __future__ import annotations

import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.field_layer.field_loader import load_sample_market_fields  # noqa: E402
from backend.model_layer.monte_carlo import run_profit_simulation  # noqa: E402


class ModelTests(unittest.TestCase):
    def test_stub_model(self) -> None:
        result = run_profit_simulation(load_sample_market_fields(), simulations=500)
        self.assertGreater(result["profit_p50"], 0)
        self.assertLessEqual(result["loss_probability"], 1)


if __name__ == "__main__":
    unittest.main()
