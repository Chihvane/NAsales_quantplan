# Part 4 Quantitative Structure

## 目的

第四部分的目标不是描述“可以卖”，而是把北美销售进入决策变成一套可复用、可量化、可审计的门禁系统。

这一部分固定回答六个问题：

- 能不能卖
- 在哪卖
- 先卖哪个渠道
- 先试什么
- 何时放大
- 何时止损

第四部分的核心输出必须是：

- 渠道级 P&L
- Go / No-Go 门槛
- 获客与留存指标体系
- 试点实验与增量测量方案
- ROI 蒙特卡洛情景

---

## 范围边界与未指定项

第四部分覆盖三类销售路径：

- DTC / 独立站
- 平台电商
- 线下 B2B / 经销商

如果以下信息在具体项目中没有补齐，必须在报告中显式标记为 `未指定`，并进入情景参数：

- 目标国家与仓配范围
- 客单价目标区间
- 目标毛利区间
- 团队能力边界
- 预算上限
- 新客识别能力
- 用户级订单或路径数据可得性
- 真实订单级退货 / 拒付数据可得性

这一条是第四部分的硬规则：缺少这些输入时，允许做区间判断，不允许给出点估计承诺。

---

## 固定交付物

第四部分建议固定输出以下交付件：

1. `Go / No-Go 决策门禁表`
2. `渠道级 P&L 模板`
3. `获客与留存 KPI 字典`
4. `渠道实验设计包`
5. `费用版本化清单`
6. `ROI 情景与敏感性分析`
7. `90 天销售执行方案`
8. `审计包与复现清单`

---

## Go / No-Go 门禁

建议第四部分把所有渠道都落到同一套门禁条件，再输出最终推荐。

### 建议门禁项

- `contribution_margin_positive`
  - P50 情景下单件贡献毛利必须为正
- `loss_probability_controlled`
  - P10 或蒙特卡洛亏损概率必须低于阈值
- `payback_within_target`
  - CAC 回本期必须小于目标窗口
- `return_risk_within_band`
  - 退款 / 退货 / 拒付风险不能吞噬全部利润缓冲
- `inventory_risk_contained`
  - 缺货与库存积压风险必须可被安全库存策略承接
- `compliance_blocker_absent`
  - 不存在税务、平台政策或售后制度上的硬阻断

### 建议输出字段

- `go_no_go_status`
- `gate_results`
- `blocked_by`
- `risk_adjusted_recommendation`

---

## 标准输入表

第四部分建议在前三部分 schema 的基础上复用并新增以下表。

### 复用前序章节表

- `listing_snapshots`
  - 用于平台货架结构、价格带、竞争密度、卖点结构
- `sold_transactions`
  - 用于历史成交价、销量、平台偏好、退款代理分析
- `product_catalog`
  - 用于 SKU 结构、属性分层、品牌化空间判断
- `landed_cost_scenarios`
  - 来自 Part 3
  - 用于所有渠道 P&L 中的 `landed_cost`

### 第四部分新增核心表

- `channel_rate_cards.csv`
  - `channel, fee_type, fee_basis, fee_rate, fixed_fee, effective_date, source_ref, notes`
  - 用于平台费率、支付费率、退款管理费、仓储费、履约费

- `marketing_spend.csv`
  - `date, channel, campaign_id, traffic_source, spend, impressions, clicks, attributed_orders, attributed_revenue`
  - 用于投放和基础归因

- `traffic_sessions.csv`
  - `date, channel, traffic_source, sessions, product_page_views, add_to_cart, checkout_start, orders`
  - 用于漏斗

- `returns_claims.csv`
  - `date, channel, order_id, sku_id, return_flag, refund_amount, return_reason, claim_cost, dispute_flag`
  - 用于退款、售后、拒付成本

- `customer_cohorts.csv`
  - `cohort_month, channel, customers, repeat_customers, repeat_orders, repeat_revenue`
  - 用于复购和 LTV

- `inventory_positions.csv`
  - `date, channel, warehouse, sku_id, on_hand_units, inbound_units, sell_through_units, storage_cost`
  - 用于库存、仓储和现金占用

- `experiment_registry.csv`
  - `experiment_id, channel, hypothesis, start_date, end_date, primary_metric, mde, split_ratio, stop_rule, status`
  - 用于 A/B、平台 split test、增量实验审计

