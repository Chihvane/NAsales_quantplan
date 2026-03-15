# Part 3 量化优化计划

更新时间：2026-03-15

## 一、这份计划要解决什么问题

`Part 3` 当前已经具备：

- 供应结构分析
- RFQ 与报价结构分析
- 合规门槛分析
- 物流履约分析
- landed cost 方案比较
- Monte Carlo 利润带与敏感度分析
- 风险矩阵与进入建议

但它还主要停留在“供应链可行性评估模块”，还没有完全升级成：

> 可做 tail-risk 评估、可做约束优化、可做 stress test、可直接接 Gate 的 `Supply Chain Engine`

因此这份计划要解决的不是“再多算几个分数”，而是五个结构性问题：

1. `Part 3` 已有 Monte Carlo，但尾部风险表达仍然不够硬，缺少 `VaR / Expected Shortfall / tail shortfall severity` 这类下行风险指标。
2. `Part 3` 目前主要是“best scenario + rule-based recommendation”，缺少真正的约束优化器，不能回答“在 margin / lead time / risk / compliance 约束下，最优供应路径是什么”。
3. `Part 3` 的模拟目前默认把多数驱动看成独立扰动，缺少更贴近现实的 `correlated stress / scenario coupling`。
4. `Part 3` 的验证还偏 smoke test，缺少更深的回归基准、stress suite、golden scenario 与 metric drift 控制。
5. `Part 3` 与 `Decision OS` 的衔接仍然偏“报告摘要输入”，还没有形成标准化的 `supply gate records / optimizer records / tail-risk records`。

---

## 二、项目回溯后的 Part 3 现状

### 2.1 已经完成的能力

当前 `Part 3` 已经具备这些基础能力：

- 标准输入六表：
  - `suppliers`
  - `rfq_quotes`
  - `compliance_requirements`
  - `logistics_quotes`
  - `tariff_tax`
  - `shipment_events`
- 原始清洗链：
  - suppliers
  - rfq
  - compliance
  - logistics
  - tariff
  - shipment
- 七个标准章节：
  - `3.1 中国供应端结构分析`
  - `3.2 国内采购与报价策略分析`
  - `3.3 合规、认证与准入门槛分析`
  - `3.4 出口路径与物流履约分析`
  - `3.5 到岸成本与利润安全边际分析`
  - `3.6 风险矩阵与应对策略`
  - `3.7 推荐进入路径与首批执行方案`
- 可靠性增强：
  - sample adequacy
  - quote quality
  - stage lead-time distributions
  - landed cost assumption flags
  - Monte Carlo percentile bands
  - driver sensitivity
- 输出结构：
  - `overview / sections / uncertainty / validation / decision_summary`

### 2.2 当前主要缺口

结合这次深研稿与现有代码，`Part 3` 还存在这些明显缺口：

1. **Tail risk 不够正式**
   - 目前有 `loss_probability` 和分位数，但没有 `VaR / ES / worst-tail average margin`。
2. **优化器缺失**
   - 还不能把 supplier / incoterm / route 组合变成“在约束下求最优”的优化问题。
3. **相关性建模不足**
   - 物流、关税、价格、return reserve 等波动默认近似独立，现实里经常联动。
4. **stress suite 不够完整**
   - 还缺 freight shock、tariff shock、sell price shock、lead-time shock、quote transparency shock 这种正式压力场景。
5. **验证协议不足**
   - 当前测试主要验证字段存在和基本数值非空，缺少 golden scenario 与风险指标回归。
6. **因子层尚未成型**
   - `Part 3` 现在有很多 section metrics，但还没有整理成统一的 Supply 因子。
7. **Decision OS 对接不够深**
   - 还缺 `supply gate record / optimizer decision record / risk budget fit record`。

---

## 三、Part 3 在整个项目中的新定位

优化后的 `Part 3` 不再只是“供应链可行性章节”，而是 `Decision OS` 的：

> `Supply Chain Engine`

它必须向后续系统输出三类结果：

1. **供应选择结果**
   - 哪个 supplier 值得谈
   - 哪个 incoterm 最适合
   - 哪条物流路径更稳

2. **风险结果**
   - 下行 tail risk 到底有多大
   - 哪些不透明项会吞掉 margin safety
   - 哪些合规与物流节点会成为硬 blocker

3. **因子结果**
   - 标准化 Supply 因子
   - 可进入 `Gate Engine`
   - 可与 Part 4/5 的 capital 与 channel 决策联动

---

## 四、优化后的 Part 3 输出目标

### 4.1 章节级输出

每个章节除了章节指标本身，还应统一补齐：

- `source_health`
- `threshold_coverage_ratio`
- `gate_results`
- `confidence_band`
- `scenario_confidence`

### 4.2 因子级输出

建议把 `Part 3` 固定输出为 6 个标准因子：

- `FAC-SUPPLY-ROBUSTNESS`
- `FAC-QUOTE-QUALITY`
- `FAC-COMPLIANCE-READINESS`
- `FAC-LOGISTICS-RELIABILITY`
- `FAC-MARGIN-SAFETY`
- `FAC-EXECUTION-RISK`

### 4.3 决策级输出

最终要能够直接支持这些供应链决策：

- 是否进入 supplier shortlist
- 是否进入 RFQ 深化
- 是否进入首单试采
- 是否应当切换物流路径
- 是否需要双供策略

---

## 五、Part 3 需要新增的治理与参考对象

除了当前六张标准输入表，`Part 3` 建议新增这些治理表：

### 5.1 `part3_source_registry`

用于记录：

- 报价来源
- 物流来源
- 合规来源
- 关税来源
- 时效性
- 置信度
- 成本与抓取方式

