from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Part2QuantPlanTests(unittest.TestCase):
    def test_part2_quant_plan_yaml_exists_and_has_required_sections(self) -> None:
        path = ROOT / "config" / "part2_quant_plan.yaml"
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["module"], "part2_product_intelligence_engine")
        self.assertIn("goals", payload)
        self.assertIn("layers", payload)
        self.assertIn("sections", payload)
        self.assertIn("backtest", payload)
        self.assertIn("delivery_phases", payload)
        self.assertIn("2.1", payload["sections"])
        self.assertIn("2.6", payload["sections"])
        self.assertIn("FAC-VOC-RISK", payload["layers"]["factor"]["outputs"])
        self.assertIn("validation", payload)
        self.assertIn("tooling", payload)
        self.assertIn("part2_calibration_report", payload["layers"]["data"]["backtest_tables"])


if __name__ == "__main__":
    unittest.main()
