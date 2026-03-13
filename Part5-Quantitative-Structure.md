# Part 5 Quantitative Structure

## 目的

第五部分的目标不是描述“上线后继续运营”，而是把上线后的经营动作固化成一套可复用、可量化、可监控、可回滚的经营系统。

这一部分固定回答六个问题：

- 上线后看什么
- 异常发生时怎么发现
- 增长动作如何验证
- 利润如何被持续保护
- 库存和现金流如何不失控
- 什么条件下可以扩张或必须止损

第五部分的核心输出必须是：

- 运营门禁与阶段目标
- 日 / 周 / 月 KPI 体系
- 增长、价格、库存、风险四套监控模型
- 实验与增量验证体系
- 预警、回滚与扩张节奏机制

---

## 范围边界与未指定项

第五部分覆盖的是商品已经进入北美并开始销售之后的持续经营阶段，重点覆盖：

- 运营监控
- 增长优化
- 定价与促销控制
- 履约与库存管理
- 实验体系
- 风险预警与扩张节奏

如果以下信息在具体项目中没有补齐，必须在报告中显式标记为 `未指定`，并进入情景参数：

- 用户级订单数据可得性
- 新客 / 老客识别能力
- 广告归因粒度
- 真实退款 / 争议 / 质保数据可得性
- 海外库存和在途库存粒度
- 渠道费用版本
- 团队人力和预算上限
- 扩张阶段目标

这一条是第五部分的硬规则：缺少输入时允许做区间判断，不允许给出过度确定的点估计承诺。

---

## 固定交付物

第五部分建议固定输出以下交付件：

1. `运营 KPI 门禁表`
2. `日 / 周 / 月经营监控面板`
3. `增长漏斗与留存分析模板`
4. `价格与促销保护规则`
5. `库存、履约与现金周转监控模板`
6. `实验注册表与实验结果审计包`
7. `异常预警与回滚规则`
8. `扩张与缩减节奏表`

---

## Go / No-Go / Pause 门禁

建议第五部分把上线后经营统一落到一套固定门禁，再输出阶段建议。

### 建议门禁项

- `contribution_margin_guardrail`
  - P50 情景下贡献毛利必须高于最小阈值
- `cash_burn_controlled`
  - 广告、库存和售后共同作用后的现金消耗不能突破预算上限
- `inventory_risk_contained`
  - 缺货率与积压风险必须处于可控带内
- `return_dispute_within_band`
  - 退款、退货、拒付、索赔不能持续侵蚀毛利缓冲
- `experiment_readiness_present`
  - 关键增长动作必须能通过实验或增量测量验证
- `policy_blocker_absent`
  - 不存在平台、税务或履约制度上的硬阻断

### 建议输出字段

- `operating_status`
- `gate_results`
- `paused_by`
- `rollback_actions`
- `scale_up_status`

---

## 标准输入表

第五部分建议复用前四部分的数据表，并新增持续经营所需的核心表。

### 复用前序章节表

- `listing_snapshots`
  - 用于货架、评分、促销、平台状态快照
- `sold_transactions`
  - 用于成交、价格、订单、退款代理
- `product_catalog`
  - 用于 SKU 和属性聚合
- `landed_cost_scenarios`
  - 来自 Part 3，用于利润和现金流情景
- `channel_rate_cards`
  - 来自 Part 4，用于平台、支付、仓储、履约费用
- `marketing_spend`
  - 用于投放与获客成本
- `traffic_sessions`
  - 用于流量漏斗
- `returns_claims`
  - 用于退款、退货、争议、售后
- `customer_cohorts`
  - 用于复购和留存
- `inventory_positions`
  - 用于库存与履约
- `experiment_registry`
  - 用于实验管理与审计

### 第五部分新增核心表

- `kpi_daily_snapshots.csv`
  - `date, channel, revenue, contribution_profit, ad_spend, refunds, disputes, inventory_value, operating_status`
  - 用于经营快照和异常检测

- `pricing_actions.csv`
  - `date, channel, sku_id, action_type, old_price, new_price, promo_flag, bundle_flag, owner`
  - 用于价格动作与促销审计

- `reorder_plan.csv`
  - `date, sku_id, warehouse, reorder_point, safety_stock, target_cover_days, planned_units, eta`
  - 用于补货与断货预警

- `policy_change_log.csv`
  - `platform, policy_type, effective_date, source_url, impact_level, change_summary`
  - 用于平台政策版本化和风险审计

- `cash_flow_snapshots.csv`
  - `date, channel, receivable, payable, inventory_cash_lock, ad_cash_out, refund_cash_out`
  - 用于现金流与营运资本监控

### 可选扩展表

- `attribution_events.csv`
  - `user_id, session_id, event_time, channel, source, campaign, event_type, order_id`
