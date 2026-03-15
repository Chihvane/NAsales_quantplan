from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import app  # noqa: E402


class SystemApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("backend.api.system.build_system_snapshot_payload")
    def test_system_snapshot_endpoint(self, build_snapshot) -> None:
        build_snapshot.return_value = {
            "decision": "GO",
            "factor_score": 0.71,
            "bridge_meta": {"factor_panel_count": 32},
        }
        response = self.client.get("/system/snapshot")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["decision"], "GO")
        self.assertEqual(response.json()["bridge_meta"]["factor_panel_count"], 32)

    @patch("backend.api.system.load_or_run_full_chain_payload")
    def test_system_summary_endpoint(self, load_summary) -> None:
        load_summary.return_value = {
            "status": "loaded",
            "artifacts": {"summary_json": "/tmp/summary.json"},
            "summary": {"snapshot": {"decision": "NO_GO"}},
            "reports_overview": [{"label": "Part 1", "decision_signal": "attractive"}],
        }
        response = self.client.get("/system/summary")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "loaded")
        self.assertEqual(payload["reports_overview"][0]["label"], "Part 1")

    @patch("backend.api.system.run_full_chain_payload")
    def test_system_run_full_chain_endpoint(self, run_payload) -> None:
        run_payload.return_value = {
            "status": "completed",
            "artifacts": {"summary_json": "/tmp/summary.json"},
            "summary": {"optimization_summary": {"test_alpha": 0.2}},
            "reports_overview": [],
        }
        response = self.client.post("/system/run-full-chain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")


if __name__ == "__main__":
    unittest.main()
