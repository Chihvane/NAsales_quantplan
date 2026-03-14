# Decision OS Backtesting Program

## Objective
Move Decision OS from a rule-complete architecture into a historically validated operating system.

## What already existed in the project
- Part-level demo backtests under `quant_framework/backtest.py`
- Backtest PDF packaging under `scripts/generate_backtest_pdf.py`
- Decision OS production scaffold under `decision-os/`

## What this module adds
- A Decision OS-native `backtest/` package
- Walk-forward state reconstruction
- Capital-aware gate evaluation
- Period-level and decision-level performance reporting

## Initial Scope
- Frequency: monthly
- Horizon: 2019-01 through 2024-12 demo panel
- Engine style: walk-forward, no future leakage
- Outputs:
  - `backtest_summary.json`
  - `period_records.csv`
  - `decision_accuracy.csv`
  - `alpha_table.csv`
  - `performance_curve.svg`
  - `drawdown_curve.svg`

## Next Upgrade Steps
1. Replace demo panel with tenant-scoped historical snapshots from PostgreSQL.
2. Add stress-test scenarios for freight, CPC, return rate, and capital compression.
3. Add parameter optimization with train/test splits rather than fixed gate thresholds.
4. Write backtest results into `decision_log`, `capital_allocation_log`, and `execution_feedback`.
