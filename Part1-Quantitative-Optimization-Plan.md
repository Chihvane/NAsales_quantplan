# Part 1 量化优化计划

更新时间：2026-03-14

## 一、这份计划要解决什么问题

经过整个项目回溯，当前工作区已经形成两条并行主线：

- `quant_framework/`
  - 已经具备 `Part 0–5` 的量化报告、验证、图表、demo 数据和回测。
- `decision-os/`
  - 已经具备生产级数据库、权限、审计、回测、部署与多租户骨架。

`Part 1` 当前的问题不是“不能运行”，而是：

1. 指标体系已经能出结论，但结论的证据等级、不确定性和适用边界还不够统一。
2. `Part 1` 仍偏“研究报告入口”，还没有完全升级成 `Decision OS` 的标准因子生产层。
3. 当前 `Part 1` 回测和 `Decision OS` 回测是两条链，尚未形成统一的市场进入校准闭环。

因此这份计划的目标不是再堆几个指标，而是把 `Part 1` 从“可运行的市场量化报告模块”，升级为：

> 可治理、可证据追溯、可回测、可接 Gate、可接数据库的市场量化引擎。

---

## 二、项目回溯后的 Part 1 现状

### 2.1 已经完成的能力

当前 `Part 1` 已经具备这些能力：

- 标准输入表
  - `search_trends / region_demand / customer_segments / listings / transactions / channels`
  - `market_size_inputs / channel_benchmarks`
- 章节化输出
  - `1.1` 市场现状与需求概览
  - `1.2` 客户画像分析
  - `1.3` 市场规模分析
  - `1.4` 购买渠道分析
  - `1.5` 货架商品价格分析
  - `1.6` 实际成交价格分析
- 方法验证
  - Google Trends 相对指数
  - HHI
  - IQR / Tukey fences
  - midpoint elasticity
  - Top-down / Bottom-up triangulation
- 输出结构
  - `overview / sections / uncertainty / validation / decision_summary`
- Demo 与回测
  - `examples/output/part1_report.json`
  - `examples/output/backtest_demo`

### 2.2 当前主要缺口

结合现有代码、文档和最新优化稿，Part 1 现在最明显的缺口是：

1. **测量治理不够硬**
   - 还没有把每个市场指标绑定到统一 `field -> metric -> factor -> gate` 链条。
2. **证据等级不够细**
   - 目前有 `validation` 和部分 `confidence`，但还没有章节级“证据等级 + 数据时效性 + 失效规则”。
3. **事件驱动维度不足**
   - 需求季节性已经有，但还没有完整的 `事件库` 与 `event attribution`。
4. **市场规模误差处理仍可加强**
   - 当前有 triangulation，但还缺“来源加权、误差传播、区间优先”的正式口径。
5. **渠道分析偏静态**
   - 缺“渠道集中度、渠道依赖度、跨渠道路径”和对 Decision OS 的 `channel risk` 因子接入。
6. **回测没有回流到 Part 1 参数**
   - 目前能回测，但 Part 1 的阈值、权重、Gate 触发条件还没有系统校准闭环。

---

## 三、Part 1 在整个项目中的新定位

优化后的 `Part 1` 不再只是“市场研究部分”，而是 `Decision OS` 的：

> `Market Quant Engine`

它必须输出三类结果：

1. **市场观测结果**
   - 描述市场发生了什么。
2. **市场因子结果**
   - 把观测结果转成可决策的标准化因子。
3. **市场进入约束结果**
   - 把因子结果转成 Gate 可消费的输入。

因此，`Part 1` 的后续开发统一按下面链条推进：

```text
标准字段 -> 标准指标 -> 市场因子 -> 市场进入 Gate 输入 -> 回测校准
```

---

## 四、优化后的 Part 1 目标结构

## 4.1 治理层

Part 1 需要显式纳入 `Part 0 + Horizontal System + Decision OS` 的治理约束：

- 每个核心结论都要有 `evidence_ref`
- 每个章节都要有 `master_data_ref`
- 每个关键指标都要有 `rule_ref`
- 每个章节都要输出：
  - `data_quality`
  - `confidence`
  - `staleness`
  - `gate_result`

### 关键新增治理对象

- `event_library`
  - 需求、价格、渠道变化的外部事件表
