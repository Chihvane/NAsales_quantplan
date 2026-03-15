# Decision OS Unified Chain

## 定位

`Decision OS` 是整个项目从研究报告体系升级到企业级量化决策操作系统之后的工程主链。

## 核心问题

- 如何把字段、指标、因子、模型、Gate、资本、风险、组合和反馈收敛成可执行系统
- 如何让报告输出进入真实 Gate 评估、回测、部署和审计

## 统一链条

### 1. 白皮书层

演进版本：

- `v1.0`：字段到 Gate 的基础结构
- `v2.0`：资本与风险约束进入系统
- `v3.0`：数据库、部署、Dashboard、回测、SaaS 结构成形

### 2. 工程层

主工程目录：

- [decision-os](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os)

关键模块：

- `backend`
- `database`
- `backtest`
- `worker`
- `frontend`
- `report_engine`

### 3. 数据层

已覆盖：

- schema
- init script
- ORM
- repositories
- tenant-ready design

### 4. 回测层

已覆盖：

- walk-forward engine
- optimization
- stress suite
- backtest reporting

### 5. 桥接层

当前已打通：

- `Part 1`
- `Part 2`

下一步主方向是用 `Part 3 / Part 4` 的真实成本和渠道费率替换 proxy。

## 当前状态

- 已有 v1 / v2 / v3 白皮书
- 已有 GitHub 级工程仓
- 已有数据库生产结构
- 已有 UI MVP
- 已有回测引擎
- 已有 OSS integration blueprint

## source references

- [Decision-OS-v1.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v1.0.md)
- [Decision-OS-v2.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v2.0.md)
- [Decision-OS-v3.0.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0.md)
- [Decision-OS-v3.0-Dashboard-Spec.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Decision-OS-v3.0-Dashboard-Spec.md)
- [decision-os/README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/README.md)
