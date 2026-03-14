from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DatabaseSchemaTests(unittest.TestCase):
    def test_schema_contains_core_tables(self) -> None:
        schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        for table_name in [
            "tenant_registry",
            "user_registry",
            "sku_master",
            "channel_master",
            "supplier_master",
            "field_registry",
            "metric_registry",
            "metric_values",
            "factor_registry",
            "factor_values",
            "model_registry",
            "model_results",
            "gate_registry",
            "capital_pool",
            "risk_budget",
            "portfolio_registry",
            "portfolio_positions",
            "decision_log",
            "execution_feedback",
            "audit_log",
        ]:
            self.assertIn(table_name, schema)

    def test_schema_contains_production_conventions(self) -> None:
        schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
        self.assertIn("tenant_id UUID", schema)
        self.assertIn("version INTEGER", schema)
        self.assertIn("is_active BOOLEAN", schema)
        self.assertIn("currency VARCHAR(10)", schema)
        self.assertIn("TIMESTAMPTZ", schema)

    def test_init_script_bootstraps_schema(self) -> None:
        init_sql = (ROOT / "database" / "init.sql").read_text(encoding="utf-8")
        self.assertIn('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";', init_sql)
        self.assertIn("\\i schema.sql", init_sql)


if __name__ == "__main__":
    unittest.main()
