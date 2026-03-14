from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.oss_integrations.evidently_adapter import build_drift_payload  # noqa: E402
from backend.oss_integrations.gx_adapter import build_validation_payload  # noqa: E402
from backend.oss_integrations.registry import summarize_integrations  # noqa: E402


class OssIntegrationTests(unittest.TestCase):
    def test_registry_summary(self) -> None:
        summary = summarize_integrations()
        self.assertEqual(summary["integration_count"], 4)
        self.assertIn("integrations", summary)

    def test_gx_payload_without_package(self) -> None:
        payload = build_validation_payload(
            "part1_search_trends",
            [{"month": "2025-01", "interest": 70}],
            required_columns=["month", "interest", "keyword"],
        )
        self.assertEqual(payload["integration"], "gx_core")
        self.assertEqual(payload["status"], "review")
        self.assertIn("keyword", payload["missing_columns"])

    def test_evidently_payload_without_package(self) -> None:
        payload = build_drift_payload(
            [{"interest": 70.0, "price": 10.0}],
            [{"interest": 84.0, "price": 12.0}],
            ["interest", "price"],
        )
        self.assertEqual(payload["integration"], "evidently")
        self.assertIn("column_mean_delta", payload)


if __name__ == "__main__":
    unittest.main()
