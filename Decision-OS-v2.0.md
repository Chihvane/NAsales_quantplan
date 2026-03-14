# Decision OS v2.0

## 定义

`Decision OS v2.0` 是对当前 `Part 0–5 + Horizontal System` 的系统级重构版本。

这一版的重点不再是报告 contract，而是把整套系统改写为：

> Field -> Metric -> Factor -> Model -> Gate -> Capital -> Portfolio -> Feedback

的企业级量化决策操作系统。

## 核心目标

- 所有对象有唯一 `id`
- 所有对象有 `schema_version`
- 所有对象可通过 `ref_key` 跨层引用
- 所有决策可自动执行
- 所有决策可资本约束
- 所有决策可风险预算
- 所有执行结果可反馈回模型

## 八层结构

### 1. Field Layer

- 数据最小颗粒度
- 强制来源、刷新频率、验证规则、置信等级

### 2. Metric Layer

- 可计算表达式
- 字段依赖
- 聚合粒度

### 3. Factor Layer

- 指标组合而成的决策因子
- 统一归一化与权重

### 4. Model Layer

- 预测、模拟、优化、因果
- 标准输入输出

### 5. Gate Layer

- Go / No-Go / Scale / Exit
- 统一规则执行

### 6. Capital Layer

- total capital
- allocated capital
- free capital
- cost of capital

### 7. Portfolio Layer

- 多机会并行排序
- 资本分配
- 集中度控制

### 8. Feedback Layer

- 实际执行结果
- 预测误差
- 重校准标记

## v2.0 与 v1.0 的主要差异

- `v1.0` 更像系统蓝图和 Gate 单点运行时
- `v2.0` 把 `capital / risk / portfolio / feedback` 提升为一等对象
- `v2.0` 的 Gate 可以同时读取：
  - model outputs
  - factor scores
  - capital state
  - risk budget

## 工程交付

### 文档

- [Decision-OS-v2.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v2.0.md)
- [Decision-OS-v2.0-Architecture.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v2.0-Architecture.md)

### Python Runtime

- [__init__.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/__init__.py)
- [models.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/models.py)
- [registry_loader.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry_loader.py)
- [gate_engine_v2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/gate_engine_v2.py)
- [capital_allocator.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/capital_allocator.py)
- [feedback_engine.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/feedback_engine.py)
- [demo.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/demo.py)

### YAML Registry

- [system.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/system.yaml)
- [field.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/field.template.yaml)
- [metric.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/metric.template.yaml)
- [factor.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/factor.template.yaml)
- [model.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/model.template.yaml)
- [gate.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/gate.template.yaml)
- [portfolio_model.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/portfolio_model.template.yaml)
- [decision_record.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/decision_record.template.yaml)
- [feedback_record.template.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/schemas/feedback_record.template.yaml)
- [capital_pool.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/config/capital_pool.yaml)
- [risk_budget.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/config/risk_budget.yaml)
- [gate_market_entry.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision_os_v2/registry/examples/gate_market_entry.yaml)

## 当前最小可运行能力

当前 runtime 已支持：

- Gate 条件计算
- 资本约束判断
- 风险预算判断
- 多机会资本分配
- 执行反馈误差评估

## 下一步

下一步最值的是把 `Decision OS v2.0` 与现有 `Part 3 / Part 4 / Part 5` 接起来：

- `Part 3` 提供 landed cost / supply risk
- `Part 4` 提供 channel ROI / payback
- `Part 5` 提供 actual operating feedback
