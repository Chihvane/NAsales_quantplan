from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.orm import PortfolioPosition, PortfolioRegistry
from backend.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[PortfolioRegistry]):
    def __init__(self, db: Session, tenant_id):
        super().__init__(db, PortfolioRegistry, tenant_id=tenant_id)

    def create_portfolio(self, payload: dict) -> PortfolioRegistry:
        return self.create(payload)

    def add_position(self, payload: dict) -> PortfolioPosition:
        if self.tenant_id is not None and "tenant_id" not in payload:
            payload["tenant_id"] = self.tenant_id
        position = PortfolioPosition(**payload)
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def list_positions(self, portfolio_id):
        stmt = select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio_id)
        stmt = stmt.where(PortfolioPosition.tenant_id == self.tenant_id)
        return list(self.db.execute(stmt).scalars())
