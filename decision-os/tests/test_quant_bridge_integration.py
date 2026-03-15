from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.dependencies import build_market_snapshot  # noqa: E402
from quant_framework.decision_os_bridge import export_decision_os_bridge_bundle  # noqa: E402
from quant_framework.horizontal_pipeline import (  # noqa: E402
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report  # noqa: E402
from quant_framework.part0 import build_part0_quant_report  # noqa: E402
from quant_framework.part0_pipeline import (  # noqa: E402
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from quant_framework.part1 import build_part1_quant_report  # noqa: E402
from quant_framework.part2 import build_part2_quant_report  # noqa: E402
from quant_framework.part2_pipeline import (  # noqa: E402
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)
from quant_framework.part3 import build_part3_quant_report  # noqa: E402
from quant_framework.part3_pipeline import (  # noqa: E402
    DEFAULT_PART3_ASSUMPTIONS,
    build_part3_dataset_from_directory,
)
from quant_framework.part4 import build_part4_quant_report  # noqa: E402
from quant_framework.part4_pipeline import (  # noqa: E402
    DEFAULT_PART4_ASSUMPTIONS,
    build_part4_dataset_from_directory,
)
from quant_framework.part5 import build_part5_quant_report  # noqa: E402
from quant_framework.part5_pipeline import (  # noqa: E402
    DEFAULT_PART5_ASSUMPTIONS,
    build_part5_dataset_from_directory,
)
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory  # noqa: E402


class QuantBridgeIntegrationTests(unittest.TestCase):
    def test_build_market_snapshot_prefers_quant_bridge_bundle(self) -> None:
        part0_report = build_part0_quant_report(
            build_part0_dataset_from_directory(WORKSPACE_ROOT / "examples" / "part0_demo"),
            DEFAULT_PART0_ASSUMPTIONS,
        )
        horizontal_report = build_horizontal_system_report(
            build_horizontal_system_dataset_from_directory(WORKSPACE_ROOT / "examples" / "horizontal_system_demo"),
            DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
        )
        part1_report = build_part1_quant_report(
            build_dataset_from_directory(WORKSPACE_ROOT / "examples"),
            DEFAULT_ASSUMPTIONS,
        )
        part2_report = build_part2_quant_report(
            build_part2_dataset_from_directory(WORKSPACE_ROOT / "examples" / "part2_demo"),
            DEFAULT_PART2_ASSUMPTIONS,
        )
        part3_report = build_part3_quant_report(
            build_part3_dataset_from_directory(WORKSPACE_ROOT / "examples" / "part3_demo"),
            DEFAULT_PART3_ASSUMPTIONS,
        )
        part4_report = build_part4_quant_report(
            build_part4_dataset_from_directory(WORKSPACE_ROOT / "examples" / "part4_demo"),
            DEFAULT_PART4_ASSUMPTIONS,
        )
        part5_report = build_part5_quant_report(
            build_part5_dataset_from_directory(WORKSPACE_ROOT / "examples" / "part5_demo"),
            DEFAULT_PART5_ASSUMPTIONS,
        )
        output_dir = WORKSPACE_ROOT / "artifacts" / "decision_os_bridge"
        export_decision_os_bridge_bundle(
            part1_report,
            part2_report,
            output_dir,
            part3_report=part3_report,
            part4_report=part4_report,
            part0_report=part0_report,
            horizontal_report=horizontal_report,
            part5_report=part5_report,
            tenant_id="TENANT-BRIDGE",
            as_of_date="2026-03-15",
        )
        snapshot = build_market_snapshot()
        self.assertEqual(snapshot["source_mode"], "quant_bridge")
        self.assertGreater(snapshot["factor_score"], 0.0)
        self.assertIn("bridge_bundle", snapshot)
        self.assertEqual(snapshot["bridge_bundle"]["tenant_id"], "TENANT-BRIDGE")
        self.assertIn("governance_readiness_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("control_tower_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("operating_system_readiness_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("forecast_backtest_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("signal_regime_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("signal_seasonality_confidence_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("drift_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("calibration_brier_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("supply_tail_risk_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("supply_optimizer_feasible_ratio", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("channel_portfolio_resilience_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("channel_optimizer_feasible_ratio", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("channel_stress_robustness_score", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("channel_margin_rate_var_95", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("channel_tail_shortfall_severity", snapshot["bridge_bundle"]["gate_inputs"])
        self.assertIn("candidate_features", snapshot)
        self.assertIn("gate_thresholds", snapshot)
        self.assertIn("governance_readiness_score", snapshot["candidate_features"])
        self.assertIn("control_tower_score", snapshot["candidate_features"])
        self.assertIn("operating_system_readiness_score", snapshot["candidate_features"])
        self.assertIn("signal_regime_score", snapshot["candidate_features"])
        self.assertIn("supply_tail_risk_score", snapshot["candidate_features"])
        self.assertIn("channel_portfolio_resilience_score", snapshot["candidate_features"])
        self.assertIn("channel_tail_shortfall_severity", snapshot["candidate_features"])
        self.assertTrue(
            json.loads((output_dir / "integrated_market_product_bundle.json").read_text(encoding="utf-8"))
        )


if __name__ == "__main__":
    unittest.main()
