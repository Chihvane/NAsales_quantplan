from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid


class Base(DeclarativeBase):
    pass


class TenantRegistry(Base):
    __tablename__ = "tenant_registry"

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    users: Mapped[list["UserRegistry"]] = relationship(back_populates="tenant")
    skus: Mapped[list["SKU"]] = relationship(back_populates="tenant")


class UserRegistry(Base):
    __tablename__ = "user_registry"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    tenant: Mapped["TenantRegistry"] = relationship(back_populates="users")


class SKU(Base):
    __tablename__ = "sku_master"

    sku_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    tenant: Mapped["TenantRegistry"] = relationship(back_populates="skus")


class ChannelMaster(Base):
    __tablename__ = "channel_master"

    channel_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_type: Mapped[Optional[str]] = mapped_column(String(50))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class SupplierMaster(Base):
    __tablename__ = "supplier_master"

    supplier_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    risk_rating: Mapped[Optional[float]] = mapped_column(Float)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class FieldRegistry(Base):
    __tablename__ = "field_registry"

    field_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_level: Mapped[Optional[str]] = mapped_column(String(1))
    ref_key: Mapped[Optional[str]] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MetricRegistry(Base):
    __tablename__ = "metric_registry"

    metric_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    aggregation_level: Mapped[Optional[str]] = mapped_column(String(50))
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class MetricDependency(Base):
    __tablename__ = "metric_dependencies"

    metric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("metric_registry.metric_id"), primary_key=True)
    depends_on_field_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("field_registry.field_id"),
        primary_key=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MetricValue(Base):
    __tablename__ = "metric_values"

    metric_value_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    metric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("metric_registry.metric_id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FactorRegistry(Base):
    __tablename__ = "factor_registry"

    factor_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    factor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalization_method: Mapped[Optional[str]] = mapped_column(String(50))
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class FactorComponent(Base):
    __tablename__ = "factor_components"

    factor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("factor_registry.factor_id"), primary_key=True)
    metric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("metric_registry.metric_id"), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FactorValue(Base):
    __tablename__ = "factor_values"

    factor_value_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    factor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("factor_registry.factor_id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    validation_method: Mapped[Optional[str]] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class ModelInput(Base):
    __tablename__ = "model_inputs"

    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_registry.model_id"), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    input_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    input_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModelResult(Base):
    __tablename__ = "model_results"

    result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_registry.model_id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    result_date: Mapped[date] = mapped_column(Date, nullable=False)
    profit_p10: Mapped[Optional[float]] = mapped_column(Float)
    profit_p50: Mapped[Optional[float]] = mapped_column(Float)
    profit_p90: Mapped[Optional[float]] = mapped_column(Float)
    loss_probability: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GateRegistry(Base):
    __tablename__ = "gate_registry"

    gate_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    gate_name: Mapped[str] = mapped_column(String(255), nullable=False)
    logic: Mapped[str] = mapped_column(String(10), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class GateCondition(Base):
    __tablename__ = "gate_conditions"

    condition_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    gate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gate_registry.gate_id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    operator: Mapped[str] = mapped_column(String(10), nullable=False)
    threshold: Mapped[Optional[float]] = mapped_column(Float)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DecisionLog(Base):
    __tablename__ = "decision_log"

    decision_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    gate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gate_registry.gate_id"), nullable=False)
    model_version: Mapped[int] = mapped_column(Integer, nullable=False)
    capital_version: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision_result: Mapped[str] = mapped_column(String(50), nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user_registry.user_id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExecutionFeedback(Base):
    __tablename__ = "execution_feedback"

    feedback_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decision_log.decision_id"), nullable=False)
    actual_profit: Mapped[Optional[float]] = mapped_column(Float)
    actual_loss_probability: Mapped[Optional[float]] = mapped_column(Float)
    model_prediction_error: Mapped[Optional[float]] = mapped_column(Float)
    recalibration_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapitalPool(Base):
    __tablename__ = "capital_pool"

    capital_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    total_capital: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_capital: Mapped[float] = mapped_column(Float, nullable=False)
    free_capital: Mapped[float] = mapped_column(Float, nullable=False)
    cost_of_capital: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CapitalAllocationLog(Base):
    __tablename__ = "capital_allocation_log"

    allocation_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    allocated_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskBudget(Base):
    __tablename__ = "risk_budget"

    risk_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    max_loss_probability: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    max_inventory_exposure: Mapped[float] = mapped_column(Float, nullable=False)
    max_channel_dependency: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class RiskExposureLog(Base):
    __tablename__ = "risk_exposure_log"

    exposure_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    loss_probability: Mapped[float] = mapped_column(Float, nullable=False)
    drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PortfolioRegistry(Base):
    __tablename__ = "portfolio_registry"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    portfolio_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    positions: Mapped[list["PortfolioPosition"]] = relationship(back_populates="portfolio")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    position_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolio_registry.portfolio_id"),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    allocated_capital: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return: Mapped[Optional[float]] = mapped_column(Float)
    expected_risk: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["PortfolioRegistry"] = relationship(back_populates="positions")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_registry.tenant_id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user_registry.user_id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    previous_hash: Mapped[Optional[str]] = mapped_column(Text)
    current_hash: Mapped[Optional[str]] = mapped_column(Text)
