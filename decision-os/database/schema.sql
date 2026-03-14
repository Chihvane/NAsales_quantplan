-- Decision OS v3.0
-- Production-grade database schema
-- Conventions:
-- 1. UTC timestamps use TIMESTAMPTZ.
-- 2. Soft delete uses is_active instead of physical delete for master records.
-- 3. All key entities carry tenant_id and version.
-- 4. Monetary tables carry currency.

-- =========================================================
-- CORE DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS tenant_registry (
    tenant_id UUID PRIMARY KEY,
    tenant_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_registry (
    user_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- MASTER DATA DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS sku_master (
    sku_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    sku_code VARCHAR(100) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    status VARCHAR(50),
    currency VARCHAR(10) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channel_master (
    channel_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    channel_name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(50),
    region VARCHAR(100),
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS supplier_master (
    supplier_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    supplier_name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    risk_rating DOUBLE PRECISION,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- FIELD DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS field_registry (
    field_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    field_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    source VARCHAR(255) NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    confidence_level CHAR(1),
    ref_key VARCHAR(255),
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- ANALYTICS DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS metric_registry (
    metric_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    metric_name VARCHAR(255) NOT NULL,
    formula TEXT NOT NULL,
    aggregation_level VARCHAR(50),
    schema_version VARCHAR(20) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metric_dependencies (
    metric_id UUID NOT NULL REFERENCES metric_registry(metric_id),
    depends_on_field_id UUID NOT NULL REFERENCES field_registry(field_id),
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id, depends_on_field_id)
);

CREATE TABLE IF NOT EXISTS metric_values (
    metric_value_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    metric_id UUID NOT NULL REFERENCES metric_registry(metric_id),
    entity_id UUID NOT NULL,
    value_date DATE NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS factor_registry (
    factor_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    factor_name VARCHAR(255) NOT NULL,
    normalization_method VARCHAR(50),
    schema_version VARCHAR(20) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS factor_components (
    factor_id UUID NOT NULL REFERENCES factor_registry(factor_id),
    metric_id UUID NOT NULL REFERENCES metric_registry(metric_id),
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    weight DOUBLE PRECISION NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (factor_id, metric_id)
);

CREATE TABLE IF NOT EXISTS factor_values (
    factor_value_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    factor_id UUID NOT NULL REFERENCES factor_registry(factor_id),
    entity_id UUID NOT NULL,
    value_date DATE NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- MODEL DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS model_registry (
    model_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    validation_method VARCHAR(100),
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_inputs (
    model_id UUID NOT NULL REFERENCES model_registry(model_id),
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    input_type VARCHAR(50) NOT NULL,
    input_id UUID NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id, input_type, input_id)
);

CREATE TABLE IF NOT EXISTS model_results (
    result_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    model_id UUID NOT NULL REFERENCES model_registry(model_id),
    entity_id UUID NOT NULL,
    result_date DATE NOT NULL,
    profit_p10 DOUBLE PRECISION,
    profit_p50 DOUBLE PRECISION,
    profit_p90 DOUBLE PRECISION,
    loss_probability DOUBLE PRECISION,
    currency VARCHAR(10),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- GATE DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS gate_registry (
    gate_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    gate_name VARCHAR(255) NOT NULL,
    logic VARCHAR(10) NOT NULL,
    schema_version VARCHAR(20) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gate_conditions (
    condition_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    gate_id UUID NOT NULL REFERENCES gate_registry(gate_id),
    target_type VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    operator VARCHAR(10) NOT NULL,
    threshold DOUBLE PRECISION,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decision_log (
    decision_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    gate_id UUID NOT NULL REFERENCES gate_registry(gate_id),
    model_version INTEGER NOT NULL,
    capital_version INTEGER NOT NULL,
    risk_version INTEGER NOT NULL,
    decision_result VARCHAR(50) NOT NULL,
    approved_by UUID REFERENCES user_registry(user_id),
    approved_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_feedback (
    feedback_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    decision_id UUID NOT NULL REFERENCES decision_log(decision_id),
    actual_profit DOUBLE PRECISION,
    actual_loss_probability DOUBLE PRECISION,
    model_prediction_error DOUBLE PRECISION,
    recalibration_flag BOOLEAN DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- CAPITAL DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS capital_pool (
    capital_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    total_capital DOUBLE PRECISION NOT NULL,
    allocated_capital DOUBLE PRECISION NOT NULL,
    free_capital DOUBLE PRECISION NOT NULL,
    cost_of_capital DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capital_allocation_log (
    allocation_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    entity_id UUID NOT NULL,
    allocated_amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- RISK DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS risk_budget (
    risk_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    max_loss_probability DOUBLE PRECISION NOT NULL,
    max_drawdown DOUBLE PRECISION NOT NULL,
    max_inventory_exposure DOUBLE PRECISION NOT NULL,
    max_channel_dependency DOUBLE PRECISION NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_exposure_log (
    exposure_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    entity_id UUID NOT NULL,
    loss_probability DOUBLE PRECISION NOT NULL,
    drawdown DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- PORTFOLIO DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS portfolio_registry (
    portfolio_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    portfolio_name VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    position_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    portfolio_id UUID NOT NULL REFERENCES portfolio_registry(portfolio_id),
    entity_id UUID NOT NULL,
    allocated_capital DOUBLE PRECISION NOT NULL,
    expected_return DOUBLE PRECISION,
    expected_risk DOUBLE PRECISION,
    currency VARCHAR(10) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- AUDIT DOMAIN
-- =========================================================

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenant_registry(tenant_id),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES user_registry(user_id),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    previous_hash TEXT,
    current_hash TEXT
);

-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_user_registry_tenant_id ON user_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sku_master_tenant_id ON sku_master(tenant_id);
CREATE INDEX IF NOT EXISTS idx_channel_master_tenant_id ON channel_master(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_master_tenant_id ON supplier_master(tenant_id);
CREATE INDEX IF NOT EXISTS idx_field_registry_tenant_id ON field_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metric_registry_tenant_id ON metric_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metric_values_metric_id ON metric_values(metric_id);
CREATE INDEX IF NOT EXISTS idx_factor_registry_tenant_id ON factor_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_factor_values_factor_id ON factor_values(factor_id);
CREATE INDEX IF NOT EXISTS idx_model_registry_tenant_id ON model_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_model_results_model_id ON model_results(model_id);
CREATE INDEX IF NOT EXISTS idx_gate_registry_tenant_id ON gate_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_gate_conditions_gate_id ON gate_conditions(gate_id);
CREATE INDEX IF NOT EXISTS idx_decision_log_gate_id ON decision_log(gate_id);
CREATE INDEX IF NOT EXISTS idx_execution_feedback_decision_id ON execution_feedback(decision_id);
CREATE INDEX IF NOT EXISTS idx_capital_pool_tenant_id ON capital_pool(tenant_id);
CREATE INDEX IF NOT EXISTS idx_risk_budget_tenant_id ON risk_budget(tenant_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_registry_tenant_id ON portfolio_registry(tenant_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio_id ON portfolio_positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_id ON audit_log(tenant_id);
