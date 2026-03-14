# Part 0 README

## Position

`Part 0` is the governance and decision-control layer for the whole research system.

It sits above `Part 1–5` and defines:

- decision tree structure
- evidence confidence rules
- assumption register rules
- Gate thresholds
- signature chain
- refresh / expiry rules
- field dictionary and reuse policy

## Core Documents

- Strategy draft: [Part0-Research-Governance-And-Decision-Charter.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-Research-Governance-And-Decision-Charter.md)
- Quant structure: [Part0-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-Quantitative-Structure.md)
- Rule crosswalk: [Part0-1-Architecture-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-1-Architecture-Optimization-Crosswalk.md)
- Source PDFs:
  - [研究报告 Part 0 模板：研究治理与决策总则.pdf](/Users/zhiwenxiang/Downloads/研究报告%20Part%200%20模板：研究治理与决策总则.pdf)
  - [第零部分：研究治理与决策总则.pdf](/Users/zhiwenxiang/Downloads/第零部分：研究治理与决策总则.pdf)

## Code Entry

- Report builder: [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- Metrics engine: [part0_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_metrics.py)
- Dataset pipeline: [part0_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_pipeline.py)

## Standard Input

- `decision_nodes.csv`
- `evidence_sources.csv`
- `assumptions_register.csv`
- `gate_thresholds.csv`
  - now expected to cover strategic metric families such as `ROIC / HHI / heat volatility / payback / risk`
- `approval_chain.csv`
- `update_policies.csv`
- `field_dictionary.csv`

## Standard Output

- Report: [part0_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part0/part0_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part0/charts)

## Current Granularity

- Strategy draft: yes
- Quantitative structure: yes
- Code builder: yes
- CLI: yes
- Validation: yes
- Demo data: yes

## Current Role In The Full System

`Part 0` is the layer that turns the existing research framework into a decision operating system.
