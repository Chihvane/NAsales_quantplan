# Part 4 量化优化计划

更新时间：2026-03-15

## 一、这份计划要解决什么问题

`Part 4` 当前已经具备：

- 渠道级 P&L 拆解
- DTC / 平台 / B2B 三条路径的基础可行性判断
- ROI Monte Carlo 区间模拟
- 风险、回本期、贡献毛利率等门禁
- 统一 `decision_summary`

但它还主要停留在：

> 可产出渠道报告的量化核算器

还没有完全升级成：

> 可做预算组合优化、可做风险调整绩效比较、可做 walk-forward 验证、可直接进入 `Decision OS Gate` 的 `Channel Portfolio Engine`

因此这份计划要解决的不是“再补几个 ROI 指标”，而是六个结构性问题：

1. `Part 4` 当前预算分配更接近启发式打分，还没有真正求解 `E[profit] - lambda * Var(profit)` 这类约束优化问题。
2. Monte Carlo 目前更偏独立扰动，缺少 `macro / ads / logistics / policy` 共同冲击与相关结构，会低估尾部风险。
3. 缺少正式的时间序列风险调整指标，如 `Sharpe / Sortino / Calmar / Ulcer / drawdown duration / turnover`。
4. 缺少正式的分布风险指标，如 `VaR / CVaR / Omega / worst-tail margin`。
5. `Part 4` 与 backtest 主链还没有完全打通，缺少 `walk-forward + train/test + stress suite + gate flip report`。
6. `Part 4` 与 `Decision OS` 的连接仍偏报告摘要级，还没有形成标准化 `channel gate records / portfolio optimizer runs / execution friction records`。

---

## 二、项目回溯后的 Part 4 现状

### 2.1 已经完成的能力

当前 `Part 4` 已经具备这些基础能力：

- 标准输入十二表：
  - `listing_snapshots`
  - `sold_transactions`
  - `product_catalog`
  - `landed_cost_scenarios`
  - `channel_rate_cards`
  - `marketing_spend`
  - `traffic_sessions`
  - `returns_claims`
  - `customer_cohorts`
  - `inventory_positions`
  - `experiment_registry`
  - `b2b_accounts`
- 七个标准章节：
  - `4.1 独立站模式可行性分析`
  - `4.2 平台电商模式可行性分析`
  - `4.3 线下经销商与 ToB 模式分析`
  - `4.4 曝光、获客与流量结构分析`
  - `4.5 转化效率与 ROI 模型分析`
  - `4.6 运营门槛与组织能力要求分析`
  - `4.7 推荐进入路径与 90 天销售执行方案`
- 核心计算能力：
  - 渠道 P&L
  - blended contribution margin
  - ROI Monte Carlo
  - loss probability
  - readiness score
  - recommendation / primary channel / best platform

### 2.2 当前主要缺口

结合这次深研稿与现有代码，`Part 4` 还存在这些明显缺口：

1. **组合优化尚未成型**
   - 本轮已补 `optimal_budget_mix / risk_adjusted_profit / portfolio_constraints / optimizer_runs`，下一步继续接入 `Decision OS` 回测主链。
2. **共同冲击与相关性不足**
   - 本轮已在 Monte Carlo 中加入 `macro / ads / logistics / policy` 共同 shock，降低独立扰动下的尾部风险低估。
3. **时间序列绩效维度不足**
   - 本轮已补 `Sharpe / Sortino / Calmar / Ulcer / drawdown duration` 风险调整指标。
4. **尾部风险维度不足**
   - 本轮已补 `VaR / CVaR / Omega / tail shortfall severity`。
5. **执行摩擦未显式建模**
   - 本轮已补 `turnover penalty / CAC slippage / fee jump / policy jump / execution friction`，并形成 `execution_friction_flags`。
6. **验证协议不完整**
   - 本轮已补 `stress_suite / optimizer_feasibility_report / gate_flip_report`，`walk-forward / train-test` 继续向 `Decision OS` 回测主链下沉。
7. **因子层尚未固定**
   - 本轮已固定 6 个标准 Channel 因子，并输出 `factor_snapshots / confidence_band / proxy_usage_flags`。

---

## 三、Part 4 在整个项目中的新定位

优化后的 `Part 4` 不再只是“销售渠道分析章节”，而是 `Decision OS` 的：

> `Channel Portfolio Engine`

它必须向后续系统输出三类结果：