### 5.2 `part3_threshold_registry`

用于记录：

- 最低净利率阈值
- 最大 loss probability
- 最大 lead-time 风险
- quote quality 下限
- supplier concentration 上限
- compliance blocker 上限

### 5.3 `part3_scenario_registry`

用于记录：

- 正常情景
- 运费上升
- 关税上升
- 卖价下滑
- return reserve 上升
- lead-time 延长

### 5.4 `part3_optimizer_registry`

用于记录：

- 优化目标
- 决策变量
- 约束条件
- capital 约束
- risk 约束

---

## 六、章节级优化方向

### `3.1 中国供应端结构分析`

当前重点是 sample adequacy 和 maturity，下一步要升级为：

- `supplier_diversity_index`
- `effective_supplier_count`
- `supply_fragility_score`
- `single_point_dependency_flag`

建议新增输出：

- `FAC-SUPPLY-ROBUSTNESS`

### `3.2 国内采购与报价策略分析`

下一步要从 quote leaderboard 升级为：

- `quote_frontier`
- `quote_scope_completeness`
- `quote_transparency_score`
- `quote_outlier_flags`

建议新增输出：

- `FAC-QUOTE-QUALITY`

### `3.3 合规、认证与准入门槛分析`

下一步要升级为：

- `time_to_market_risk`
- `compliance_buffer_days`
- `compliance_cost_stress`
- `blocker_probability`

建议新增输出：

- `FAC-COMPLIANCE-READINESS`

### `3.4 出口路径与物流履约分析`

下一步要从 route score 升级为：

- `otif_proxy`
- `delay_severity_distribution`
- `route_bottleneck_ranking`
- `stage_hazard_score`

建议新增输出：

- `FAC-LOGISTICS-RELIABILITY`

### `3.5 到岸成本与利润安全边际分析`

这一节是 `Part 3` 最值得升级的核心。

建议增加：

- `margin_var_95`
- `margin_es_95`
- `tail_shortfall_probability`
- `cost_transparency_score`
- `scenario_pareto_frontier`

建议新增输出：

- `FAC-MARGIN-SAFETY`

### `3.6 风险矩阵与应对策略`

这一节要从平均风险分数升级为：

- `weighted_risk_budget_fit`
- `tail_risk_gate`
- `dual_sourcing_trigger`
- `execution_risk_factor`

建议新增输出：

- `FAC-EXECUTION-RISK`

### `3.7 推荐进入路径与首批执行方案`

下一步要从 rule-based recommendation 升级为：

- `constraint_optimized_path`
- `feasible_set_count`
- `capital_fit_status`
- `risk_budget_fit_status`

---

## 七、Part 3 的模型与工具模块升级

### 7.1 建议新增的模型模块

- `part3_risk_metrics`
  - 负责 `VaR / ES / tail diagnostics`
- `part3_optimizer`
  - 基于 `cvxpy` 的供应路径约束优化
- `part3_validation`
  - 负责 golden scenario、regression checks、stress suite
- `part3_stress_suite`
  - 负责标准化压力测试

### 7.2 建议新增的工具模块

- `part3_evidence_index`
- `part3_scenario_library`
- `part3_cost_lineage`
- `part3_optimizer_runs`
- `part3_tail_risk_report`

---

## 八、Part 3 与 Decision OS 的对接目标

`Part 3` 在优化后应当直接输出到 `Decision OS` 的这几个接口：

### 8.1 因子面板

- `part3_factor_snapshots`
- `part3_factor_panel.csv`

### 8.2 决策记录

- `supply_gate_records`
- `optimizer_decision_records`
- `tail_risk_records`

### 8.3 约束记录

- `capital_fit_records`
- `risk_budget_fit_records`
- `compliance_blocker_records`

---

## 九、Part 3 的验证、校准与 stress test

`Part 3` 继续优化后，必须把“模拟漂亮”升级成“压力下仍可信”。

建议固定接入这些验证对象：

### 9.1 回归验证

- golden scenario comparison
- core margin band regression
- sensitivity ranking regression

### 9.2 风险验证

- `VaR / ES` consistency check
- tail severity monotonicity
- optimizer feasibility check

### 9.3 压力测试

建议至少包括：

- freight_up_40
- tariff_up_20
- sell_price_down_10
- lead_time_up_30
- ddp_transparency_break

### 9.4 漂移与稳定性

- quote freshness drift
- logistics volatility drift
- risk gate flip report

---

## 十、2-6 周 MVP 路线

### 第 1-2 周

- 完成 `Part 3` 指标词典 v0
- 完成 `source / threshold / scenario / optimizer` 四张治理表
- 固化 `tail-risk` 输出定义

### 第 3-4 周

- 接入 `VaR / ES`
- 接入第一版 `part3_optimizer`
- 补齐 6 个 Supply 因子目标结构

### 第 5-6 周

- 接入 `stress suite`
- 输出 `optimizer_decision_records`
- 输出 `tail_risk_report`

---

## 十一、近期最值得先做的事

按当前代码状态，`Part 3` 最值得优先推进的是：

1. 把 `part3_source_registry / part3_threshold_registry / part3_scenario_registry / part3_optimizer_registry` 接入数据层
2. 新增 `part3_risk_metrics`，先补 `VaR / ES`
3. 新增 `part3_optimizer`，把 best scenario 改成可约束优化
4. 新增 `stress suite`
5. 把 `Part 3` 输出正式接到 `Decision OS` 的 `capital / risk budget` 决策记录

一句话总结：

> `Part 3` 下一轮优化的方向，不是“更会算 landed cost”，而是把供应链可行性模块升级成真正可约束、可压力测试、可进入 Gate 的 `Supply Chain Engine`。
