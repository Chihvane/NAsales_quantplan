from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.orm import TenantRegistry
from backend.repositories.base import BaseRepository


class TenantRepository(BaseRepository[TenantRegistry]):
    def __init__(self, db: Session):
        super().__init__(db, TenantRegistry)

    def get_active_tenants(self) -> list[TenantRegistry]:
        stmt = select(TenantRegistry).where(TenantRegistry.is_active.is_(True))
        return list(self.db.execute(stmt).scalars())
