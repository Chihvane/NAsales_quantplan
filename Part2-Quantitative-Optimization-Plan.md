# Part 2 量化优化计划

更新时间：2026-03-15

## 一、这份计划要解决什么问题

`Part 2` 当前已经能完成：

- 竞品结构分析
- 成交价格带分析
- 属性白空间识别
- 评论主题抽取
- 货架生存分析
- 回测 demo 与 `Decision OS` 桥接

但它仍然主要停留在“可运行的竞争分析模块”，还没有完全升级成：

> 可证据分层、可概率化输出、可回测校准、可直接接 Gate 的 `Product Intelligence Engine`

因此这份计划要解决的不是“再加几个指标”，而是五个系统性问题：

1. `Part 2` 的证据等级还不够统一，平台抓取、第三方估算、一手成交与评论文本没有进入同一套置信度口径。
2. `Part 2` 的很多结论仍然偏“强结论”，缺少概率表达、区间表达和偏差降级规则。
3. `Part 2` 的 VOC、评论、退款、售后、问答等反馈还没有真正形成产品迭代闭环。
4. `Part 2` 的因子层已经有雏形，但还没有形成更完整的 `field -> metric -> factor -> gate` 产品 intelligence 链条。
5. `Part 2` 的回测还偏“竞争结构 demo”，没有与 `Decision OS` 的 walk-forward、stress test 和参数优化完全打通。

---

## 二、项目回溯后的 Part 2 现状

### 2.1 已经完成的能力

当前 `Part 2` 已经具备这些基础能力：

- 标准输入四表：
  - `listing_snapshots`
  - `sold_transactions`
  - `product_catalog`
  - `reviews`
- 原始清洗链：
  - Amazon
  - eBay
  - TikTok
- 六个标准章节：
  - `2.1 在售商品与成交结构`
  - `2.2 成交价格带与折扣深度`
  - `2.3 价格-评分价值矩阵`
  - `2.4 属性画像与白空间机会`
  - `2.5 评论情绪与痛点主题`
  - `2.6 货架动态与生存分析`
- 输出结构：
  - `overview / sections / uncertainty / validation / decision_summary`
- 当前因子快照：
  - `FAC-COMPETITION-HEADROOM`
  - `FAC-PRICING-FIT`
  - `FAC-WHITESPACE-DEPTH`
  - `FAC-SHELF-STABILITY`
- 回测与桥接：
  - `Part 2` 专用回测
  - GitHub 开源样本 demo
  - `Part 1 + Part 2 -> Decision OS bridge`

### 2.2 当前主要缺口

结合你给的 `deep-research-report (14).md` 和现有代码，`Part 2` 还存在这些明显缺口：

1. **证据分层不足**
   - 官方/一手/平台/第三方/代理信号没有统一的 A/B/C/D 证据等级。
2. **概率化输出不足**
   - 当前仍然以“因子分数 + 章节结论”为主，缺少“通过概率、可信区间、证据带宽”。
3. **VOC 闭环不足**
   - 评论、差评、问答、售后、退货原因还没有归一到“产品缺陷树 / 体验缺陷树 / 预期错配树”。
4. **竞争结构风险不足**
   - HHI、CR4、Top SKU 集中度已经有，但还没有系统接入“可靠度、集中度门禁、结构性拒绝条件”。
5. **白空间信号仍偏静态**
   - 当前属性 outperformance 已有，但还缺“最小样本支持 + 收缩 + 新颖度 + 覆盖缺口”。
6. **价格分析还不够经营化**
   - 需要从“成交甜蜜带”升级到“真实价格实现率 / 折扣依赖度 / 价值陷阱概率 / 毛利代理”。
7. **回测未完全接入产品决策**
   - 当前回测能验证竞争筛选，但还没有形成 SKU 上线、SKU 淘汰、属性开发的参数校准闭环。

---

## 三、Part 2 在整个项目中的新定位

优化后的 `Part 2` 不再只是“竞品分析章节”，而是 `Decision OS` 的：

> `Product Intelligence Engine`

它必须向后续系统输出三类结果：

1. **产品选择结果**
   - 什么商品结构值得切入
   - 什么属性组合值得打样
   - 什么价格带最容易形成可成交商品

2. **风险结果**
   - 哪些属性/主题会显著拖累成交
   - 哪些价格带属于价值陷阱
   - 哪些货架结构意味着进入难度过高

3. **因子结果**
   - 标准化 Product 因子
   - 可进入 `Gate Engine`
   - 可回测、可 stress test、可与 Part 3/4 联动

---

## 四、优化后的 Part 2 输出目标

### 4.1 章节级输出

每个章节除了指标本身，还要补齐四类治理字段：

- `source_health`
- `threshold_coverage_ratio`
- `gate_results`
- `confidence_band`

### 4.2 因子级输出

