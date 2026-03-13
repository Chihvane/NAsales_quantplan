# Part 3 Quantitative Structure

## Purpose

Part 3 focuses on Chinese supply-side execution rather than market demand.  
It answers:

- whether China has a mature supplier base for the target category
- what the real RFQ price structure looks like
- what compliance gates must be cleared before North America launch
- which export and fulfillment path is operationally strongest
- whether landed cost still leaves enough margin after channel fees
- whether the category should move into pilot order, scale order, or hold

## Standard Input Tables

The current implementation uses six canonical CSV tables:

- `suppliers.csv`
  - `supplier_id, supplier_name, supplier_type, region, factory_flag, oem_flag, odm_flag, main_category, moq, sample_days, production_days, capacity_score, compliance_support_score`
- `rfq_quotes.csv`
  - `supplier_id, sku_version, incoterm, moq_tier, unit_price, sample_fee, tooling_fee, packaging_cost, customization_cost, currency, quote_date`
- `compliance_requirements.csv`
  - `market, category, requirement_type, requirement_name, mandatory_flag, estimated_cost, estimated_days, risk_level, notes`
- `logistics_quotes.csv`
  - `route_id, origin, destination, shipping_mode, incoterm, quote_basis, cost_value, currency, lead_time_days, volatility_score, quote_date`
- `tariff_tax.csv`
  - `market, hs_code, base_duty_rate, additional_duty_rate, brokerage_fee, port_fee, effective_date`
- `shipment_events.csv`
  - `shipment_id, supplier_id, shipping_mode, etd, eta, customs_release_date, warehouse_received_date, sellable_date, delay_days, issue_type`

## Section Structure

- `3.1 中国供应端结构分析`
  - supplier type share
  - regional share
  - factory / OEM / ODM share
  - average MOQ and lead time
  - supply maturity score
- `3.2 国内采购与报价策略分析`
  - incoterm median quoted cost
  - factory vs trader price gap
  - MOQ quote curve
  - best quote leaderboard
- `3.3 合规、认证与准入门槛分析`
  - mandatory requirement count
  - mandatory estimated cost
  - mandatory estimated days
  - risk distribution
  - gating requirements
- `3.4 出口路径与物流履约分析`
  - route score ranking
  - shipping mode mix
  - average actual lead time
  - on-time rate / customs delay rate
- `3.5 到岸成本与利润安全边际分析`
  - landed cost by scenario
  - best scenario breakdown
  - break-even price
  - margin safety level
  - Monte Carlo margin band
- `3.6 风险矩阵与应对策略`
  - priority risks
  - severity score
  - overall risk level
- `3.7 推荐进入路径与首批执行方案`
  - recommendation enum
  - recommended supplier
  - recommended path
  - first batch units
  - next 90-day actions

## Assumptions

Part 3 currently uses these assumptions:

- `target_market`
- `target_sell_price`
- `target_order_units`
- `channel_fee_rate`
- `marketing_fee_rate`
- `return_rate`
- `return_cost_per_unit`
- `working_capital_rate`

## Report Builder

- main builder: [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- metrics: [part3_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_metrics.py)
- data loader: [part3_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_pipeline.py)
- uncertainty: [uncertainty.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/uncertainty.py)
- validation: [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)

## CLI

Build report:

```bash
python3 -m quant_framework.cli report-part3 --data-dir examples/part3_demo --output-json /tmp/part3_report.json
```

Generate charts:

```bash
python3 -m quant_framework.cli charts-part3 --data-dir examples/part3_demo --output-dir /tmp/part3_charts
```

Run demo:

```bash
python3 examples/run_part3_demo.py
```

Clean a raw RFQ export into the Part 3 standard table:

```bash
python3 -m quant_framework.cli clean-part3 --table rfq --input-csv examples/raw_part3_rfq_export.csv --output-csv /tmp/rfq_quotes.csv
```

Run the raw-to-report cleaning demo:

```bash
python3 examples/run_part3_cleaning_demo.py
```

## Current Demo Outputs

The demo writes:

- JSON report
- `supplier_type_share.svg`
- `incoterm_median_cost.svg`
- `landed_cost_breakdown.svg`
- `risk_priority.svg`
- `monte_carlo_margin_band.svg`

to [examples/output_part3](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part3).