### 可选扩展表

- `b2b_accounts.csv`
  - `account_id, account_type, region, discount_rate, payment_terms_days, rebate_rate, annual_target`
- `attribution_events.csv`
  - `user_id, session_id, event_time, channel, source, campaign, event_type, order_id`

如果拿不到 `attribution_events`，则多触点归因只允许标记为 `未指定` 或 `low_confidence`。

---

## 数据降级与代理规则

第四部分比前三部分更依赖真实订单和营销数据，因此必须显式规定“字段拿不到怎么办”。

### 建议固定规则

- 缺 `new_customer`：
  - `CAC` 可计算为平台报表口径，但必须标注 `new_customer_identification_unavailable`
- 缺 `customer_id`：
  - `LTV` 只能做粗估或 cohort 级估算，标注 `ltv_data_limited`
- 缺 `sold_transaction.qty`：
  - 可用订单数或销量代理做探索性判断，但必须降级为 `exploratory_only`
- 缺 `return_reason / claim_cost`：
  - 退款和售后只能做区间模拟，不能做点估计
- 缺 `attribution_events`：
  - 归因优先退化为平台内实验和增量测试

### 建议输出字段

- `data_availability_flags`
- `proxy_usage_flags`
- `confidence_downgrade_reason`

---

## 章节结构

### `4.1 独立站模式可行性分析`

建议输出指标：

- `brandability_score`
- `content_driven_conversion_fit`
- `dtc_aov_support`
- `owned_data_value_score`
- `site_launch_complexity`
- `dtc_channel_pnl`

建议重点：

- 是否适合作为首发渠道
- 是否更适合作为品牌沉淀渠道
- 是否对内容和付费流量依赖过强

### `4.2 平台电商模式可行性分析`

建议按平台拆分：

- Amazon
- TikTok Shop
- eBay
- Walmart

建议输出指标：

- `platform_fit_score`
- `platform_cost_stack`
- `platform_conversion_potential`
- `platform_competition_pressure`
- `platform_launch_complexity`
- `platform_channel_pnl`

建议重点：

- 平台优先级
- 白牌 / 品牌 / 长尾切入方式
- 平台费率和广告依赖风险

### `4.3 线下经销商与 ToB 模式分析`

建议输出指标：

- `dealer_fit_score`
- `offline_dependency_score`
- `b2b_margin_spread`
- `rebate_and_terms_pressure`
- `account_complexity_score`
- `b2b_channel_pnl`

建议重点：

- 是否必须依赖线下体验或安装售后
- 是否能承受返点、账期、库存与渠道冲突

### `4.4 曝光、获客与流量结构分析`

建议输出指标：

- `traffic_source_mix`
- `traffic_efficiency_index`
- `owned_vs_paid_share`
- `first_touch_mix`
- `paid_media_dependency`
- `channel_exposure_funnel`

建议重点：

- 初期流量是否必须依赖广告
- 哪些流量适合冷启动
- 哪些流量适合放大阶段

### `4.5 转化效率与 ROI 模型分析`

建议输出指标：

- `ctr`
- `session_rate`
- `atc_rate`
- `checkout_rate`
- `conversion_rate`
- `aov`
- `gross_margin_rate`
- `cac`
- `roas`
- `ltv`
- `payback_period`
- `unit_contribution_margin`
- `channel_roi`

建议重点：

- 哪个渠道能先回本
- 哪个渠道适合测试
- 哪个渠道会出现“有流量但利润不成立”

### `4.6 运营门槛与组织能力要求分析`

建议输出指标：

- `content_ops_gap_score`
- `ad_ops_gap_score`
- `store_ops_gap_score`
- `cs_and_after_sales_gap_score`
- `localization_gap_score`
- `team_readiness_score`

建议重点：

- 当前团队能否承接该渠道
- 是否必须补本地仓、本地客服或投放能力

### `4.7 推荐进入路径与 90 天销售执行方案`

建议输出指标：

- `go_no_go_status`
- `launch_channel_priority`
- `second_stage_channel_priority`
- `budget_allocation_plan`
- `pilot_kpi_targets`
- `expansion_trigger_rules`
- `stop_loss_rules`

建议重点：

