from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Part1QuantPlanTests(unittest.TestCase):
    def test_part1_quant_plan_yaml_exists_and_has_required_sections(self) -> None:
        path = ROOT / "config" / "part1_quant_plan.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["module"], "part1_market_quant_engine")
        self.assertIn("goals", payload)
        self.assertIn("layers", payload)
        self.assertIn("sections", payload)
        self.assertIn("backtest", payload)
        self.assertIn("delivery_phases", payload)
        self.assertIn("1.1", payload["sections"])
        self.assertIn("1.6", payload["sections"])


if __name__ == "__main__":
    unittest.main()
