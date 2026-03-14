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


if __name__ == "__main__":
    unittest.main()
