# Decision OS v1.0

## 定位

`Decision OS v1.0` 是对当前 `Part 0–5 + Horizontal System` 的系统级重构说明。

它不再把系统定义为“研究报告模板”，而是定义为：

> 企业级量化决策操作系统

核心目标：

- 让字段、指标、因子、模型、Gate、资本、风险进入同一套机器可读 contract
- 让任意决策都可以追溯到最底层字段
- 让 Go / No-Go / Scale / Exit 决策由规则引擎执行，而不是只靠人工阅读报告

## 七层结构

### Layer 0 Governance Layer

- schema version
- namespace
- ID system
- capital budget
- risk budget
- ownership
- approval chain

### Layer 1 Data Layer

- field definitions
- source systems
- refresh cadence
- confidence level
- validation rules

### Layer 2 Metric Layer

- formulas
- field dependencies
- aggregation grain
- metric ownership

### Layer 3 Factor Layer

- normalized decision factors
- weighted components
- positive / negative direction

### Layer 4 Model Layer

- simulation
- forecasting
- causal evaluation
- scenario engine

### Layer 5 Gate Engine

- market entry
- supply commitment
- channel launch
- scaling
- stop-loss
- exit

### Layer 6 Capital & Risk Layer

- capital pool
- free capital
- required capital
- risk limits
- drawdown budget
- inventory exposure budget

### Layer 7 Execution Feedback Loop

- alerts
- runbooks
- audit records
- decision replay
- post-mortem

## 核心原则

1. 所有字段必须有 `field_id`
2. 所有指标必须有 `metric_id`
3. 所有因子必须由指标组合而成
4. 所有模型必须声明输入、输出、假设与验证方法
5. 所有 Gate 必须读取模型输出与资本 / 风险约束
6. 所有决策必须生成标准化 `decision_record`
7. 所有层都必须带 `schema_version` 与 `ref_key`

## 与现有 Part 0–5 的映射

### Part 0 = Governance Kernel

- ID system
- schema version
- capital / risk config
- gate registry
- approval flow

### Part 1 = Market Quant Engine

- market factors
- demand stability
- competition intensity
- market entry pre-signal

### Part 2 = Product Intelligence Engine

- SKU attractiveness
- pricing sweet spot
- review risk
- product-level decision signals

### Part 3 = Supply Chain Engine

- landed cost distribution
- route risk
- supplier reliability
- working-capital pressure

### Part 4 = Channel Engine

- channel ROI
- payback
- traffic efficiency
- channel launch / scale gates

### Part 5 = Operating System Engine

- daily / weekly contribution profit
- run-rate capital efficiency
- alerting
- experimentation
- execution gates

## 交付包组成

- 系统主配置：[system.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/system.yaml)
- README：[README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/README.md)
- 架构图：[Decision-OS-v1.0-Architecture.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v1.0-Architecture.md)
- Gate 引擎代码：[gate_engine.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/gate_engine.py)
- schema 模板：
  - [field_schema.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/field_schema.template.yaml)
  - [metric_schema.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/metric_schema.template.yaml)
  - [factor_schema.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/factor_schema.template.yaml)
  - [model_schema.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/model_schema.template.yaml)
  - [gate_schema.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/gate_schema.template.yaml)
  - [decision_record.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/schemas/decision_record.template.yaml)
- 配置模板：
  - [capital_config.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/config/capital_config.template.yaml)
  - [risk_config.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/config/risk_config.template.yaml)
- 示例：
  - [market_entry_bundle.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os/examples/market_entry_bundle.yaml)

## 系统运行顺序

1. 注册字段 schema
2. 计算指标
3. 组装因子
4. 运行模型
5. 调用 Gate Engine
6. 检查资本与风险约束
7. 生成 `decision_record`
8. 写入审计链与反馈回路

## Gate 决策标准化输出

每次 Gate 运行至少输出：

- `decision_record_id`
- `gate_id`
- `gate_version`
- `model_version`
- `capital_config_ref`
- `risk_config_ref`
- `status`
- `failed_conditions`
- `capital_check`
- `risk_check`
- `approved_by`
- `generated_at`

## 当前工程状态

这一版是 `Decision OS v1.0` 的第一版正式交付包，已经包含：

- 统一 YAML 样板
- 系统结构图
- Gate Engine Python 骨架
- 决策记录模板
- 资本与风险配置模板
- 与现有 `Part 0–5 + Horizontal System` 的映射说明

## 下一步

下一步最值的是：

1. 把字符串级 `master_data_ref / evidence_ref / rule_ref` 升级为真实 ID 映射
2. 把 `Gate Engine` 真正接到现有 `Part 3 / Part 4 / Part 5` 输出
3. 把 `capital_config` 与 `risk_config` 接入真实预算和风险预算数据