- `subscription_events.csv`
  - `customer_id, start_date, renewal_date, cancel_date, channel, sku_id`
- `warranty_cases.csv`
  - `case_id, sku_id, open_date, close_date, issue_type, cost_amount`

如果拿不到 `attribution_events` 或 `customer_id`，则留存建模与增量归因必须降级为 `low_confidence` 或 `未指定`。

---

## 数据降级与代理规则

第五部分对真实经营数据依赖最强，因此必须显式规定字段缺失时的处理方式。

### 建议固定规则

- 缺 `customer_id`
  - `LTV`、复购生命周期模型降级为 cohort 粒度估算
- 缺 `new_customer_flag`
  - `CAC` 只能计算平台报表口径，标记 `new_customer_identification_unavailable`
- 缺 `return_reason`
  - 售后优化只能做损失分布，不做原因分层
- 缺 `inventory_eta`
  - 补货模型必须进入宽区间情景
- 缺 `policy_change_log`
  - 平台风险监控结论降级为 `medium_confidence`
- 缺 `experiment_assignment`
  - 增量判断只能做前后对比，标记 `causal_inference_limited`

### 建议输出字段

- `data_availability_flags`
- `proxy_usage_flags`
- `confidence_downgrade_reason`
- `model_blockers`

---

## 章节结构

### `5.1 运营目标与门禁指标设计`

建议输出指标：

- `primary_kpi_set`
- `guardrail_kpi_set`
- `phase_goal_alignment_score`
- `gate_breach_rate`
- `operating_health_score`

建议重点：

- 试运营、稳定运营、放量运营三阶段指标不应混用
- 每个渠道的主指标和红线指标必须区分

### `5.2 数据体系与持续监控机制`

建议输出指标：

- `data_coverage_score`
- `refresh_latency_hours`
- `metric_consistency_score`
- `fee_version_coverage`
- `policy_monitoring_completeness`

建议重点：

- 数据不是越多越好，而是关键经营指标必须稳定可复现
- 所有费用和政策结论必须可追溯到版本

### `5.3 获客、转化与留存增长机制`

建议输出指标：

- `traffic_mix`
- `funnel_conversion_matrix`
- `new_customer_efficiency`
- `repeat_rate`
- `retention_curve`
- `growth_leverage_score`

建议重点：

- 区分冷启动增长动作和放量阶段增长动作
- 将复购和留存从“附加项”提升为经营指标

### `5.4 定价、促销与利润保护策略`

建议输出指标：

- `price_realization_rate`
- `promo_dependency_score`
- `bundle_uplift`
- `discount_depth_band`
- `margin_protection_score`

建议重点：

- 促销不是默认动作，必须受利润保护规则约束
- 区分健康促销和依赖促销

### `5.5 履约、库存与现金周转管理`

建议输出指标：

- `inventory_days`
- `stockout_risk`
- `overstock_risk`
- `fill_rate`
- `cash_lock_days`
- `reorder_readiness_score`

建议重点：

- 库存问题必须和现金周转一起判断
- 补货策略应以区间和预警机制表达，而不是单点预测

### `5.6 增量实验与持续优化机制`

建议输出指标：

- `experiment_coverage_ratio`
- `mde_attainability_score`
- `lift_realization_rate`
- `test_velocity`
- `causal_confidence_score`

建议重点：

- 不是所有优化都值得实验
- 要优先实验高影响、高不确定性动作

### `5.7 风险监控、复盘机制与扩张节奏`

建议输出指标：

- `risk_alert_count`
- `rollback_trigger_rate`
- `scale_readiness_score`
- `expansion_gate_status`
- `operating_stability_score`

建议重点：

- 扩张决策应由数据门禁触发，而不是情绪驱动
- 必须保留回滚规则和阶段退出路径

---

## 核心量化模型

### 1. 经营健康评分模型

建议以阶段目标、利润、库存、售后和实验能力共同构建：

```text
operating_health_score
= 0.30 * profit_safety
+ 0.20 * traffic_quality
+ 0.20 * inventory_stability
+ 0.15 * customer_retention
+ 0.15 * experimentation_readiness
```

### 2. 增长漏斗与复购模型

建议固定拆成：

- `impression -> click`
- `click -> session`
- `session -> add_to_cart`
- `add_to_cart -> checkout`
- `checkout -> order`
- `order -> repeat_order`

如用户级数据可得，可扩展：

- cohort 留存
- repeat interval
- channel-level LTV

### 3. 价格与促销保护模型

建议输出：

- 正价贡献毛利
- 促销后贡献毛利
- 促销引起的销量 uplift
- 促销依赖度
- 回到正价后的利润恢复速度

### 4. 库存与现金周转模型

建议输出：

