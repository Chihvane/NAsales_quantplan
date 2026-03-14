from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.portfolio_engine.portfolio_optimizer import rank_portfolio_rows  # noqa: E402


class PortfolioTests(unittest.TestCase):
    def test_portfolio_ranking(self) -> None:
        rows = rank_portfolio_rows(
            [
                {"channel": "Amazon", "score": 0.5},
                {"channel": "DTC", "score": 0.7},
            ]
        )
        self.assertEqual(rows[0]["channel"], "DTC")


if __name__ == "__main__":
    unittest.main()
