from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Part4QuantPlanTests(unittest.TestCase):
    def test_part4_quant_plan_yaml_exists_and_has_required_sections(self) -> None:
        path = ROOT / "config" / "part4_quant_plan.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["module"], "part4_channel_portfolio_engine")
        self.assertIn("goals", payload)
        self.assertIn("layers", payload)
        self.assertIn("sections", payload)
        self.assertIn("validation", payload)
        self.assertIn("tooling", payload)
        self.assertIn("delivery_phases", payload)
        self.assertIn("4.1", payload["sections"])
        self.assertIn("4.7", payload["sections"])
        self.assertIn("FAC-PORTFOLIO-RESILIENCE", payload["layers"]["factor"]["outputs"])
        self.assertIn("part4_optimizer_runs", payload["layers"]["data"]["backtest_tables"])


if __name__ == "__main__":
    unittest.main()
