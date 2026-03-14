from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.orm import SKU
from backend.repositories.base import BaseRepository


class SKURepository(BaseRepository[SKU]):
    def __init__(self, db: Session, tenant_id):
        super().__init__(db, SKU, tenant_id=tenant_id)

    def create_sku(self, sku_data: dict) -> SKU:
        return self.create(sku_data)

    def get_sku(self, sku_id):
        return self.get(sku_id)

    def get_by_code(self, sku_code: str) -> SKU | None:
        stmt = select(SKU).where(SKU.sku_code == sku_code)
        stmt = self._apply_tenant_scope(stmt)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_active(self, limit: int = 100) -> list[SKU]:
        return self.list(limit=limit, active_only=True)
