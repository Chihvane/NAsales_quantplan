# Quant Report Contract

## Purpose

This file defines the shared output contract used by Part 1, Part 2, and Part 3.

The goal is to keep all quantitative modules aligned on:

- report metadata
- section envelope
- data quality scoring
- confidence labeling
- executive summary output
- CLI summary shape

## Standard Report Shape

Every report now returns:

- `metadata`
- `overview`
- `sections`
- `uncertainty`
- `validation`

For Part 1, Part 2, and Part 3, `overview` now also carries a shared decision layer:

- `headline_metrics`
- `decision_signal`
- `decision_score`
- `decision_summary`

## Metadata

`metadata` contains:

- `report_id`
- `report_version`
- `generated_at`
- `section_order`
- `section_structure`
- `metric_specs`
- `assumptions`
- `table_inventory`

## Section Envelope

Every section now uses the same outer structure:

```json
{
  "id": "1.1",
  "title": "市场现状与需求概览",
  "required_tables": ["search_trends", "region_demand"],
  "metric_ids": ["demand_growth_rate", "seasonality_index", "regional_demand_share"],
  "data_quality": {
    "record_counts": {
      "search_trends": 12,
      "region_demand": 7
    },
    "available_tables": ["search_trends", "region_demand"],
    "missing_tables": [],
    "completeness_ratio": 1.0,
    "richness_ratio": 1.0,
    "quality_score": 1.0,
    "quality_level": "high"
  },
  "confidence": {
    "score": 1.0,
    "level": "high"
  },
  "metrics": {}
}
```

## Data Quality Rule

Section quality is now derived from two components:

- `completeness_ratio`
  - whether the required tables exist and are non-empty
- `richness_ratio`
  - whether each table reaches the section's target row count

Current formula:

```text
quality_score = completeness_ratio * 0.65 + richness_ratio * 0.35
```

Current levels:

- `high`: `>= 0.75`
- `medium`: `>= 0.50`
- `low`: `< 0.50`

## Section Targets

Each part now defines `quality_targets` inside its section structure.

This keeps confidence scoring comparable while still respecting different data grains:

- Part 1: search / region / listing / transaction / channel level
- Part 2: listing snapshot / sold transaction / review level
- Part 3: supplier / RFQ / route / shipment event level

## CLI Summary

All `report*` CLI commands now return the same summary keys when not printing the full report:

- `validation`
- `overview`
- `headline_metrics`
- `decision_signal`
- `decision_score`
- `sections`
- optional `report_json`

## Implementation

Shared assembly logic lives in:

- [reporting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/reporting.py)

Current builders using this contract:

- [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
