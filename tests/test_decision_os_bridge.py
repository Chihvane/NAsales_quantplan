from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from quant_framework.decision_os_bridge import export_decision_os_bridge_bundle
from quant_framework.horizontal_pipeline import (
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report
from quant_framework.part0 import build_part0_quant_report
from quant_framework.part0_pipeline import (
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from quant_framework.part1 import build_part1_quant_report
from quant_framework.part2 import build_part2_quant_report
from quant_framework.part2_pipeline import DEFAULT_PART2_ASSUMPTIONS, build_part2_dataset_from_directory
from quant_framework.part3 import build_part3_quant_report
from quant_framework.part3_pipeline import DEFAULT_PART3_ASSUMPTIONS, build_part3_dataset_from_directory
from quant_framework.part4 import build_part4_quant_report
from quant_framework.part4_pipeline import DEFAULT_PART4_ASSUMPTIONS, build_part4_dataset_from_directory
from quant_framework.part5 import build_part5_quant_report
from quant_framework.part5_pipeline import DEFAULT_PART5_ASSUMPTIONS, build_part5_dataset_from_directory
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PART0_EXAMPLES = EXAMPLES / "part0_demo"
HORIZONTAL_EXAMPLES = EXAMPLES / "horizontal_system_demo"
PART2_EXAMPLES = EXAMPLES / "part2_demo"
PART3_EXAMPLES = EXAMPLES / "part3_demo"
PART4_EXAMPLES = EXAMPLES / "part4_demo"
PART5_EXAMPLES = EXAMPLES / "part5_demo"


class DecisionOSBridgeTests(unittest.TestCase):
    def test_export_bridge_bundle(self) -> None:
        part0_report = build_part0_quant_report(
            build_part0_dataset_from_directory(PART0_EXAMPLES),
            DEFAULT_PART0_ASSUMPTIONS,
        )
        horizontal_report = build_horizontal_system_report(
            build_horizontal_system_dataset_from_directory(HORIZONTAL_EXAMPLES),
            DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
        )
        part1_report = build_part1_quant_report(build_dataset_from_directory(EXAMPLES), DEFAULT_ASSUMPTIONS)
        part2_report = build_part2_quant_report(
            build_part2_dataset_from_directory(PART2_EXAMPLES),
            DEFAULT_PART2_ASSUMPTIONS,
        )
        part3_report = build_part3_quant_report(
            build_part3_dataset_from_directory(PART3_EXAMPLES),
            DEFAULT_PART3_ASSUMPTIONS,
        )
        part4_report = build_part4_quant_report(
            build_part4_dataset_from_directory(PART4_EXAMPLES),
            DEFAULT_PART4_ASSUMPTIONS,
        )
        part5_report = build_part5_quant_report(
            build_part5_dataset_from_directory(PART5_EXAMPLES),
            DEFAULT_PART5_ASSUMPTIONS,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            result = export_decision_os_bridge_bundle(
                part1_report,
                part2_report,
                temp_dir,
                part3_report=part3_report,
                part4_report=part4_report,
                part0_report=part0_report,
                horizontal_report=horizontal_report,
                part5_report=part5_report,
                tenant_id="TENANT-TEST",
                as_of_date="2026-03-15",
            )
            bundle = json.loads(Path(result["bundle_json"]).read_text(encoding="utf-8"))
            self.assertEqual(bundle["tenant_id"], "TENANT-TEST")
            self.assertEqual(bundle["as_of_date"], "2026-03-15")
            self.assertGreater(bundle["gate_inputs"]["integrated_factor_score"], 0.0)
            self.assertGreaterEqual(len(bundle["factor_panel"]), 32)
            self.assertIn("governance_readiness_score", bundle["gate_inputs"])
            self.assertIn("control_tower_score", bundle["gate_inputs"])
            self.assertIn("operating_system_readiness_score", bundle["gate_inputs"])
            self.assertIn("data_contract_score", bundle["gate_inputs"])
            self.assertIn("signal_regime_score", bundle["gate_inputs"])
            self.assertIn("signal_seasonality_confidence_score", bundle["gate_inputs"])
            self.assertIn("supply_tail_risk_score", bundle["gate_inputs"])
            self.assertIn("supply_optimizer_feasible_ratio", bundle["gate_inputs"])
            self.assertIn("channel_portfolio_resilience_score", bundle["gate_inputs"])
            self.assertIn("channel_stress_robustness_score", bundle["gate_inputs"])
            self.assertIn("channel_margin_rate_var_95", bundle["gate_inputs"])
            self.assertIn("channel_tail_shortfall_severity", bundle["gate_inputs"])
            self.assertIn("part0_governance_signals", bundle)
            self.assertIn("horizontal_control_signals", bundle)
            self.assertIn("part3_supply_signals", bundle)
            self.assertIn("part4_channel_signals", bundle)
            self.assertIn("part5_operating_signals", bundle)
            self.assertTrue(Path(result["factor_panel_csv"]).exists())


if __name__ == "__main__":
    unittest.main()
