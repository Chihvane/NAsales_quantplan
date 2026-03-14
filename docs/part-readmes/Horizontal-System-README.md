# Horizontal System README

## Position

`Horizontal System` is the cross-part control-tower layer for `Part 0–5`.

It is responsible for:

- master data and data dictionary governance
- evidence lineage and audit traceability
- decision-rule and trigger-loop control

## Core Documents

- Strategy draft: [Horizontal-System-Management-Module.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Management-Module.md)
- Quant structure: [Horizontal-System-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Quantitative-Structure.md)
- Source PDF: [北美小众兴趣商品研究框架横向系统模块草案.pdf](/Users/zhiwenxiang/Downloads/北美小众兴趣商品研究框架横向系统模块草案.pdf)
- Source DOCX: [北美市场量化报告框架.docx](/Users/zhiwenxiang/Downloads/北美市场量化报告框架.docx)
- Crosswalk: [Horizontal-System-DOCX-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-DOCX-Crosswalk.md)

## Code Entry

- Report builder: [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- Metrics engine: [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
- Dataset pipeline: [horizontal_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_pipeline.py)

## Standard Input

- `master_data_entities.csv`
- `data_dictionary_fields.csv`
- `evidence_lineage.csv`
- `audit_events.csv`
- `decision_rules.csv`
- `decision_triggers.csv`

## Standard Output

- Report: [horizontal_system_report.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_horizontal_system/horizontal_system_report.json)
- Charts: [charts](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_horizontal_system/charts)

## Current Granularity

- Strategy draft: yes
- Quantitative structure: yes
- Code builder: yes
- CLI: yes
- Validation: yes
- Demo data: yes

## Current Role In The Full System

`Horizontal System` turns `Part 0` governance rules into reusable master-data, audit, and decision-rule controls that can be shared across `Part 1–5`.

It is now aligned to both the standalone horizontal-module source PDF and the broader framework DOCX, so the governance layer uses the same terminology as the full report draft.
