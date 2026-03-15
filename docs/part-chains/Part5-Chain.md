# Part 5 Unified Chain

## 定位

`Part 5` 是上线后经营控制层，负责把业务运行状态转成扩张、暂停、回滚与资本再配置动作。

## 核心问题

- 上线后看什么指标
- 异常如何发现
- 增长动作如何验证
- 利润如何持续保护
- 何时扩张，何时止损

## 统一链条

### 1. 策略层

固定覆盖：

- 运营目标与门禁
- 数据体系与持续监控
- 增长闭环
- 定价与利润保护
- 库存与现金周转
- 实验与增量优化
- 风险监控与扩张节奏

### 2. 量化层

固定输出：

- 日 / 周 / 月 KPI 体系
- 经营门禁
- alert 与 runbook
- ETL skeleton
- experiment readout
- hierarchy / Bayesian / auto-stop

### 3. 代码层

- [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)
- [part5_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_metrics.py)
- [part5_experiments.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_experiments.py)
- [part5_alerts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_alerts.py)
- [part5_etl.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_etl.py)
- [part5_audit.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_audit.py)
- [part5_forecasting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_forecasting.py)
- [part5_optimization.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_optimization.py)

### 4. 决策层

`Part 5` 输出：

- `scale`
- `pause`
- `rollback`
- `capital reallocation`

并且已和 ETL、实验、audit pack 打通。

## 当前状态

- 已有策略稿
- 已有量化结构
- 已有 ETL skeleton
- 已有实验结果判读
- 已有 auto-stop
- 已有周度经营控制与回测

## source references

- [Part5-Post-Launch-Operations-Optimization-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Post-Launch-Operations-Optimization-Strategy.md)
- [Part5-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Quantitative-Structure.md)
- [Part5-GitHub-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-GitHub-Crosswalk.md)
- [Part5-Execution-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part5-Execution-Optimization-Crosswalk.md)
- [Part5-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Part5-README.md)
