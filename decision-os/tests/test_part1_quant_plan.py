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
        self.assertIn("validation", payload)
        self.assertIn("tooling", payload)
        self.assertIn("delivery_phases", payload)
        self.assertIn("1.1", payload["sections"])
        self.assertIn("1.6", payload["sections"])
        self.assertIn(
            "part1_calibration_report",
            payload["layers"]["data"]["backtest_tables"],
        )
        self.assertIn("market_destination_registry", payload["layers"]["governance"]["required_objects"])
        self.assertIn("consumer_habit_vectors", payload["layers"]["governance"]["required_objects"])
        self.assertIn("region_weight_profiles", payload["layers"]["governance"]["required_objects"])
        self.assertIn("part1_market_destination_engine", payload["tooling"]["modules"])
        self.assertIn("fibonacci_regime_lab", payload["tooling"]["modules"])


if __name__ == "__main__":
    unittest.main()