- `source_registry`
  - 每个来源的 `source_type / confidence_grade / refresh_window`
- `part1_threshold_registry`
  - 市场进入门槛、市场结构门槛、需求稳定性门槛

## 4.2 数据层

Part 1 标准表继续保留，但升级成三类：

### A. 基础观测表

- `search_trends`
- `region_demand`
- `customer_segments`
- `listings`
- `transactions`
- `channels`

### B. 参考与校准表

- `market_size_inputs`
- `channel_benchmarks`
- `event_library`
- `source_registry`

### C. 回测与校准表

- `part1_factor_snapshots`
- `part1_gate_records`
- `part1_backtest_panel`
- `part1_stress_scenarios`

---

## 五、章节级量化优化方案

## 5.1 `1.1 市场现状与需求概览`

### 当前已做

- 趋势
- CAGR
- 波动率
- 季节性指数
- 区域份额
- 热度与销量滞后

### 下一步优化

1. 增加 `event_library`
   - Prime Day
   - Black Friday
   - 停电/飓风/暴雪季
   - 平台政策变化
   - 竞品新品发布
2. 增加 `anchored trend normalization`
   - 解决 Google Trends 重采样导致历史指数漂移的问题
3. 增加 `lead-lag confidence`
   - 对滞后关系输出样本覆盖和稳定性，而不是只给相关系数
4. 增加 `demand regime`
   - 稳定型 / 周期型 / 事件驱动型 / 噪声型

### 目标输出

- `demand_strength_score`
- `demand_stability_score`
- `event_sensitivity_score`

## 5.2 `1.2 客户画像分析`

### 当前已做

- 年龄/性别/收入/场景/决策因素分布

### 下一步优化

1. 增加来源分层
   - 评论
   - 社媒
   - 问卷
   - 平台画像工具
2. 增加 `source-weighted persona`
   - 不同来源按证据等级加权
3. 增加 `sampling adequacy`
   - 样本量是否达到误差界要求
4. 增加 `persona concentration`
   - 用户是否高度集中在某一画像

### 目标输出

- `customer_fit_score`
- `persona_confidence_score`
- `persona_concentration_score`

## 5.3 `1.3 市场规模分析`

### 当前已做

- Top-down
- Bottom-up
- Triangulation gap
- HHI
- 参考面板一致性

### 下一步优化

1. 增加 `source-weighted triangulation`
   - 不同来源按 `confidence_grade` 加权
2. 增加 `uncertainty-first sizing`
   - 先输出区间，再输出点估计
3. 增加 `coverage-adjusted bottom-up`
   - 对样本覆盖率、长尾缺失率做显式调整
4. 增加 `market entry fit`
   - 把规模、增长、集中度、波动统一成市场进入因子

### 目标输出

- `market_attractiveness_factor`
- `market_structure_factor`
- `sizing_confidence_band`

## 5.4 `1.4 购买渠道分析`

### 当前已做

- 渠道收入占比
- 转化率
- AOV
- ROAS
- benchmark gap

### 下一步优化

1. 增加 `channel concentration`
   - 渠道依赖度和集中度
2. 增加 `channel path`
   - 发现、比较、成交三段式
3. 增加 `benchmark quality`
   - 行业基准是否来自同类目、同价格带、同成熟度
4. 增加 `channel risk`
   - 单渠道依赖、平台政策、退货和价格战风险

### 目标输出

- `channel_efficiency_factor`
- `channel_risk_factor`
- `channel_dependency_score`

## 5.5 `1.5 货架商品价格分析`

### 当前已做

- 分位数价格带
- IQR 异常值
- 品牌溢价
- 销量加权价格结构

### 下一步优化

1. 增加 `spec-adjusted premium`
   - 溢价需扣除规格差异
2. 增加 `promo contamination flag`
   - 区分常规标价和异常促销干扰
3. 增加 `price architecture`
   - 入门 / 主力 / 旗舰三层结构
4. 增加 `white-space price band`
   - 供给不足但需求有承接的价格带

### 目标输出

- `price_band_fit_factor`
- `brand_premium_clean`
- `price_white_space_signal`

## 5.6 `1.6 实际成交价格分析`

### 当前已做

- 平均成交价
- 折扣率
- 价格实现率
- 成交价格带
- midpoint elasticity

### 下一步优化

