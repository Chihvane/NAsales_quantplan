from __future__ import annotations

import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.field_layer.field_validator import validate_field_record  # noqa: E402


class FieldTests(unittest.TestCase):
    def test_field_validator(self) -> None:
        errors = validate_field_record(
            {
                "field_id": "F-0001",
                "schema_version": "3.0",
                "entity": "SKU",
                "data_type": "float",
                "source": "amazon_sp_api",
            }
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
