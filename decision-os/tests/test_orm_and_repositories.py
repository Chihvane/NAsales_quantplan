from __future__ import annotations

import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models import Base, SKU, TenantRegistry  # noqa: E402
from backend.repositories import SKURepository, TenantRepository  # noqa: E402


class OrmAndRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def test_metadata_contains_production_tables(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        for table_name in [
            "tenant_registry",
            "sku_master",
            "field_registry",
            "metric_registry",
            "factor_registry",
            "model_registry",
            "gate_registry",
            "decision_log",
            "execution_feedback",
            "portfolio_registry",
            "audit_log",
        ]:
            self.assertIn(table_name, table_names)

    def test_tenant_scoped_sku_repository(self) -> None:
        tenant_repo = TenantRepository(self.session)
        tenant = tenant_repo.create({"tenant_name": "Tenant A"})

        sku_repo = SKURepository(self.session, tenant.tenant_id)
        sku = sku_repo.create_sku(
            {
                "sku_code": "SKU-001",
                "brand": "North",
                "category": "EDC",
                "status": "active",
                "currency": "USD",
            }
        )

        fetched = sku_repo.get_sku(sku.sku_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.sku_code, "SKU-001")
        self.assertEqual(fetched.tenant_id, tenant.tenant_id)

    def test_er_assets_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "er_diagram.mmd").exists())
        self.assertTrue((ROOT / "docs" / "er_diagram.dot").exists())


if __name__ == "__main__":
    unittest.main()
