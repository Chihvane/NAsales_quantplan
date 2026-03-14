CREATE TABLE IF NOT EXISTS system_registry (
    system_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    namespace TEXT NOT NULL,
    governance_owner TEXT NOT NULL,
    capital_pool_ref TEXT NOT NULL,
    risk_budget_ref TEXT NOT NULL,
    gate_engine_version TEXT NOT NULL,
    feedback_engine_version TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS field_registry (
    field_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    entity TEXT NOT NULL,
    data_type TEXT NOT NULL,
    unit TEXT,
    source TEXT NOT NULL,
    update_frequency TEXT,
    confidence_level TEXT,
    owner TEXT,
    ref_key TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metric_registry (
    metric_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    formula TEXT NOT NULL,
    aggregation_level TEXT,
    definition_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS factor_registry (
    factor_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    normalization_method TEXT,
    weighting_logic TEXT,
    definition_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_registry (
    model_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    validation_method TEXT,
    definition_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gate_registry (
    gate_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    logic TEXT NOT NULL,
    definition_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capital_pool_snapshot (
    capital_pool_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    snapshot_at TEXT NOT NULL,
    total_capital REAL NOT NULL,
    allocated_capital REAL NOT NULL,
    free_capital REAL NOT NULL,
    cost_of_capital REAL NOT NULL,
    PRIMARY KEY (capital_pool_id, snapshot_at)
);

CREATE TABLE IF NOT EXISTS risk_budget_snapshot (
    risk_budget_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    snapshot_at TEXT NOT NULL,
    max_loss_probability REAL NOT NULL,
    max_drawdown REAL NOT NULL,
    max_inventory_exposure REAL NOT NULL,
    max_channel_dependency REAL NOT NULL,
    PRIMARY KEY (risk_budget_id, snapshot_at)
);

CREATE TABLE IF NOT EXISTS model_run (
    model_run_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    input_ref_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    run_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES model_registry(model_id)
);

CREATE TABLE IF NOT EXISTS gate_evaluation (
    gate_eval_id TEXT PRIMARY KEY,
    gate_id TEXT NOT NULL,
    decision_status TEXT NOT NULL,
    failed_conditions_json TEXT NOT NULL,
    capital_blocked INTEGER DEFAULT 0,
    risk_blocked INTEGER DEFAULT 0,
    model_run_id TEXT,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (gate_id) REFERENCES gate_registry(gate_id),
    FOREIGN KEY (model_run_id) REFERENCES model_run(model_run_id)
);

CREATE TABLE IF NOT EXISTS decision_record (
    decision_id TEXT PRIMARY KEY,
    gate_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    capital_version TEXT NOT NULL,
    risk_version TEXT NOT NULL,
    portfolio_id TEXT,
    status TEXT NOT NULL,
    failed_conditions_json TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    notes TEXT,
    hash_signature TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (gate_id) REFERENCES gate_registry(gate_id)
);

CREATE TABLE IF NOT EXISTS portfolio_run (
    portfolio_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    objective TEXT NOT NULL,
    allocated_capital REAL NOT NULL,
    remaining_capital REAL NOT NULL,
    expected_profit_proxy REAL NOT NULL,
    capital_utilization_rate REAL NOT NULL,
    run_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_allocation (
    portfolio_id TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    allocated_capital REAL NOT NULL,
    expected_return REAL NOT NULL,
    expected_drawdown REAL NOT NULL,
    objective_score REAL NOT NULL,
    accepted INTEGER NOT NULL,
    reject_reason TEXT,
    PRIMARY KEY (portfolio_id, opportunity_id),
    FOREIGN KEY (portfolio_id) REFERENCES portfolio_run(portfolio_id)
);

CREATE TABLE IF NOT EXISTS feedback_record (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    portfolio_id TEXT,
    predicted_profit REAL NOT NULL,
    actual_profit REAL NOT NULL,
    predicted_loss_probability REAL NOT NULL,
    actual_loss_probability REAL NOT NULL,
    predicted_drawdown REAL NOT NULL,
    actual_drawdown REAL NOT NULL,
    model_prediction_error REAL NOT NULL,
    loss_probability_gap REAL NOT NULL,
    drawdown_gap REAL NOT NULL,
    recalibration_required INTEGER NOT NULL,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (decision_id) REFERENCES decision_record(decision_id)
);

CREATE TABLE IF NOT EXISTS evidence_node (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    parent_node_id TEXT,
    data_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_node_id) REFERENCES evidence_node(node_id)
);

CREATE INDEX IF NOT EXISTS idx_model_run_model_id ON model_run(model_id);
CREATE INDEX IF NOT EXISTS idx_gate_evaluation_gate_id ON gate_evaluation(gate_id);
CREATE INDEX IF NOT EXISTS idx_decision_record_gate_id ON decision_record(gate_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_allocation_channel ON portfolio_allocation(channel);
CREATE INDEX IF NOT EXISTS idx_feedback_record_decision_id ON feedback_record(decision_id);
