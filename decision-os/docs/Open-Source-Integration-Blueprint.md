# Open-Source Integration Blueprint

## Goal
Connect Decision OS to open-source tooling that improves measurement discipline without making runtime availability depend on any single external package.

## Current Integration Targets
- `GX Core`
  - data quality validation for raw and processed datasets
- `Evidently`
  - drift and monitoring payloads for changing demand, price, and channel distributions
- `MLflow`
  - run tracking for backtests and parameter optimization
- `Optuna`
  - optional hyperparameter optimization for gate thresholds

## Design Principle
All integrations are optional adapters.

If the package is installed:
- Decision OS can hand off to the external project.

If the package is not installed:
- the adapter still returns a structured payload
- tests still pass
- the core decision engine remains runnable

## Quantitative Strategy Upgrade
This integration layer is not only for tooling convenience. It upgrades the quantitative strategy in three ways:

1. `GX Core`
   - turns schema assumptions into explicit validation payloads.
2. `Evidently`
   - adds monitored distribution drift for market and channel inputs.
3. `Optuna / fallback grid search`
   - trains gate thresholds instead of freezing them as static defaults.
4. `MLflow`
   - records parameter choices and backtest outcomes in a reproducible run log.

## Current Runtime
- Adapters live under `backend/oss_integrations/`
- Optimization entrypoint lives in `backtest/strategy_optimizer.py`
- Demo runner lives in `scripts/run_backtest_optimization.py`
