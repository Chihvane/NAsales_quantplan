# 横向系统模块与框架 DOCX 对照

## 来源

- 总框架文档：[北美市场量化报告框架.docx](/Users/zhiwenxiang/Downloads/北美市场量化报告框架.docx)
- 现有策略稿：[Horizontal-System-Management-Module.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Management-Module.md)
- 现有量化结构：[Horizontal-System-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Quantitative-Structure.md)

## 结论

这份 `docx` 不是新的 `Part`，而是对当前“横向系统管理模块”的另一版写法。其核心三段式结构已经被当前模块覆盖：

- `第一部分：数据字典与主数据管理` -> `H1`
- `第二部分：证据链与审计链` -> `H2`
- `第三部分：决策门槛系统` -> `H3`

当前代码版已经比 `docx` 多出这些可执行能力：

- 标准输入表 contract
- 可量化治理评分
- 校验层
- CLI
- demo 数据
- SVG 图表输出

## 章节映射

### 1. 数据字典与主数据管理

`docx` 重点：

- YAML 元数据结构
- `SKU` 属性字段表
- 渠道字段表
- 时间维度表
- 价格指标字段表

当前落点：

- 文档：[Horizontal-System-Management-Module.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Management-Module.md)
- 量化结构：[Horizontal-System-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Quantitative-Structure.md)
- 标准输入：
  - [master_data_entities.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/master_data_entities.csv)
  - [data_dictionary_fields.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/data_dictionary_fields.csv)
- 代码：
  - [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
  - [horizontal_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_pipeline.py)

本次补齐：

- 从“主数据数量阈值”升级为“显式必备主数据族”
- 增加 `required_field_groups`
- 输出 `covered_required_entity_types / missing_required_entity_types / core_field_group_coverage_ratio`

### 2. 证据链与审计链

`docx` 重点：

- 证据链字段模板
- 审计链字段模板
- 综合记录与版本控制

当前落点：

- 标准输入：
  - [evidence_lineage.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/evidence_lineage.csv)
  - [audit_events.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/audit_events.csv)
- 代码：
  - [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
  - [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)

当前已经覆盖：

- 数据版本
- 脚本版本
- 审批引用
- 可复现实验率
- 追溯 SLA
- 审计不可篡改率

### 3. 决策门槛系统

`docx` 重点：

- 市场进入
- 试点放大
- SKU 下线
- 渠道退出
- 投放中止

当前落点：

- 标准输入：
  - [decision_rules.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/decision_rules.csv)
  - [decision_triggers.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo/decision_triggers.csv)
- 代码：
  - [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
  - [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)

本次补齐：

- 从“规则场景数量阈值”升级为“显式必备场景清单”
- 输出 `covered_required_rule_scenarios / missing_required_rule_scenarios`

## 当前状态

与 `docx` 对齐后，横向模块现在更像控制塔规范，而不是单独一份说明文档。它已经可以直接为 `Part 0–5` 提供：

- 主数据口径约束
- 证据链编号与审计可追溯
- Go / No-Go / Stop-Loss 规则库
- 治理评分与验证结果

## 后续最值的动作

下一步最值的是把横向模块继续下沉到 `Part 0–5`，给各 part 统一增加：

- `master_data_ref`
- `evidence_ref`
- `rule_ref`
- `gate_result`
