# Part 0 Unified Chain

## 定位

`Part 0` 是整个系统的治理内核，不负责判断某个品类能不能做，而负责约束所有 `Part 1-5` 的证据等级、Gate、签字链、更新失效与字段口径。

## 核心问题

- 这套研究体系是否稳定、可复用、可审计
- 每个章节的结论是否都能回到统一证据等级与统一 Gate
- 团队是否具备推进、暂停、回滚、退出的明确责任链

## 统一链条

### 1. 策略层

- 全局决策树
- 证据置信度
- 假设登记与验证
- Gate 阈值
- 审批链
- 更新与失效规则

### 2. 量化层

标准输入：

- `decision_nodes.csv`
- `evidence_sources.csv`
- `assumptions_register.csv`
- `gate_thresholds.csv`
- `approval_chain.csv`
- `update_policies.csv`
- `field_dictionary.csv`

标准输出：

- `part0_report.json`
- Part 0 charts
- 治理评分、证据评分、Gate 覆盖评分

### 3. 代码层

- [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- [part0_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_metrics.py)
- [part0_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_pipeline.py)

### 4. 决策层

`Part 0` 的输出会约束：

- `master_data_ref`
- `evidence_ref`
- `rule_ref`
- `gate_result`

并向 `Part 1-5` 提供统一治理口径。

## 当前状态

- 已有策略总则
- 已有量化结构
- 已有 demo、CLI、validation
- 已与 `Part 1` 的规则细化对齐

## source references

- [Part0-Research-Governance-And-Decision-Charter.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-Research-Governance-And-Decision-Charter.md)
- [Part0-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-Quantitative-Structure.md)
- [Part0-1-Architecture-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part0-1-Architecture-Optimization-Crosswalk.md)
- [Part0-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Part0-README.md)
