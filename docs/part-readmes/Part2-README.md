# Part 2 README

## Position

`Part 2` answers one question: what product profile is actually winning in the market right now.

## Core Documents

- Quant structure: [Part2-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Quantitative-Structure.md)

## Code Entry

- Report builder: [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- Metrics engine: [part2_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_metrics.py)
- Dataset pipeline: [part2_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_pipeline.py)

## Standard Input

- `listing_snapshots.csv`
- `sold_transactions.csv`
- `product_catalog.csv`
- `reviews.csv`

## Standard Output

- Report: [part2_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part2/part2_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part2/charts)
- Backtest demo: [backtest_demo](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part2/backtest_demo)

## Current Granularity

- Strategy draft: no standalone strategy draft yet
- Quantitative structure: yes
- Raw bundle cleaners: yes
- Demo data: yes
- Charts: yes
- Backtest: yes

## Section Scope

- `2.1` 在售与成交结构
- `2.2` 价格甜蜜带
- `2.3` 商品属性画像
- `2.4` 属性白空间
- `2.5` 评论与负面主题
- `2.6` 货架动态与存活

## Current Role In The Full System

`Part 2` is the product-selection layer. It should feed `Part 3` RFQ, landed cost, and supplier screening.