1. **渠道排序结果**
   - 先打哪个渠道
   - 哪个平台值得试点
   - 哪类渠道只能作为辅助或观察项

2. **风险调整结果**
   - 同样赚 1 元利润，哪个渠道路径承担的回撤、尾部风险和执行摩擦更低
   - 哪种预算组合更稳

3. **因子结果**
   - 标准化 Channel 因子
   - 可进入 `Gate Engine`
   - 可与 Part 3 的成本模型、Part 5 的运营数据联动

---

## 四、优化后的 Part 4 输出目标

### 4.1 章节级输出

每个章节除了章节指标本身，还应统一补齐：

- `source_health`
- `threshold_coverage_ratio`
- `gate_results`
- `confidence_band`
- `proxy_usage_flags`
- `execution_friction_flags`

### 4.2 因子级输出

建议把 `Part 4` 固定输出为 6 个标准因子：

- `FAC-CHANNEL-FIT`
- `FAC-TRAFFIC-EFFICIENCY`
- `FAC-UNIT-ECONOMICS`
- `FAC-PORTFOLIO-RESILIENCE`
- `FAC-EXECUTION-FRICTION`
- `FAC-SCALE-READINESS`

### 4.3 决策级输出

最终要能够直接支持这些渠道决策：

- 是否进入渠道试点
- 是否扩大渠道预算
- 是否压缩或暂停某平台
- 是否切换主攻平台
- 是否从单渠道进入升级为渠道组合进入

---

## 五、Part 4 需要新增的治理与参考对象

除了当前标准输入表，`Part 4` 建议新增这些治理表：

### 5.1 `part4_source_registry`

用于记录：

- 流量来源
- 费率来源
- 订单来源
- 退货与拒付来源
- 时效性
- 置信度
- 成本与抓取方式

### 5.2 `part4_threshold_registry`

用于记录：

- 最低贡献毛利率
- 最大亏损概率
- 最大平台依赖度
- 最长回本期
- 最大 drawdown
- 最大执行摩擦上限

### 5.3 `part4_benchmark_registry`

用于记录：

- 渠道基准 CVR
- 基准 AOV
- 基准 CAC / ROAS
- 基准退款率
- 基准库存周转
- 基准回本期

### 5.4 `part4_optimizer_registry`

用于记录：

- 优化目标
- 决策变量
- 单渠道权重上限
- capital 约束
- risk 约束
- turnover penalty

### 5.5 `part4_stress_registry`

用于记录：

- CPC 上升
- 费率上升
- 退货率翻倍
- 物流费用上升
- 宏观需求下降
- 平台政策冲击

---

## 六、章节级优化方向

### `4.1 独立站模式可行性分析`

下一步要升级为：

- `brand_ownability_score`
- `content_dependency_score`
- `owned_data_capture_score`
- `dtc_payback_distribution`

建议新增输出：

- `channel_fit_factor`
- `owned_data_value_score`

### `4.2 平台电商模式可行性分析`

下一步要升级为：

- `platform_dependency_index`
- `platform_margin_stack`
- `platform_white_space_signal`
- `platform_penalty_risk`

建议新增输出：

- `platform_fit_factor`
- `platform_risk_factor`

### `4.3 线下经销商与 ToB 模式分析`

下一步要升级为：

- `rebate_pressure_score`
- `payment_terms_burden`
- `dealer_concentration_risk`
- `offline_execution_complexity`

建议新增输出：

- `b2b_fit_factor`
- `terms_pressure_score`

### `4.4 曝光、获客与流量结构分析`

下一步要升级为：

- `traffic_source_resilience`
- `paid_dependency_ratio`
- `first_touch_mix_stability`
- `traffic_efficiency_index`

建议新增输出：

- `traffic_efficiency_factor`
- `traffic_dependency_score`

### `4.5 转化效率与 ROI 模型分析`

这一节是 `Part 4` 最值得升级的核心。

建议增加：

- `sharpe_ratio`
- `sortino_ratio`
- `calmar_ratio`
- `ulcer_index`
- `var_95`
- `cvar_95`
- `omega_ratio`
- `turnover_penalty_score`
- `risk_adjusted_profit`

建议新增输出：

- `unit_economics_factor`
- `portfolio_resilience_factor`

### `4.6 运营门槛与组织能力要求分析`

下一步要升级为：

- `execution_friction_score`
- `ops_capacity_gap`
- `experiment_readiness_score`
- `inventory_reaction_time`

建议新增输出：

