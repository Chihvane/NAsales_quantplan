# Decision OS v3.0 Dashboard Spec

## Purpose

This dashboard spec defines the minimum product structure for `Decision OS v3.0`.

It is organized around four operator views:

1. Executive View
2. Model View
3. Portfolio View
4. Audit View

## 1. Executive View

Primary cards:

- Market attractiveness score
- Capital utilization rate
- Risk budget utilization rate
- Current gate pass rate
- Active portfolio count
- Recalibration required count

Primary tables:

- Latest decision records
- Gate failures by scenario
- Capital pool status by portfolio

## 2. Model View

Primary charts:

- Monte Carlo profit distribution
- Loss probability trend
- Drawdown band
- Factor score breakdown

Primary tables:

- Model registry
- Model versions
- Validation status
- Prediction error leaderboard

## 3. Portfolio View

Primary charts:

- Channel ROI comparison
- Portfolio capital allocation mix
- Channel dependency heatmap
- Expected return vs drawdown scatter

Primary tables:

- Opportunity ranking
- Accepted vs rejected allocation rows
- Portfolio concentration summary

## 4. Audit View

Primary charts:

- Decision count by gate
- Evidence chain coverage
- Schema version distribution

Primary tables:

- Decision record ledger
- Approval chain ledger
- Capital history
- Feedback and recalibration events

## 5. Data Binding Contract

The dashboard should bind to these entities:

- `field_registry`
- `metric_registry`
- `factor_registry`
- `model_registry`
- `gate_registry`
- `capital_pool_snapshot`
- `risk_budget_snapshot`
- `decision_record`
- `portfolio_run`
- `portfolio_allocation`
- `feedback_record`

## 6. MVP UI Rule

The dashboard MVP should be read-only first.

Phase order:

1. Read-only executive and audit views
2. Portfolio and model drill-down
3. Manual gate evaluation trigger
4. Automated decision and alert subscriptions
