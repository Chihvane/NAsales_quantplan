# Part 2 Quantitative Structure

## Purpose

Part 2 focuses on SKU-level competitive evidence rather than market sizing.  
It answers:

- what sells
- at what realized prices
- which attributes overperform supply
- which review themes create drag
- which listings survive on shelf

## Standard Input Tables

The current implementation uses four canonical CSV tables:

- `listing_snapshots.csv`
  - `platform, listing_id, canonical_sku, brand, seller_id, captured_at, list_price, sale_price, currency, shipping_fee, rating_avg, review_count, sold_count_window, sales_rank, active_flag, seller_type, fulfillment_type`
- `sold_transactions.csv`
  - `platform, sold_id, listing_id, canonical_sku, sold_at, transaction_price, shipping_fee, units, seller_type`
- `product_catalog.csv`
  - `canonical_sku, brand, category_path, title, attribute_tokens`
- `reviews.csv`
  - `platform, canonical_sku, review_id, review_date, rating, review_text`

These can now be generated directly from raw platform exports through the Part 2 cleaners:

- Amazon raw export -> proxy transactions + listing snapshots
- eBay sold export -> observed transactions + listing snapshots
- TikTok open listing export -> proxy transactions + listing snapshots

## Section Structure

- `2.1 在售商品与成交结构`
  - Top SKU / Top Brand leaderboard
  - platform GMV share
  - brand HHI / CR4
- `2.2 成交价格带与折扣深度`
  - realized price distribution
  - sweet spot band
  - weighted average discount
- `2.3 价格-评分价值矩阵`
  - price quartile × rating bucket matrix
  - strong value clusters
  - risk clusters
- `2.4 属性画像与白空间机会`
  - attribute sku share / gmv share
  - outperformance
  - brand feature coverage
- `2.5 评论情绪与痛点主题`
  - positive / neutral / negative mix
  - top negative themes
  - pain point intensity
- `2.6 货架动态与生存分析`
  - median lifetime
  - survival curve
  - entry / exit velocity
  - price band exit risk

## Report Builder

- main builder: [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- metrics: [part2_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_metrics.py)
- data loader: [part2_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_pipeline.py)
- uncertainty: [uncertainty.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/uncertainty.py)
- validation: [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)

## CLI

Build report:

```bash
python3 -m quant_framework.cli report-part2 --data-dir examples/part2_demo --output-json /tmp/part2_report.json
```

Generate charts:

```bash
python3 -m quant_framework.cli charts-part2 --data-dir examples/part2_demo --output-dir /tmp/part2_charts
```

Run demo:

```bash
python3 examples/run_part2_demo.py
```

Clean a raw platform export into a Part 2 bundle:

```bash
python3 -m quant_framework.cli clean-part2 --platform amazon --input-csv examples/raw_part2_amazon_export.csv --output-dir /tmp/amazon_part2_bundle --capture-date 2025-11-30
```

Merge multiple cleaned bundles:

```bash
python3 -m quant_framework.cli clean-part2 --platform combine --bundle-dirs /tmp/amazon_part2_bundle /tmp/ebay_part2_bundle /tmp/tiktok_part2_bundle --output-dir /tmp/part2_bundle_combined
```

Run the Part 2 backtest demo:

```bash
python3 -m quant_framework.cli backtest-part2-demo --output-dir /tmp/part2_backtest_demo
```

## Current Demo Outputs

The demo writes:

- JSON report
- `top_sku_share.svg`
- `sweet_spot_band.svg`
- `negative_theme_intensity.svg`
- `listing_survival_curve.svg`

to [examples/output_part2](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_part2).

The raw-to-report demo writes cleaned bundles and a combined report to [cleaned_part2_demo](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/cleaned_part2_demo).
