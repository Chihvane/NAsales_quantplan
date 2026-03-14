# Quant Report Contract

## Purpose

This file defines the shared output contract used by Part 0 through Part 5, plus the horizontal system control module.

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

For Part 0 through Part 5 and the horizontal module, `overview` now also carries a shared decision layer:

- `headline_metrics`
- `decision_signal`
- `decision_score`
- `decision_summary`
- `connected_channel_scope`
- `control_tower_binding`

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
  "granularity": {
    "analysis_grain": "month x keyword / region",
    "entity_grain": "keyword / region",
    "time_grain": "month"
  },
  "channel_scope": ["marketwide"],
  "master_data_ref": ["mdm.calendar", "mdm.region"],
  "evidence_ref": ["evidence.search_trends", "evidence.region_demand"],
  "rule_ref": ["gate.market_entry", "gate.demand_stability"],
  "gate_result": {
    "status": "not_applicable",
    "source": "",
    "raw_value": "",
    "failed_items": []
  },
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

## Control-Tower Binding

All sections now expose the same governance bridge back to `Part 0` and the horizontal control module:

- `master_data_ref`
  - which master-data domains the section depends on
- `evidence_ref`
  - which evidence chains support the section
- `rule_ref`
  - which gate / guardrail / stop-loss rules govern the section
- `gate_result`
  - normalized section-level gate status: `pass / review / fail / not_applicable`

At the report overview level, this is summarized as:

- `connected_channel_scope`
- `control_tower_binding.master_data_ref_coverage_ratio`
- `control_tower_binding.evidence_ref_coverage_ratio`
- `control_tower_binding.rule_ref_coverage_ratio`
- `control_tower_binding.gate_status_mix`

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

- Part 0: governance / gate / approval / update-policy / field-dictionary level
- Horizontal System: master-data / audit-lineage / decision-rule level
- Part 1: search / region / listing / transaction / channel level
- Part 2: listing snapshot / sold transaction / review level
- Part 3: supplier / RFQ / route / shipment event level
- Part 4: channel / traffic / ROI / readiness level
- Part 5: operating / experiment / inventory / alert level

Granularity is now also explicit in every section via:

- `analysis_grain`
- `entity_grain`
- `time_grain`

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

- [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- [part4.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4.py)
- [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
