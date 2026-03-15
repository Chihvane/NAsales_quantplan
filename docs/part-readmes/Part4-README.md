# Part 4 README

## Position

`Part 4` answers one question: which North American sales path should be tested first, with what operating burden and ROI profile.

## Core Documents

- Strategy draft: [Part4-North-America-Go-To-Market-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-North-America-Go-To-Market-Strategy.md)
- Quant structure: [Part4-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-Quantitative-Structure.md)
- Optimization plan: [Part4-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-Quantitative-Optimization-Plan.md)
- Deep optimization crosswalk: [Part4-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-Deep-Optimization-Crosswalk.md)

## Code Entry

- Report builder: [part4.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4.py)
- Metrics engine: [part4_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4_metrics.py)
- Simulation: [part4_simulation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4_simulation.py)
- Dataset pipeline: [part4_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4_pipeline.py)

## Standard Input

- `listing_snapshots.csv`
- `sold_transactions.csv`
- `product_catalog.csv`
- `landed_cost_scenarios.csv`
- `channel_rate_cards.csv`
- `marketing_spend.csv`
- `traffic_sessions.csv`
- `returns_claims.csv`
- `customer_cohorts.csv`
- `inventory_positions.csv`
- `experiment_registry.csv`
- `b2b_accounts.csv`

## Standard Output

- Report: [part4_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part4/part4_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part4/charts)

## Current Granularity

- Strategy draft: yes
- Quantitative structure: yes
- Optimization plan: yes
- Monte Carlo ROI: yes
- Validation: yes
- Decision summary: yes
- Backtest: yes

## Section Scope

- `4.1` 独立站模式
- `4.2` 平台电商模式
- `4.3` 线下经销 / ToB
- `4.4` 流量结构
- `4.5` ROI 与单位经济
- `4.6` 组织承接能力
- `4.7` 进入建议与 90 天计划

## Current Role In The Full System

`Part 4` is the channel sequencing layer. It should convert product feasibility into a practical launch order, not just describe channels independently.
