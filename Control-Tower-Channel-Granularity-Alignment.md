# 控制塔、通道与颗粒度对齐说明

## 来源

- 细化稿：[deep-research-report (11).md](/Users/zhiwenxiang/Downloads/deep-research-report%20(11).md)
- 共享 contract：[Quant-Report-Contract.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Quant-Report-Contract.md)

## 本轮目标

这轮不是继续在单个 part 上堆指标，而是把 `Part 0–5 + Horizontal System` 真正接成一个统一控制塔：

- 每个 section 明确自己的分析颗粒度
- 每个 section 明确自己覆盖的通道范围
- 每个 section 明确自己依赖的主数据、证据链和规则库
- 每个 report 顶层都能汇总控制塔绑定情况

## 新增的共享字段

所有 section 现在统一新增：

- `granularity`
  - `analysis_grain`
  - `entity_grain`
  - `time_grain`
- `channel_scope`
- `master_data_ref`
- `evidence_ref`
- `rule_ref`
- `gate_result`

所有 report 的 `overview` 现在统一新增：

- `connected_channel_scope`
- `control_tower_binding.master_data_ref_coverage_ratio`
- `control_tower_binding.evidence_ref_coverage_ratio`
- `control_tower_binding.rule_ref_coverage_ratio`
- `control_tower_binding.gate_status_mix`

## 这解决了什么问题

### 1. 通道没有统一接通

之前：

- Part 4 和 Part 5 有明显的渠道视角
- Part 1 和 Part 2 也在分析渠道，但外层 contract 不知道这些 section 属于哪些通道
- 横向系统和 Part 0 也没有把渠道范围显式暴露出来

现在：

- 所有与渠道相关的 section 都明确暴露 `channel_scope`
- report 顶层可直接看到 `connected_channel_scope`

### 2. 颗粒度没有统一表达

之前：

- 只有人读文档时才知道某一节到底是按 `month`、`sku`、`supplier` 还是 `experiment` 在分析

现在：

- 每个 section 都固定输出 `analysis_grain / entity_grain / time_grain`
- 前端、PDF、审计层都可以直接读取

### 3. 控制塔没有真正下沉到业务章节

之前：

- `Part 0` 和 `Horizontal System` 是治理层
- `Part 1–5` 是业务层
- 但二者在 report contract 上没有强制连起来

现在：

- 每个业务 section 都要显式声明：
  - 依赖哪些主数据
  - 依赖哪些证据链
  - 受哪些规则约束

## 已覆盖范围

当前已完成：

- [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- [part4.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part4.py)
- [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
- [reporting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/reporting.py)

## 当前状态

现在的系统已经可以回答这类问题：

- 这个 section 分析的是哪个颗粒度？
- 这个 section 覆盖了哪些通道？
- 这个 section 依赖哪些主数据定义？
- 这个 section 的结论要回到哪条证据链？
- 这个 section 受哪些 Gate / Guardrail / Stop-Loss 约束？

## 下一步最值的动作

如果继续推进，这轮之后最值的是：

1. 把 `master_data_ref / evidence_ref / rule_ref` 升级成真实 ID 映射，而不是当前字符串引用
2. 把 `gate_result` 与横向规则库的触发记录真正联动
3. 给 PDF / dashboard 增加“控制塔绑定视图”，按通道和 section 直接展示依赖关系
