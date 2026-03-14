# 横向系统管理模块量化结构

## 目标

横向模块的目标不是预测市场，而是回答三个治理问题：

1. 主数据是否稳定且可复用
2. 证据链是否完整且可审计
3. 决策规则是否可执行且可闭环

## 标准输入表

### `master_data_entities.csv`

- `entity_type`
- `entity_id`
- `entity_name`
- `owner_role`
- `version`
- `approved_flag`
- `active_flag`
- `duplicate_flag`
- `missing_required_field_count`
- `updated_at`

建议至少覆盖这些核心 `entity_type`：

- `sku`
- `channel`
- `calendar`
- `price_metric`
- `supplier`

### `data_dictionary_fields.csv`

- `field_name`
- `field_group`
- `entity_type`
- `data_type`
- `required_flag`
- `enum_flag`
- `validation_rule`
- `version`
- `approved_flag`

建议至少覆盖这些核心 `field_group`：

- `product`
- `channel`
- `time`
- `price`

### `evidence_lineage.csv`

- `lineage_id`
- `source_id`
- `target_metric_id`
- `dataset_version`
- `transform_step_count`
- `script_version`
- `generated_at`
- `approval_ref`
- `reproducible_flag`
- `reconstruction_minutes`

### `audit_events.csv`

- `audit_id`
- `event_type`
- `object_type`
- `object_id`
- `actor_role`
- `happened_at`
- `immutable_flag`
- `approval_ref`
- `status`

### `decision_rules.csv`

- `rule_id`
- `scenario`
- `gate_name`
- `metric_name`
- `operator`
- `threshold_value`
- `severity`
- `approver_role`
- `active_flag`
- `version`
- `stop_loss_flag`

建议至少覆盖这些核心 `scenario`：

- `market_entry`
- `pilot_scale`
- `sku_exit`
- `channel_exit`
- `ad_pause`

### `decision_triggers.csv`

- `trigger_id`
- `rule_id`
- `object_scope`
- `triggered_at`
- `observed_value`
- `decision_status`
- `resolved_flag`
- `approval_ref`

## 章节结构

### `H1 数据字典与主数据管理`

核心指标：

- `entity_type_coverage_ratio`
- `covered_required_entity_types`
- `missing_required_entity_types`
- `dictionary_approval_ratio`
- `duplicate_free_ratio`
- `required_field_compliance_ratio`
- `validation_rule_coverage_ratio`
- `core_field_group_coverage_ratio`
- `master_data_health_score`

### `H2 证据链与审计链`

核心指标：

- `reproducibility_ratio`
- `traceback_sla_ratio`
- `immutable_audit_ratio`
- `approval_linkage_ratio`
- `audit_approval_ref_ratio`
- `audit_trace_score`

### `H3 决策门槛系统`

核心指标：

- `scenario_coverage_ratio`
- `active_rule_ratio`
- `stop_loss_rule_ratio`
- `trigger_resolution_ratio`
- `trigger_approval_ref_ratio`
- `decision_gate_control_score`

## 顶层输出

横向模块报告同样复用统一 contract：

- `metadata`
- `overview`
- `sections`
- `uncertainty`
- `validation`

并强制输出：

- `headline_metrics`
- `decision_signal`
- `decision_score`
- `decision_summary`

## 当前代码入口

- [models.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/models.py)
- [loaders.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/loaders.py)
- [horizontal_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_pipeline.py)
- [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
- [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)
- [charts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/charts.py)

## 当前定位

这一版是横向系统模块的第一版代码骨架，已经具备：

- 标准输入表
- 报告 builder
- 顶层决策摘要
- 校验层
- 图表层
- CLI 入口
- demo 数据

## 与 DOCX 总稿的关系

这份量化结构已经对齐 [北美市场量化报告框架.docx](/Users/zhiwenxiang/Downloads/北美市场量化报告框架.docx) 里的三段式写法，但额外补了代码所需的治理约束：

- 从“至少维护主数据表”升级为“显式必备 `entity_type` 列表”
- 从“至少维护决策门槛模板”升级为“显式必备 `scenario` 列表”
- 从“建议记录字段”升级为“标准输入表 + 校验规则 + 输出指标”