- 首发渠道
- 次级渠道
- 试点 KPI
- 放大和止损条件

---

## 费用版本化

第四部分和前三部分最大的差别，是平台费率和政策会持续变化。

因此所有渠道 P&L 都必须使用 `fee versioning`，不能把费率硬编码成固定常量。

### 建议最小版本字段

- `channel`
- `fee_type`
- `effective_date`
- `source_ref`
- `applies_to`
- `notes`

### 建议规则

- 费用版本要和报告生成时间绑定
- 每次生成报告时保留费率版本号
- 费用变动应进入敏感性分析和 Monte Carlo

---

## 渠道级 P&L 模型

第四部分建议统一落到两层：

- 单件贡献毛利
- 渠道级贡献利润

### 通用单件贡献毛利

```text
unit_contribution =
net_revenue
- landed_cost
- channel_fees
- fulfillment_cost
- storage_cost
- refund_and_return_cost
- payment_cost
- acquisition_cost_per_order
```

其中：

- `landed_cost` 直接来自 Part 3 的 `landed_cost_scenarios`
- `channel_fees` 来自 `channel_rate_cards`
- `acquisition_cost_per_order` 来自 `marketing_spend / attributed_orders`

### 渠道公式

#### DTC / 独立站

```text
contribution_dtc =
price_after_discount
- landed_cost
- payment_fee
- 3pl_or_shipping_cost
- returns_cost
- dispute_cost
- cac
```

#### Amazon FBA

```text
contribution_amazon_fba =
price
- landed_cost
- referral_fee
- fba_fulfillment_fee
- storage_fee
- ads_cost
- returns_cost
```

#### TikTok Shop

```text
contribution_tiktok =
price
- landed_cost
- referral_fee
- fulfill_cost
- ads_or_affiliate_cost
- refund_admin_cost
```

#### eBay

```text
contribution_ebay =
price
- landed_cost
- final_value_fee
- promoted_listing_cost
- shipping_cost
- returns_cost
```

#### Walmart

```text
contribution_walmart =
price
- landed_cost
- referral_fee
- wfs_fulfillment_fee
- wfs_storage_fee
- ads_cost
- returns_cost
```

#### B2B / 经销

```text
contribution_b2b =
wholesale_price
- landed_cost
- rebate_cost
- claims_cost
- sales_ops_cost
- working_capital_cost
```

---

## 核心量化模型

### 1. 渠道组合优化

目标：

```text
max E[profit] - lambda * Var(profit)
```

约束建议：

- 总预算上限
- 单渠道预算上限
- 缺货概率上限
- 平台依赖上限
- 团队执行容量上限

建议输出：

- `optimal_budget_mix`
- `risk_adjusted_profit`
- `channel_dependency_index`

### 2. 漏斗与转化模型

统一漏斗：

```text
impressions -> clicks -> sessions -> add_to_cart -> checkout -> orders
```

建议指标：

- `ctr = clicks / impressions`
- `session_rate = sessions / clicks`
- `atc_rate = add_to_cart / sessions`
- `checkout_rate = checkout_start / add_to_cart`
- `cvr = orders / sessions`

### 3. LTV / CAC

建议最小可行口径：

```text
LTV = expected_repeat_orders * contribution_per_order
CAC = total_acquisition_cost / new_customers
payback = CAC / contribution_in_payback_window
```

若缺少用户级购买历史：

- 输出 `ltv_data_limited`
- 改为 cohort 级估算

### 4. 归因与增量

推荐优先级：

1. 平台内实验
2. 增量测试
3. 多触点归因

建议输出：

- `incremental_lift`
- `attribution_confidence`
- `causal_readiness`

如果无法随机化但有明确干预时点，可退化为 DiD。

### 5. A/B 与 Split Test

建议实验对象：

- 价格
- 素材
- 标题 / listing
- 套装结构
- 广告受众
- 交期 / 免邮门槛 / 退货政策

建议固定输出：

- `experiment_id`
- `primary_metric`
- `mde`
- `sample_size`
- `lift`
- `confidence_interval`
- `stop_rule`
- `decision`

### 6. ROI 蒙特卡洛

建议随机化变量：

- `landed_cost`
- `cvr`
- `refund_rate`
- `ad_cost`
- `aov`
- `storage_cost`
- `platform_fee_shift`

建议输出：

