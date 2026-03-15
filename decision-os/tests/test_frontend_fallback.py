from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.streamlit_app import _load_local_state  # noqa: E402


class FrontendFallbackTests(unittest.TestCase):
    def test_load_local_state_from_artifacts(self) -> None:
        summary, snapshot, audit = _load_local_state(refresh_summary=False)
        self.assertIn("summary", summary)
        self.assertEqual(snapshot.get("decision"), "NO_GO_CONCENTRATION")
        self.assertGreaterEqual(snapshot.get("bridge_meta", {}).get("factor_panel_count", 0), 1)
        self.assertEqual(audit.get("logs", [{}])[0].get("module"), "frontend.local_fallback")


if __name__ == "__main__":
    unittest.main()
