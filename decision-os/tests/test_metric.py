from __future__ import annotations

import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.metric_layer.metric_engine import safe_divide  # noqa: E402


class MetricTests(unittest.TestCase):
    def test_safe_divide(self) -> None:
        self.assertEqual(safe_divide(10, 2), 5)
        self.assertEqual(safe_divide(10, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