1. 增加 `elasticity confidence`
   - 对样本量、波动窗口、促销干扰做标记
2. 增加 `short-term vs long-term elasticity`
3. 增加 `discount dependency`
   - 成交是否过度依赖打折
4. 增加 `realized margin proxy`
   - 成交价与理论利润空间的联动

### 目标输出

- `price_realization_factor`
- `elasticity_reliability_score`
- `discount_dependency_score`

---

## 六、Part 1 新增因子层设计

为了和 `Decision OS` 对齐，Part 1 需要从“章节输出”提升到“因子输出”。第一阶段先固定六个因子：

- `FAC-MARKET-ATTRACT`
  - 规模、增长、集中度、价格空间
- `FAC-DEMAND-STABILITY`
  - 波动率、季节性、事件敏感度、热度滞后稳定性
- `FAC-CUSTOMER-FIT`
  - 用户集中度、画像清晰度、证据等级
- `FAC-CHANNEL-EFFICIENCY`
  - 转化、AOV、ROAS、基准偏差
- `FAC-CHANNEL-RISK`
  - 渠道集中度、政策风险、路径依赖
- `FAC-PRICE-REALIZATION`
  - 折扣依赖、成交价实现率、弹性可靠性

这些因子后续要进入：

- `Gate 1：市场进入`
- `Gate 3：渠道试点`
- `Gate 4：放大量产`

---

## 七、验证与回测优化计划

当前 `Part 1` 已有 demo backtest，但它和 `decision-os/backtest/` 还没有完全打通。下一步必须做成统一回测体系。

### 7.1 回测原则

- 采用 `walk-forward`
- 严禁未来数据泄漏
- 训练期和测试期分离
- 回测输出直接进入 Gate 校准

### 7.2 Part 1 回测要验证的 4 件事

1. 市场进入门是否真的筛掉差市场
2. 需求稳定因子是否能降低回撤
3. 渠道效率因子是否能提升后续渠道选择命中率
4. 价格实现因子是否能减少“高热度低利润”误判

### 7.3 压力测试场景

- 广告 CPC 上涨 50%
- 运费上涨 40%
- 退货率翻倍
- 搜索热度断崖下跌
- 单渠道被封禁/政策收紧

### 7.4 回测产物

- `part1_backtest_summary.json`
- `part1_factor_panel.csv`
- `part1_gate_records.csv`
- `part1_alpha_table.csv`
- `part1_stress_test_summary.json`

---

## 八、实施顺序

### Phase 1：治理与测量收口

1. 固化 `event_library`
2. 固化 `source_registry`
3. 固化 `part1_threshold_registry`
4. 给 `Part 1` 每节补 `staleness` 与 `confidence downgrade`

### Phase 2：因子化

1. 从章节指标计算 `Part 1` 六个因子
2. 输出标准化因子快照
3. 接入 `Decision OS` registry

### Phase 3：回测化

1. 把 `quant_framework` 的 `Part 1` backtest 接入 `decision-os/backtest`
2. 加入 train/test split
3. 加入 stress test

### Phase 4：Gate 化

1. 把 Part 1 因子接入 `market entry gate`
2. 输出标准 `decision_record`
3. 与 `capital/risk` 约束联动

---

## 九、这轮优化的直接交付要求

这份计划之后，Part 1 的后续迭代必须优先满足：

1. 新增指标必须说明：
   - 来源
   - 口径
   - 置信等级
   - 对应 Gate
2. 新增代码必须说明：
   - 写入哪个标准输出
   - 如何回测
   - 如何验证
3. 新增图表必须说明：
   - 用于哪个决策问题
   - 是否有误导风险

---

## 十、与现有文件的对齐关系

- 现有量化结构基线：
  - [Part1-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Quantitative-Structure.md)
- 现有方法对照：
  - [Part1-Methodology-Reliability-Validation.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Methodology-Reliability-Validation.md)
- 现有代码入口：
  - [quant_framework/part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
  - [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py)
- Decision OS 回测与生产骨架：
  - [decision-os/docs/Backtesting-Program.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/docs/Backtesting-Program.md)
  - [decision-os/database/schema.sql](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/database/schema.sql)

这份文档的作用不是替代原有结构稿，而是作为：

> Part 1 从“现有可运行版本”升级到“Decision OS 兼容版本”的执行计划。
