from __future__ import annotations

import unittest

from decision_os_mvp.main import run_decision_flow
from decision_os_mvp.models import compute_market_factor, monte_carlo_profit_simulation
from decision_os_mvp.sample_data import generate_sample_market_data


class DecisionOSMVPTests(unittest.TestCase):
    def test_market_factor_positive(self) -> None:
        data = generate_sample_market_data()
        factor_score = compute_market_factor(data)
        self.assertGreater(factor_score, 0.5)

    def test_monte_carlo_outputs(self) -> None:
        data = generate_sample_market_data()
        outputs = monte_carlo_profit_simulation(data, simulations=1000, seed=42)
        self.assertIn("profit_p50", outputs)
        self.assertIn("loss_probability", outputs)
        self.assertGreater(outputs["profit_p50"], 0)

    def test_run_decision_flow(self) -> None:
        result = run_decision_flow()
        self.assertEqual(result["decision"], "GO")


if __name__ == "__main__":
    unittest.main()
