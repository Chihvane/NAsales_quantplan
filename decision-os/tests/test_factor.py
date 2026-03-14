from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.factor_layer.factor_engine import compute_market_factor  # noqa: E402
from backend.field_layer.field_loader import load_sample_market_fields  # noqa: E402


class FactorTests(unittest.TestCase):
    def test_market_factor(self) -> None:
        score = compute_market_factor(load_sample_market_fields())
        self.assertGreater(score, 0.5)


if __name__ == "__main__":
    unittest.main()
