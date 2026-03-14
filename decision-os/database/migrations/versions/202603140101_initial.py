"""initial decision os schema

Revision ID: 202603140101_initial
Revises:
Create Date: 2026-03-14 01:01:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "202603140101_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_registry",
        sa.Column("field_id", sa.String(length=50), primary_key=True),
        sa.Column("schema_version", sa.String(length=10), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("ref_key", sa.String(length=100)),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("field_registry")