- `roi_p10`
- `roi_p50`
- `roi_p90`
- `loss_probability`
- `payback_probability`

---

## 流量先验与试点替换规则

第四部分可以使用行业先验来设定初始区间，但不能把行业基准当作最终结论。

### 建议规则

- 所有 CTR / CVR / CAC 先验都要标记为 `assumption_only`
- 一旦进入试点阶段，必须用真实渠道数据替换
- 先验只能用于设定预算边界和样本量，不可直接用于承诺 ROI

### 建议输出

- `prior_assumption_table`
- `replaced_by_real_data_at`
- `assumption_confidence_level`

---

## 库存、履约与现金周转

第四部分必须把库存和现金周转纳入渠道判断，否则会系统性高估“卖得出去”的价值。

### 建议量化

- `days_of_inventory`
- `inventory_turnover`
- `stockout_probability`
- `safety_stock_units`
- `reorder_point`
- `cash_conversion_cycle`
- `avg_inventory_units`

### 建议公式

```text
reorder_point = avg_demand_during_lead_time + safety_stock
```

```text
cash_conversion_cycle = inventory_days + receivable_days - payable_days
```

```text
avg_inventory_units = daily_sales * days_of_inventory
```

### 建议重点

- FBA / WFS 仓储费要进入情景成本
- 3PL / 自发货要显式计入履约与售后成本
- B2B 账期要单独进入 working capital

---

## 定价与促销保护规则

第四部分建议固定三条价格线：

- `floor_price`
  - 用高成本情景保护最低可卖价
- `target_price`
  - 对齐 Part 2 的成交甜蜜带
- `acquisition_price`
  - 仅在增量 ROI 为正时短期使用

### 建议输出

- `floor_price`
- `target_price`
- `acquisition_price`
- `promotion_lift`
- `cannibalization_check`

---

## 风险与合规边界

第四部分建议固定纳入以下风险：

- 平台费率变动风险
- 平台政策变动风险
- 税务注册与代征风险
- 退款 / 退货 / 拒付风险
- 广告投产崩塌风险
- 缺货与仓储费放大风险
- 组织执行不足风险

建议输出：

- `channel_policy_risk_score`
- `tax_and_compliance_risk_score`
- `return_risk_score`
- `inventory_risk_score`
- `execution_risk_score`

---

## 仪表盘组件

第四部分建议固定输出三类可视化。

### 渠道级

- GMV
- 贡献毛利
- 费用拆解瀑布图
- CAC
- ROAS
- 退款 / 退货率

### 运营级

- 库存周转
- 缺货率
- 仓储费
- 现金占用
- 补货预警

### 实验级

- uplift
- confidence interval
- 运行天数
- 是否达成停止规则

---

## 审计包与复现清单

第四部分建议固定输出以下审计信息：

1. 费率版本
2. 成本版本
3. 渠道假设版本
4. 税务与政策口径
5. 归因口径
6. ROI 公式口径
7. 实验注册表
8. 停止规则
9. 敏感性分析
10. 缺失数据清单

---

## 报告构建建议

第四部分后续代码建议拆成以下模块：

- `part4_pipeline.py`
  - 读取第四部分标准输入
- `part4_metrics.py`
  - 计算渠道效率、P&L、ROI、LTV/CAC、库存与组织匹配等指标
- `part4_simulation.py`
  - 渠道级蒙特卡洛 ROI
- `part4_experiments.py`
  - A/B、split test、增量评估模板
- `part4.py`
  - 装配标准化报告

后续输出结构应对齐现有统一 contract：

- `metadata`
- `overview`
- `sections`
- `uncertainty`
- `validation`

---

## 后续开发顺序

建议下一步按下面顺序推进：

1. 固定第四部分标准输入表
2. 开发渠道级 P&L 模型
3. 开发 Go / No-Go 门禁
4. 开发 ROI 与蒙特卡洛
5. 开发实验与归因模板
6. 最后开发图表与 demo

---

## 当前定位

这份文件是第四部分的优化版量化结构稿。

它的作用是：

- 让 Part 4 进入可以 coding 的状态
- 让 Part 4 和 Part 1 / Part 2 / Part 3 的颗粒度一致
- 为后续渠道级 P&L、实验、ROI 与仪表盘开发提供统一规范