建议把 `Part 2` 固定输出升级为 6 个标准因子：

- `FAC-COMPETITION-HEADROOM`
- `FAC-PRICING-FIT`
- `FAC-VALUE-ADVANTAGE`
- `FAC-WHITESPACE-DEPTH`
- `FAC-VOC-RISK`
- `FAC-SHELF-STABILITY`

### 4.3 决策级输出

最终要能够直接支持这些产品决策：

- 是否进入这个商品结构
- 是否进入这个属性组合
- 是否进入这个价格带
- 是否应当跳过当前竞争区间
- 是否值得把这个结构送入 Part 3 打样与 RFQ

---

## 五、Part 2 需要新增的治理与参考对象

除了当前四张标准输入表，`Part 2` 建议新增这些治理表：

### 5.1 `part2_source_registry`

用于记录：

- 数据来源
- 来源类型
- 抓取方式
- 采集时间
- 时效性
- 置信度等级
- 成本与配额约束

### 5.2 `part2_threshold_registry`

用于记录：

- HHI 阈值
- Top SKU share 阈值
- 负评率阈值
- 生存期阈值
- 折扣依赖阈值
- 属性样本支持阈值

### 5.3 `part2_benchmark_registry`

用于记录：

- 类目基准
- 平台基准
- 价格带基准
- 评分/评论/退货基准

### 5.4 `voc_event_registry`

用于记录：

- 差评事件
- 售后事件
- 退款原因
- 预期错配事件
- 平台规则变化

---

## 六、证据分层与不确定性框架

`Part 2` 继续优化后，所有指标都不应再直接输出“裸分数”，而要同时输出：

- 点估计
- 区间估计
- 证据等级
- 偏差说明

建议统一采用 `A / B / C / D` 证据等级：

- `A`：官方或一方真值
- `B`：可审计的付费第三方平台数据
- `C`：趋势、代理、抽样、归一化指数
- `D`：经验假设或弱证据推断

在 `Part 2` 中，这一分层尤其重要，因为：

- 销量、份额、SOV、关键词量经常是估算值
- 评论、问答、社媒文本存在采样偏差
- 平台结构与抓取覆盖经常变化

因此建议把每一节统一补为：

- `source_health`
- `coverage_ratio`
- `staleness`
- `confidence_band`
- `proxy_usage_flags`

---

## 七、章节级优化方向

### `2.1 在售商品与成交结构`

当前重点是结构和份额，下一步要升级为：

- `structure_confidence_score`
- `concentration_reliability_score`
- `active_competitor_quality_score`
- `competition_density_gate`

建议新增输出：

- `competition_headroom_factor`
- `seller_fragmentation_score`
- `entry_barrier_score`

### `2.2 成交价格带与折扣深度`

下一步要从价格带分析升级为：

- `realized_price_quality`
- `discount_dependency_score`
- `margin_proxy_band`
- `promo_contamination_flag`

建议新增输出：

- `pricing_fit_factor`
- `price_realization_score`
- `value_trap_probability`

### `2.3 价格-评分价值矩阵`

下一步要升级为“价值结构判断”而不是静态矩阵：

- `value_advantage_score`
- `rating_confidence_score`
- `premium_justification_score`
- `low_rating_discount_trap`

建议新增输出：

- `FAC-VALUE-ADVANTAGE`

### `2.4 属性画像与白空间机会`

这一节是 `Part 2` 最值得升级的核心。

建议增加：

- 样本支持约束
- 收缩后的属性超额表现
- 属性新颖度
- 品牌覆盖缺口
- 属性组合白空间

建议新增输出：

- `whitespace_confidence_score`
- `attribute_gap_depth`
- `attribute_combo_opportunity`

### `2.5 评论情绪与痛点主题`

这一节要从“情绪统计”升级为 `VOC Engine`：

建议新增三棵树：

- `product_defect_tree`
- `experience_defect_tree`
- `expectation_mismatch_tree`

建议新增输入源：

- 问答区高频问题
- 售后工单
- 退款原因
- 社媒吐槽

建议新增输出：

- `FAC-VOC-RISK`
- `design_fix_priority`
- `copy_fix_priority`
- `returns_prevention_priority`

### `2.6 货架动态与生存分析`

这一节要从“生存期描述”升级为“上架风险判断”：

建议新增：

- `hazard_rate_by_price_band`
- `hazard_rate_by_attribute`
- `entry_exit_velocity`
- `listing_decay_score`

建议新增输出：

- `FAC-SHELF-STABILITY`
- `shelf_risk_gate`

---

## 八、Part 2 的模型与工具模块升级

`Part 2` 继续优化不应只加指标，还应明确工具层和模型层。

### 8.1 建议新增的模型模块

- `Bayesian evidence scoring`
  - 用于把一方数据、第三方数据、趋势代理和经验先验合并成可解释的后验分布
