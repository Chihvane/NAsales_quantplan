# Part 1 README

## Position

`Part 1` answers one question: is the North American niche category worth entering at all.

## Core Documents

- Framework draft: [Part1-Market-Research-Framework-Outline.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Market-Research-Framework-Outline.md)
- Quant structure: [Part1-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Quantitative-Structure.md)
- Optimization plan: [Part1-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Quantitative-Optimization-Plan.md)
- Method validation note: [Part1-Methodology-Reliability-Validation.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Methodology-Reliability-Validation.md)
- Rule crosswalk: [Part0-1-Architecture-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-1-Architecture-Optimization-Crosswalk.md)
- Decision OS plan config: [part1_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part1_quant_plan.yaml)

## Code Entry

- Report builder: [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- Metrics engine: [metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py)
- Dataset pipeline: [pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/pipeline.py)

## Standard Input

- `search_trends.csv`
- `region_demand.csv`
- `customer_segments.csv`
- `listings.csv`
- `transactions.csv`
- `channels.csv`
- `market_size_inputs.csv`
- `channel_benchmarks.csv`
- `event_library.csv`
- `source_registry.csv`
- `part1_threshold_registry.csv`

## Standard Output

- Report: [part1_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output/part1_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output/charts)
- Backtest demo: [backtest_demo](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output/backtest_demo)

## Current Granularity

- Strategy / framework: yes
- Quantitative structure: yes
- Optimization plan: yes
- Demo data: yes
- Charts: yes
- Validation: yes
- Backtest: yes

## Section Scope

- `1.1` 需求趋势
- `1.2` 客户画像
- `1.3` 市场规模
- `1.4` 购买渠道
  - includes channel benchmark gap and benchmark coverage
- `1.5` 货架价格
- `1.6` 实际成交价格

## Current Role In The Full System

`Part 1` is the market-entry screen. It should feed `Part 2` SKU competition analysis, not make supply-chain or launch decisions by itself.

After the current optimization round, `Part 1` is also the target `Market Quant Engine` to be aligned with `Decision OS`.
