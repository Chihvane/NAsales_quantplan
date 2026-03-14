# Decision OS v3.0

## Enterprise Quantitative Strategy & Governance Framework

### 北美小众兴趣商品量化决策操作系统白皮书

## 目录

1. 系统定位与目标
2. 核心原则
3. 七层结构模型
4. 统一颗粒度对齐体系
5. 横向治理模块
6. Gate Engine 规则体系
7. 资本与风险预算系统
8. Portfolio 管理与反馈机制
9. 审计与可追溯体系
10. 组织落地与实施路径

## 1. 系统定位与目标

`Decision OS` 是一个企业级量化决策操作系统，用于统一：

- 市场研究
- 品类选择
- 供应链决策
- 渠道配置
- SKU 生命周期管理
- 资本分配
- 风险预算控制
- 投放与退出机制

其目标是：

> 将“分析报告”升级为“可执行决策引擎”。

## 2. 核心原则

1. 所有决策必须可溯源到字段。
2. 所有模型必须可版本化。
3. 所有 Gate 必须规则化。
4. 所有资本必须受风险预算约束。
5. 所有执行必须反馈回模型校准。
6. 所有规则必须可程序执行。

## 3. 七层结构模型

```text
L0 Governance Kernel
L1 Field Layer
L2 Metric Layer
L3 Factor Layer
L4 Model Layer
L5 Gate Engine
L6 Capital & Risk Layer
L7 Portfolio & Feedback Layer
```

## 4. 统一颗粒度对齐体系

### 4.1 字段级（Field Layer）

字段是最低颗粒度单位，也是唯一数据源。

每个字段必须定义：

```yaml
field_id:
schema_version:
entity:
data_type:
unit:
source:
update_frequency:
confidence_level:
owner:
ref_key:
```

### 4.2 指标级（Metric Layer）

指标是可计算表达式。

```yaml
metric_id:
schema_version:
formula:
depends_on:
aggregation_level:
```

### 4.3 因子级（Factor Layer）

因子是决策抽象变量。

```yaml
factor_id:
schema_version:
components:
normalization_method:
weighting_logic:
```

### 4.4 模型级（Model Layer）

模型负责模拟与预测。

```yaml
model_id:
schema_version:
type:
inputs:
outputs:
validation_method:
```

### 4.5 Gate 级（Decision Gate Layer）

Gate 统一所有决策逻辑。

```yaml
gate_id:
schema_version:
logic: AND/OR
conditions:
capital_constraint:
risk_constraint:
```

### 4.6 资本层（Capital Layer）

```yaml
capital_pool:
total:
allocated:
free:
cost_of_capital:
```

### 4.7 风险层（Risk Layer）

```yaml
risk_budget:
max_loss_probability:
max_drawdown:
max_inventory_exposure:
max_channel_dependency:
```

## 5. 横向治理模块

### 5.1 数据字典与主数据管理

核心要求：

- 所有字段必须注册
- 所有字段必须可追溯
- 所有字段必须有 `schema_version`
- 所有字段必须可跨模块引用

主数据对象：

- SKU
- Channel
- Supplier
- Market
- Currency
- Region

### 5.2 证据链与审计链

任何结论都必须回答：

- 来源是什么
- 数据版本是多少
- 谁计算的
- 谁审批的
- 何时生效

每条决策必须生成：

```yaml
decision_record:
decision_id:
gate_id:
model_version:
capital_version:
risk_version:
approved_by:
approved_at:
hash_signature:
```

### 5.3 统一决策门槛系统

决策场景包括：

- 市场进入
- SKU 上线
- SKU 下线
- 渠道扩张
- 渠道退出
- 投放启动
- 投放停止
- 资本再分配

每个场景必须：

- 有固定 `Gate ID`
- 有固定阈值
- 有可执行规则

## 6. Gate Engine 规则体系

`Gate Engine` 是系统核心。

所有 Gate 必须：

- 读取模型输出
- 读取资本池状态
- 读取风险预算
- 输出 `GO / NO_GO / SCALE / EXIT`

Gate 不允许人工绕过，人工审批只能在记录层确认，不允许改变引擎结果。

## 7. 资本与风险预算系统

### 7.1 资本控制

决策必须满足：

```text
required_capital <= free_capital
```

### 7.2 风险控制

必须满足：

```text
loss_probability <= max_loss_probability
expected_drawdown <= max_drawdown
```

## 8. Portfolio 管理与反馈机制

### 8.1 组合优化

目标：

```text
Maximize(Expected Return)
Subject to:
  Capital Constraint
  Risk Constraint
```

### 8.2 反馈循环

每个模型必须接受：

- 实际利润
- 实际波动
- 实际损失

并输出重校准标记与误差记录。

## 9. 审计与可追溯体系

必须实现：

- 字段级血缘图
- 模型级版本记录
- Gate 级审批留痕
- 资本分配历史
- 风险暴露历史

系统必须可回答：

> 任意决策在任意时间点的完整路径。

## 10. 组织落地与实施路径

阶段 1：字段与主数据规范化  
阶段 2：指标与因子结构统一  
阶段 3：Gate Engine 上线  
阶段 4：资本风险模块嵌入  
阶段 5：Portfolio 优化引擎  
阶段 6：全链路自动化

## 最终状态

`Decision OS v3.0` 实现：

- 咨询级结构严谨性
- 量化工程级可执行性
- 自动化决策能力
- 风险与资本硬约束
- 全链条可追溯
