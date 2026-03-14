# Part 5 README

## Position

`Part 5` answers one question: after launch, is the business healthy enough to scale, pause, roll back, or reallocate capital.

## Core Documents

- Strategy draft: [Part5-Post-Launch-Operations-Optimization-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Post-Launch-Operations-Optimization-Strategy.md)
- Quant structure: [Part5-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Quantitative-Structure.md)
- GitHub crosswalk: [Part5-GitHub-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-GitHub-Crosswalk.md)
- Execution crosswalk: [Part5-Execution-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Execution-Optimization-Crosswalk.md)

## Code Entry

- Report builder: [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
- Metrics engine: [part5_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_metrics.py)
- Experiments: [part5_experiments.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_experiments.py)
- Alerts: [part5_alerts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_alerts.py)
- ETL: [part5_etl.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_etl.py)
- Audit: [part5_audit.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_audit.py)
- Forecasting: [part5_forecasting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_forecasting.py)
- Optimization: [part5_optimization.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_optimization.py)
- Dataset pipeline: [part5_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_pipeline.py)

## Standard Input

- Shared launch tables from `Part 4`
- `kpi_daily_snapshots.csv`
- `pricing_actions.csv`
- `reorder_plan.csv`
- `policy_change_log.csv`
- `cash_flow_snapshots.csv`
- `experiment_assignments.csv`
- `experiment_metrics.csv`

## Standard Output

- Report: [part5_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part5/part5_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part5/charts)
- ETL output: [output_part5_etl](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part5_etl)

## Current Granularity

- Strategy draft: yes
- Quantitative structure: yes
- ETL skeleton: yes
- Audit pack: yes
- Experiment readout: yes
- Hierarchical Bayesian readout: yes
- Auto-stop rules: yes
- Validation: yes

## Section Scope

- `5.1` 运营目标与门禁
- `5.2` 数据体系与持续监控
- `5.3` 增长闭环
- `5.4` 定价与利润保护
- `5.5` 库存与现金周转
- `5.6` 实验与增量优化
- `5.7` 风险监控与扩张节奏

## Current Role In The Full System

`Part 5` is the operating control layer. It should produce scale, pause, rollback, and capital-allocation decisions based on monitored evidence rather than narrative judgment.
