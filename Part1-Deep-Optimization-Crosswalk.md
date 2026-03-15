# Part 1 Deep Optimization Crosswalk

更新时间：2026-03-15

## 本轮执行目标

基于 [deep-research-report (13).md](/Users/zhiwenxiang/Downloads/deep-research-report%20(13).md) 的要求，本轮不再只做 Part 1 的目录与治理占位，而是把 `event_library / source_registry / part1_threshold_registry` 真正接入量化主链。

## 已落地的优化

### 1. 需求章节从静态趋势升级为事件驱动

已在 `1.1` 增加：

- `source_health`
- `event_analysis`
- `demand_strength_score`
- `demand_stability_score`
- `event_sensitivity_score`
- `threshold_coverage_ratio`
- `gate_results`

### 2. 客户画像从分布表升级为可决策分数

已在 `1.2` 增加：

- `customer_fit_score`
- `persona_confidence_score`
- `persona_concentration_score`

### 3. 市场规模章节升级为因子生产层

已在 `1.3` 增加：

- `source_health`
- `market_attractiveness_factor`
- `market_structure_factor`
- `sizing_confidence_band`
- `threshold_coverage_ratio`
- `gate_results`

### 4. 渠道章节升级为效率/风险双因子

已在 `1.4` 增加：

- `source_health`
- `channel_dependency_score`
- `channel_efficiency_factor`
- `channel_risk_factor`
- `threshold_coverage_ratio`
- `gate_results`

### 5. 成交价格章节升级为标准化价格实现因子

已在 `1.6` 增加：

- `price_realization_factor`
- `elasticity_reliability_score`
- `discount_dependency_score`

### 6. Part 1 已输出标准因子快照

主报告新增 `factor_snapshots`，当前输出：

- `FAC-MARKET-ATTRACT`
- `FAC-DEMAND-STABILITY`
- `FAC-CUSTOMER-FIT`
- `FAC-CHANNEL-EFFICIENCY`
- `FAC-CHANNEL-RISK`
- `FAC-PRICE-REALIZATION`

## 当前效果

本轮优化后，Part 1 已从“只输出基础统计”推进到：

- 可绑定证据来源
- 可绑定更新时效
- 可绑定门槛规则
- 可输出 Gate 可消费因子
- 可继续接入 Decision OS 的回测与 market-entry gate

## 还未完成的下一步

下一轮最直接的工作是：

1. 把 `factor_snapshots` 落成正式 `part1_factor_snapshots.csv/json`
2. 把 Part 1 因子接到 `decision-os/backtest`，替换 demo panel 的市场因子输入
3. 把 `event_library` 扩成正式事件库，加入事件标签和归因窗口
