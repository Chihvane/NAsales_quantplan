# Strategy Deep Optimization

## Why This Iteration Exists

The prior Decision OS backtest stack could deliver high decision hit rates while still
underperforming the benchmark. The main issue was weak selectivity:

- `GO` coverage was too high.
- Gate thresholds emphasized median profit only.
- Portfolio selection did not cap position count per period.
- Optimization used a single-objective alpha target with no robustness test.

This iteration hardens the strategy so the engine behaves more like a real screening
and allocation system instead of a broad pass-through filter.

## Key Changes

### 1. Harder Gate Dimensions

The market gate now supports additional constraints beyond `profit_p50`:

- `min_profit_p10`
- `min_margin_p50_ratio`
- `max_volatility`
- `max_hhi`
- `max_required_capital_ratio`

These thresholds allow the engine to reject opportunities that are profitable on median
but weak on tail risk, unit economics, or structural concentration.

### 2. Portfolio Capacity Control

`run_walk_forward_backtest` now supports `max_positions_per_period`.

This prevents the strategy from deploying capital into nearly every passing opportunity
in a given period, which previously diluted selectivity and benchmark-relative edge.

### 3. Richer Backtest Summary

Performance summaries now include:

- `go_ratio`
- `average_positions_per_period`
- `average_deployed_capital_ratio`

These metrics are used to judge whether the strategy is realistically deployable,
not just directionally profitable.

### 4. Stress Test Integration

The optimizer now evaluates candidates under a stress suite:

- `freight_up_40`
- `cpc_up_50`
- `demand_drop_20`
- `return_rate_shock`
- `capital_cut_30`

The resulting `robustness_score` is included in optimization.

### 5. Composite Optimization Objective

The optimizer no longer maximizes raw alpha only.

It now uses a composite score that rewards:

- alpha
- decision hit rate
- rejection precision
- healthy selectivity
- healthy deployed capital ratio
- stress robustness

and penalizes:

- excessive drawdown
- over-broad selection

## Expected Outcome

The goal of this iteration is not simply a higher hit rate.

The goal is a strategy that:

- rejects more low-quality candidates,
- preserves capital under stress,
- avoids benchmark-like overexposure,
- and produces better train/test stability.