- 日均消耗速度
- 安全库存
- 补货点
- 覆盖天数
- 资金占用
- 库存变现压力

### 5. 异常检测与预警模型

建议优先监控：

- 广告成本突然上升
- 转化率断崖下滑
- 退款率突然上升
- 缺货与积压
- 差评异常增加

建议方法：

- rolling z-score
- STL 残差异常
- changepoint detection

### 6. 实验与增量验证模型

建议输出：

- 实验优先级
- 样本量与运行时长
- uplift
- 置信区间
- 是否达成停止规则
- 是否可推广

---

## 流量先验与试点替换规则

第五部分需要明确：很多经营动作在刚上线时数据很少，因此必须允许“试点数据替换先验”。

### 建议规则

- 冷启动 30 天内允许使用试点期漏斗均值作为先验
- 一旦累计订单达到阈值，必须切换到真实观测值
- 若真实值和先验偏差超过阈值，触发重新估算和预算调整

### 建议输出

- `prior_source`
- `prior_replaced_flag`
- `prior_vs_observed_gap`
- `model_refresh_triggered`

---

## 库存、履约与现金周转

建议第五部分把这部分当成经营硬约束，不再只做辅助分析。

### 建议量化

- `days_of_cover`
- `stockout_probability`
- `overstock_probability`
- `cash_conversion_cycle_proxy`
- `fulfillment_stability_score`

### 建议公式

```text
days_of_cover = on_hand_units / daily_sell_through
reorder_point = lead_time_demand + safety_stock
inventory_cash_lock = inventory_value / daily_revenue
```

### 建议重点

- 所有扩张动作必须经过库存和现金周转门禁
- 所有库存结论都必须带情景区间

---

## 定价与促销保护规则

建议第五部分将“价格动作”纳入正式审计范围。

建议固定记录：

- 谁发起价格动作
- 哪个渠道
- 哪个 SKU
- 调整前后价格
- 是否伴随赠品 / 套餐 / 优惠券
- 调整后的利润变化
- 调整后的转化变化

### 建议输出

- `pricing_action_log`
- `promo_dependency_band`
- `margin_floor_breach_count`
- `price_action_effectiveness`

---

## 风险与合规边界

第五部分需要持续监控的不是“静态合规”，而是“经营中的合规与平台风险”。

建议重点监控：

- 平台费率变化
- 平台政策调整
- 税务责任变化
- 退款与拒付机制变化
- 质保和售后政策变化

建议固定输出：

- `policy_change_risk_level`
- `fee_version_gap_flags`
- `refund_dispute_risk_score`
- `operating_compliance_alerts`

---

## 仪表盘组件

### 渠道级

- 收入
- 贡献毛利
- 广告支出
- 转化率
- 退款率
- 库存覆盖天数

### 运营级

- 周度经营健康分
- 门禁触发次数
- 预算扩张与回撤状态
- 经营异常告警

### 实验级

- 实验运行状态
- 预计结束时间
- 当前 uplift
- 是否已达样本量
- 是否达到停止规则

---

## 审计包与复现清单

第五部分建议固定保留下列复现材料：

- 数据源与权限说明
- 费用版本与政策版本
- 指标口径表
- 模型版本号
- 异常预警日志
- 实验注册与结果记录
- 回滚记录
- 周报与月报快照

---

## 报告构建建议

建议第五部分每次实际输出时，按以下顺序写：

1. 当前经营状态
2. 当前最重要的增长机会
3. 当前最重要的利润风险
4. 当前最重要的库存 / 现金流风险
5. 当前最优实验动作
6. 当前是否可以扩张

这样第五部分不会写成运营流水账，而会始终围绕“经营决策”展开。

---

## 后续代码模块建议

如果进入量化开发，建议第五部分拆成以下模块：

- `part5_pipeline.py`
- `part5_metrics.py`
- `part5_experiments.py`
- `part5_alerts.py`
- `part5_forecasting.py`
- `part5.py`

建议与 Part 1-4 保持一致：

- 标准输入表
- 标准报告 contract
- uncertainty
- validation
- charts
- CLI

---

## 环境依赖建议

第五部分后续量化开发建议准备以下 Python 依赖：

- `numpy`
- `pandas`
- `scipy`
- `statsmodels`
- `matplotlib`
- `scikit-learn`
- `cvxpy`

这些依赖分别用于：

- 数据处理
- 统计建模
- 时间序列分解
- 优化与预算分配
- 实验与异常检测

---

## 当前定位

这份文档当前的定位是：

- 它是第五部分的量化结构稿
- 它把“上线后经营”正式拆成标准输入、标准指标和标准模型
- 它为 Part 5 后续代码开发提供了统一接口
- 它和 Part 1-4 的结构语言保持一致
