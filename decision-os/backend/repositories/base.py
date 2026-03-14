from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from backend.models.orm import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: type[ModelT], tenant_id: Any | None = None):
        self.db = db
        self.model = model
        self.tenant_id = tenant_id

    def _apply_tenant_scope(self, stmt):
        if self.tenant_id is not None and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(getattr(self.model, "tenant_id") == self.tenant_id)
        return stmt

    def _primary_key_name(self) -> str:
        return inspect(self.model).primary_key[0].name

    def create(self, payload: dict[str, Any]) -> ModelT:
        if self.tenant_id is not None and hasattr(self.model, "tenant_id") and "tenant_id" not in payload:
            payload["tenant_id"] = self.tenant_id
        entity = self.model(**payload)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get(self, entity_id: Any) -> ModelT | None:
        pk_name = self._primary_key_name()
        stmt = select(self.model).where(getattr(self.model, pk_name) == entity_id)
        stmt = self._apply_tenant_scope(stmt)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, *, limit: int = 100, active_only: bool = False) -> list[ModelT]:
        stmt = select(self.model)
        stmt = self._apply_tenant_scope(stmt)
        if active_only and hasattr(self.model, "is_active"):
            stmt = stmt.where(getattr(self.model, "is_active").is_(True))
        stmt = stmt.limit(limit)
        return list(self.db.execute(stmt).scalars())

    def update(self, entity_id: Any, updates: dict[str, Any]) -> ModelT | None:
        entity = self.get(entity_id)
        if entity is None:
            return None
        for key, value in updates.items():
            setattr(entity, key, value)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def soft_delete(self, entity_id: Any) -> bool:
        if not hasattr(self.model, "is_active"):
            raise AttributeError(f"{self.model.__name__} does not support soft delete")
        entity = self.get(entity_id)
        if entity is None:
            return False
        setattr(entity, "is_active", False)
        self.db.add(entity)
        self.db.commit()
        return True
