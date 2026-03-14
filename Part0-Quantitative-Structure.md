# Part 0 Quantitative Structure

## 目的

Part 0 的目标不是做市场分析，而是把整套研究体系升级成治理系统。

它负责三件事：

1. 统一证据等级、版本和更新失效规则
2. 统一 Gate、责任链和签字链
3. 统一字段命名、主数据口径和跨项目复用规范

## 范围边界

Part 0 不做：

- 具体市场规模估算
- SKU 画像与价格带判断
- RFQ、到岸成本和渠道 ROI 测算

Part 0 只做这些工作的治理底座。

## 固定交付物

- 决策树总图
- 数据置信度表
- 假设登记表
- Gate 阈值表
- 签字链表
- 更新周期与失效规则表
- 字段字典
- Part 0 治理评分报告

## 标准输入表

### `decision_nodes.csv`

- `node_id, parent_id, gate_id, stage, decision_question, domain, metric_ref, owner_role, go_path, hold_path, kill_path`
- 用于构建全局决策树

### `evidence_sources.csv`

- `source_id, topic, source_name, source_type, confidence_grade, collected_at, freshness_days, version, status, owner_role`
- 用于证据等级、版本与时效分析

### `assumptions_register.csv`

- `assumption_id, domain, assumption_text, rationale, confidence_grade, owner_role, validation_method, status, due_date`
- 用于假设治理

### `gate_thresholds.csv`

- `gate_id, gate_name, metric_name, operator, threshold_value, unit, source_grade_min, approver_role, decision_if_fail`
- 用于 Gate 可执行性分析
- 建议强制覆盖五类战略 Gate 家族：
  - `capital_return`：`roic / roi / irr / margin`
  - `market_structure`：`tam / sam / som / hhi / cagr`
  - `demand_stability`：`heat_volatility / trend_lag / seasonality`
  - `payback_control`：`payback_months / cash_cycle`
  - `risk_control`：`compliance / tariff / supplier_risk / fx_risk`

### `approval_chain.csv`

- `gate_id, step_order, role_name, owner_name, action_type, status, signed_at, veto_flag`
- 用于责任链与签字流分析

### `update_policies.csv`

- `scope_id, scope_name, update_frequency_days, expiry_days, event_trigger, owner_role, sla_days, status`
- 用于更新与失效规则分析

### `field_dictionary.csv`

- `field_name, field_group, definition, data_type, naming_style, source_table, reusable_flag, required_flag`
- 用于字段复用和命名治理

## 章节结构

### `0.1 全局决策树与研究问题映射`

建议指标：

- `decision_node_count`
- `gate_count`
- `leaf_count`
- `gate_coverage_ratio`
- `domain_coverage_ratio`
- `owner_coverage_ratio`
- `decision_tree_score`

### `0.2 数据置信度与版本控制`

建议指标：

- `confidence_mix`
- `version_coverage_ratio`
- `status_coverage_ratio`
- `owner_coverage_ratio`
- `freshness_compliance_ratio`
- `auditability_score`

### `0.3 策略假设登记与验证机制`

建议指标：

- `assumption_count`
- `validated_ratio`
- `validation_method_coverage_ratio`
- `high_confidence_share`
- `overdue_assumption_count`
- `assumption_governance_score`

### `0.4 决策门槛与 Gate 管理`

建议指标：

- `gate_coverage_ratio`
- `threshold_completeness_ratio`
- `approver_coverage_ratio`
- `fail_action_coverage_ratio`
- `source_grade_policy_coverage_ratio`
- `strategic_metric_family_coverage_ratio`
- `strategic_metric_family_mix`
- `strategic_gate_score`
- `gate_operability_score`

### `0.5 责任链与签字流`

建议指标：

- `gate_signoff_coverage_ratio`
- `minimum_step_pass_ratio`
- `signed_completion_ratio`
- `veto_coverage_ratio`
- `signature_chain_score`

### `0.6 更新周期与失效规则`

建议指标：

- `scope_coverage_ratio`
- `expiry_rule_coverage_ratio`
- `event_trigger_coverage_ratio`
- `sla_coverage_ratio`
- `refresh_expiry_alignment_ratio`
- `refresh_policy_score`

### `0.7 字段字典、复用与审计要求`

建议指标：

- `definition_coverage_ratio`
- `data_type_coverage_ratio`
- `source_table_coverage_ratio`
- `reusable_field_share`
- `required_field_share`
- `naming_compliance_ratio`
- `dictionary_reuse_score`

## 统一假设参数

当前代码里建议固定这些 Part 0 假设：

- `required_gate_count`
- `required_decision_domains`
- `required_policy_scopes`
- `required_strategic_metric_families`
- `max_source_age_days`
- `max_assumption_overdue_days`
- `minimum_signoff_steps`
- `required_naming_style`

## 决策摘要层

Part 0 的顶层 `overview` 不应只显示表格完成度，还应固定输出：

- `decision_signal`
- `decision_score`
- `decision_summary`

建议信号：

- `ready_for_execution_system`
- `governance_needs_hardening`
- `not_ready`

## 不确定性与校验

Part 0 不适合做传统统计置信区间，但仍应输出：

- `governance_quality_band`
- `decision_gate_band`
- `auditability_band`

并对以下方面做方法校验：

- 决策树 Gate 覆盖是否完整
- 证据等级占比是否回勾 100%
- 假设验证率是否在合法范围
- Gate 阈值和签字链是否具备最小可执行性
- 更新与失效规则是否成对存在
- 字段字典是否满足命名一致性

## 当前代码骨架

本轮已启动的 Part 0 代码入口：

- [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
- [part0_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_metrics.py)
- [part0_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_pipeline.py)

共享层复用：

- [models.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/models.py)
- [loaders.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/loaders.py)
- [reporting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/reporting.py)
- [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)
- [uncertainty.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/uncertainty.py)
- [cli.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/cli.py)

## 当前定位

这一版是 Part 0 的第一版研发骨架。

它已经具备：

- 标准输入表
- 报告 builder
- 决策摘要
- 校验层
- 图表层
- CLI 入口
- demo 数据
- 战略 Gate 家族覆盖评分

下一步应继续补：

- Part 0 与 Part 1–5 的 Gate 映射规则
- 证据链编号规范
- 主数据词典与跨 part 字段映射
- 治理层 PDF 输出模板
