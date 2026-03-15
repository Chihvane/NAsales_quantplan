# Part 3 README

## Position

`Part 3` answers one question: can China-side supply and export execution deliver a viable landed cost and controlled risk.

## Core Documents

- Strategy draft: [Part3-China-Supply-Chain-Export-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-China-Supply-Chain-Export-Strategy.md)
- Quant structure: [Part3-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Structure.md)
- Optimization plan: [Part3-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Optimization-Plan.md)
- Decision OS plan config: [part3_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part3_quant_plan.yaml)

## Code Entry

- Report builder: [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- Metrics engine: [part3_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_metrics.py)
- Simulation: [part3_simulation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_simulation.py)
- Dataset pipeline: [part3_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_pipeline.py)

## Standard Input

- `suppliers.csv`
- `rfq_quotes.csv`
- `compliance_requirements.csv`
- `logistics_quotes.csv`
- `tariff_tax.csv`
- `shipment_events.csv`

## Standard Output

- Report: [part3_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part3/part3_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part3/charts)
- Cleaning demo: [cleaned_part3_demo](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/cleaned_part3_demo)

## Current Granularity

- Strategy draft: yes
- Quantitative structure: yes
- Raw export cleaners: yes
- Monte Carlo: yes
- Validation: yes
- Backtest: yes

## Section Scope

- `3.1` 供应成熟度
- `3.2` 报价结构
- `3.3` 合规准入
- `3.4` 物流履约
- `3.5` 到岸成本与利润安全边际
- `3.6` 风险矩阵
- `3.7` 推荐进入路径

## Current Role In The Full System

`Part 3` is the supply feasibility gate. It should determine whether the selected product concept can survive landed cost, compliance, and logistics reality.
