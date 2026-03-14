from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.orm import DecisionLog, ExecutionFeedback
from backend.repositories.base import BaseRepository


class DecisionRepository(BaseRepository[DecisionLog]):
    def __init__(self, db: Session, tenant_id):
        super().__init__(db, DecisionLog, tenant_id=tenant_id)

    def record_decision(self, payload: dict) -> DecisionLog:
        return self.create(payload)

    def add_feedback(self, payload: dict) -> ExecutionFeedback:
        if self.tenant_id is not None and "tenant_id" not in payload:
            payload["tenant_id"] = self.tenant_id
        feedback = ExecutionFeedback(**payload)
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def list_feedback(self, decision_id):
        stmt = select(ExecutionFeedback).where(ExecutionFeedback.decision_id == decision_id)
        if self.tenant_id is not None:
            stmt = stmt.where(ExecutionFeedback.tenant_id == self.tenant_id)
        return list(self.db.execute(stmt).scalars())