- `execution_friction_factor`
- `scale_readiness_factor`

### `4.7 推荐进入路径与 90 天销售执行方案`

下一步要升级为：

- `optimal_budget_mix`
- `recommended_channel_sequence`
- `pilot_scale_rollback_map`
- `channel_portfolio_feasible_set`

建议新增输出：

- `optimized_channel_portfolio`
- `risk_adjusted_recommendation`

---

## 七、Part 4 的指标、优化器与压力测试升级

### 7.1 时间序列绩效指标

建议正式纳入：

- `annualized_return`
- `annualized_volatility`
- `max_drawdown`
- `drawdown_duration`
- `sharpe_ratio`
- `sortino_ratio`
- `calmar_ratio`
- `ulcer_index`

### 7.2 分布与尾部风险指标

建议正式纳入：

- `profit_var_95`
- `profit_cvar_95`
- `tail_shortfall_probability`
- `omega_ratio`
- `worst_case_margin`

### 7.3 渠道组合优化器

建议新增：

- `mean_variance_optimizer`
- `cvar_optimizer`
- `channel_cap_constraints`
- `dependency_constraints`
- `turnover_penalty`

### 7.4 执行摩擦与滑点建模

建议新增：

- `cac_slippage_curve`
- `budget_turnover_penalty`
- `fee_jump_scenario`
- `policy_jump_scenario`

### 7.5 压力测试与情景分析

建议固定 stress suite：

- `cpc_up_30`
- `fee_up_20`
- `return_rate_x2`
- `logistics_up_15`
- `demand_down_20`
- `platform_policy_shock`

---

## 八、Part 4 需要新增的验证与回测体系

### 8.1 验证协议

建议固定输出：

- `walk_forward_summary`
- `train_test_split_summary`
- `optimizer_feasibility_report`
- `metric_regression_report`
- `gate_flip_report`
- `stress_suite_summary`

### 8.2 输出产物

建议统一输出：

- `part4_backtest_summary.json`
- `part4_optimizer_runs.json`
- `part4_portfolio_panel.csv`
- `part4_stress_suite.json`
- `part4_channel_performance_metrics.json`
- `part4_gate_records.csv`

---

## 九、Part 4 与 Decision OS 的连接目标

`Part 4` 后续必须向 `Decision OS` 输出：

- `channel factor snapshots`
- `channel gate records`
- `portfolio optimizer runs`
- `stress test records`
- `execution friction records`

这意味着 `Part 4` 不应只输出 “best platform”，而应输出：

- `portfolio decision set`
- `capital fit status`
- `risk budget fit status`
- `recommended budget weights`

---

## 十、建议的实施顺序

### Phase 1：治理层

- 新增 `part4_source_registry`
- 新增 `part4_threshold_registry`
- 新增 `part4_benchmark_registry`
- 新增 `part4_optimizer_registry`
- 新增 `part4_stress_registry`

### Phase 2：指标层

- 补 `Sharpe / Sortino / Calmar / Ulcer`
- 补 `VaR / CVaR / Omega`
- 补 `turnover_penalty / execution_friction`

### Phase 3：优化层

- 补 `mean_variance_optimizer`
- 补 `cvar_optimizer`
- 输出 `optimal_budget_mix`

### Phase 4：验证层

- 接 `walk-forward`
- 接 `train/test split`
- 接 `stress suite`
- 接 `gate flip report`

### Phase 5：Decision OS 层

- 输出标准化 `channel factor snapshots`
- 输出标准化 `portfolio records`
- 绑定 capital / risk constraints

---

## 十一、这轮优化的直接交付要求

这轮 `Part 4` 深度优化，不应停留在建议层，至少要落成：

1. `Part4-Quantitative-Optimization-Plan.md`
2. `Part4-Deep-Optimization-Crosswalk.md`
3. `decision-os/config/part4_quant_plan.yaml`
4. `decision-os/tests/test_part4_quant_plan.py`
5. `docs/part-chains/Part4-Chain.md` 更新

---

## 十二、与现有文件的对齐关系

这轮优化与以下文件直接对齐：

- [Part4-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-Quantitative-Structure.md)
- [Part4-North-America-Go-To-Market-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part4-North-America-Go-To-Market-Strategy.md)
- [quant_framework/part4.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4.py)
- [quant_framework/part4_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4_metrics.py)
- [quant_framework/part4_simulation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4_simulation.py)
- [decision-os/config/part4_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part4_quant_plan.yaml)