- `Monte Carlo uncertainty propagation`
  - 用于把价格、销量、份额、VOC 风险等不确定性传播到最终输出
- `AHP weighting workflow`
  - 用于把业务权重治理化，而不是散落在代码里
- `SHAP / contribution decomposition`
  - 用于解释最终通过概率或因子分数的来源

### 8.2 建议新增的工具模块

- `part2_evidence_index`
- `part2_data_quality_log`
- `part2_source_cost_registry`
- `part2_label_registry`
- `part2_calibration_report`
- `part2_drift_monitor`

这些模块的目标不是增加复杂度，而是让 `Part 2` 从“竞品分析”升级成“能被审计的产品 intelligence 系统”。

---

## 九、Part 2 与 Decision OS 的对接目标

`Part 2` 在优化后应当直接输出到 `Decision OS` 的这几个接口：

### 7.1 因子面板

输出：

- `part2_factor_snapshots`
- `part2_factor_panel.csv`

### 7.2 决策记录

输出：

- `sku_selection_gate_records`
- `sku_reject_records`
- `voc_risk_records`

### 7.3 回测记录

输出：

- `part2_backtest_summary`
- `part2_alpha_table`
- `part2_stress_summary`

---

## 十、Part 2 的验证、校准与漂移监控

`Part 2` 继续优化后，必须从“能算”升级到“可信”。

建议固定接入这些验证对象：

### 10.1 回测

- `walk-forward backtest`
- `train / test split`
- `parameter stability review`

### 10.2 校准

- `calibration curve`
- `ECE / MCE`
- `probability bucket diagnostics`

### 10.3 贝叶斯检验

- `posterior predictive checks`
- `prior sensitivity review`

### 10.4 漂移监控

- `source drift`
- `metric drift`
- `factor drift`
- `proxy dependency drift`

建议每轮 `Part 2` 版本升级都输出：

- `calibration_report`
- `drift_report`
- `gate_flip_report`

---

## 十一、Part 2 回测与优化方向

下一步回测不应只验证“竞争分数高不高”，而要验证四件事：

1. `Part 2` 选中的商品结构，真实后续表现是否更好。
2. `Part 2` 拒绝的商品结构，是否确实更容易亏损或退出。
3. `VOC 风险` 是否能提前预判退货和差评。
4. `白空间机会` 是否真的能在后续成交中兑现。

建议固定采用：

- `walk-forward split`
- `train / test split`
- `stress scenarios`

建议 stress 情景至少包括：

- 退货率翻倍
- 评论恶化
- 平台费率上升
- 价格战加剧
- 广告竞争加剧

---

## 十二、实施顺序

建议按四阶段推进：

### 阶段 1：治理化

- 新增 `part2_source_registry`
- 新增 `part2_threshold_registry`
- 新增 `part2_benchmark_registry`
- 新增 `voc_event_registry`

### 阶段 2：因子化

- 补齐 6 个标准因子
- 输出章节级 `confidence_band`
- 输出章节级 `gate_results`
- 补齐 `source_health / proxy_usage_flags / evidence_grade`

### 阶段 3：经营化

- VOC 三棵树
- 价格实现率与价值陷阱
- 属性组合白空间
- contribution decomposition
- calibration baseline

### 阶段 4：回测化

- train/test split
- stress suite
- `Decision OS` gate 对接
- drift monitor
- probability calibration

---

## 十三、2-6 周 MVP 路线

### 第 1-2 周

- 完成 `Part 2` 指标词典 v0
- 完成 `A/B/C/D` 证据等级口径
- 完成 `source / threshold / benchmark / VOC event` 四张治理表

### 第 3-4 周

- 让 `Part 2` 吃进治理表
- 补齐 `FAC-VALUE-ADVANTAGE`
- 补齐 `FAC-VOC-RISK`
- 输出第一版 `confidence_band`

### 第 5-6 周

- 加入 `walk-forward + stress suite`
- 输出 `calibration_report`
- 输出 `Part 2 -> Decision OS` 的 gate records

---

## 十四、近期最值得先做的事

按当前代码状态，`Part 2` 最值得优先推进的是：

1. 把 `source_registry / threshold_registry / benchmark_registry` 接入 `Part 2Dataset`
2. 把 `FAC-VALUE-ADVANTAGE` 与 `FAC-VOC-RISK` 正式补齐
3. 把 VOC 从评论情绪升级到“问题树 + 修复建议”
4. 把 `Part 2` 回测接入 `Decision OS` 的 walk-forward + stress test
5. 增加 `calibration + drift + proxy dependency` 三张验证报告

一句话总结：

> `Part 2` 下一轮优化的方向，不是“更会看竞品”，而是把竞品与成交分析升级成真正可驱动 SKU 决策的产品 intelligence 系统。
