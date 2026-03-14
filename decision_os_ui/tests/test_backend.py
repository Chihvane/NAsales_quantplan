from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from decision_os_ui.backend.main import app


class DecisionOSUIBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_decision_endpoint(self) -> None:
        response = self.client.get("/decision")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("factor_score", payload)
        self.assertIn("model_outputs", payload)
        self.assertEqual(payload["decision"], "GO")

    def test_report_generation_endpoint(self) -> None:
        response = self.client.post("/report/generate")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("paths", payload)
        self.assertTrue(payload["paths"]["pdf_path"].endswith(".pdf"))
