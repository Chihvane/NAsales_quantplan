# Part 1 Unified Chain

## 定位

`Part 1` 是市场进入筛选层，也是当前系统正在升级的 `Market Quant Engine`。

## 核心问题

- 北美市场是否值得进入
- 需求是否真实、持续、稳定
- 用户、渠道、价格带是否支持商业化进入
- 这些结论是否达到可接 Gate 的颗粒度

## 统一链条

### 1. 框架层

章节固定为：

- `1.1` 市场现状与需求概览
- `1.2` 客户画像分析
- `1.3` 市场规模分析
- `1.4` 购买渠道分析
- `1.5` 货架商品价格分析
- `1.6` 实际成交价格分析

### 2. 量化层

标准输入：

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

关键治理与因子输出：

- `source_health`
- `event_analysis`
- `threshold_coverage_ratio`
- `gate_results`
- `factor_snapshots`

当前标准因子已覆盖：

- `FAC-MARKET-ATTRACT`
- `FAC-DEMAND-STABILITY`
- `FAC-CUSTOMER-FIT`
- `FAC-CHANNEL-EFFICIENCY`
- `FAC-CHANNEL-RISK`
- `FAC-PRICE-REALIZATION`

### 3. 代码层

- [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py)
- [pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/pipeline.py)

### 4. 回测与桥接层

- 已有 Part 1 demo 回测
- 已有 `Part 1 + Part 2 -> Decision OS` bridge
- 已能产出 `factor_panel`

桥接产物：

- [integrated_market_product_bundle.json](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts/decision_os_bridge/integrated_market_product_bundle.json)
- [integrated_factor_panel.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/artifacts/decision_os_bridge/integrated_factor_panel.csv)

### 5. 决策层

`Part 1` 不负责供应链、上架和放量决策，但负责提供：

- 市场进入 readiness
- 市场吸引力因子
- 需求稳定因子
- 渠道效率与风险因子

## 当前状态

- 已有框架稿
- 已有量化结构
- 已有优化计划
- 已有方法验证
- 已完成深度优化
- 已形成持续量化升级方向
- 已与 `Part 2`、`Decision OS` 串联

## source references

- [Part1-Market-Research-Framework-Outline.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Market-Research-Framework-Outline.md)
- [Part1-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Quantitative-Structure.md)
- [Part1-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Quantitative-Optimization-Plan.md)
- [Part1-Continuous-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Continuous-Optimization-Crosswalk.md)
- [Part1-Methodology-Reliability-Validation.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Methodology-Reliability-Validation.md)
- [Part1-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Deep-Optimization-Crosswalk.md)
- [Part1-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Part1-README.md)
