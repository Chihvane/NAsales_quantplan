# Part 3 Deep Optimization Crosswalk

这份对照稿用于把 `deep-research-report (16).md` 的要求，映射到当前工作区的 `Part 3` 计划与代码结构。

## 已吸收的方向

- 把 `Part 3` 从供应链可行性模块升级为 `Supply Chain Engine`
- 明确加入 `VaR / Expected Shortfall / tail-risk` 这类下行风险指标
- 把 `best scenario` 思路升级为 `constraint-based optimization`
- 把 Monte Carlo 从单一 percentile 输出，升级到 tail-risk + stress suite
- 补上 `golden scenario / regression / drift` 的验证思路

## 与当前系统的对接方式

### 1. 文档层

主计划文件：

- [Part3-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Optimization-Plan.md)

链条入口：

- [Part3-Chain.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-chains/Part3-Chain.md)

### 2. 配置层

计划配置：

- [part3_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part3_quant_plan.yaml)

### 3. 后续代码层

本轮还没有直接改 `part3.py / part3_metrics.py / part3_simulation.py`，当前落地的是：

- 正式优化计划
- `Decision OS` 配置骨架
- 统一链条入口

下一轮 coding 的第一批对象应当是：

- `part3_source_registry`
- `part3_threshold_registry`
- `part3_scenario_registry`
- `part3_optimizer_registry`
- `part3_risk_metrics`
- `part3_optimizer`
- `part3_stress_suite`

## 当前建议

下一步最合理的动作不是继续扩文档，而是开始把治理表接进 `Part3Dataset`，然后补 `VaR / ES` 和约束优化器。
