# Part 0-1 架构与建模优化对照

本文用于把 [Part 0–1 架构与建模优化方案.pdf](/Users/zhiwenxiang/Downloads/Part%200%E2%80%931%20%E6%9E%B6%E6%9E%84%E4%B8%8E%E5%BB%BA%E6%A8%A1%E4%BC%98%E5%8C%96%E6%96%B9%E6%A1%88.pdf) 中的细化要求，对照到当前 Part 0 / Part 1 文档与代码实现。

## 已落地项

### Part 0

- 战略 Gate 家族覆盖：
  - 已在 [part0_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_metrics.py) 中落地 `capital_return / market_structure / demand_stability / payback_control / risk_control`
  - 已输出 `strategic_metric_family_coverage_ratio / strategic_metric_family_mix / strategic_gate_score`
- Gate demo 数据已补 ROIC、HHI、热度波动、Payback、风险类阈值：
  - [gate_thresholds.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/part0_demo/gate_thresholds.csv)
- Part 0 决策摘要已把战略 Gate 覆盖并入顶层信号：
  - [decision_summary.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/decision_summary.py)

### Part 1

- 市场规模参考面板：
  - 新增 [market_size_inputs.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/market_size_inputs.csv)
  - 新增 `compute_market_size_input_panel`
- 渠道基准面板：
  - 新增 [channel_benchmarks.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/channel_benchmarks.csv)
  - 新增 `channel benchmark gap` 计算
- 市场热度稳定性：
  - 已在 `1.1` 加入 `heat_volatility_coefficient`
  - 已补搜索热度与销量的领先滞后扫描
- Top-Down 假设不再只有固定参数：
  - 现在同时输出假设口径与参考面板口径偏差

## 对应代码入口

- Part 0:
  - [part0.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0.py)
  - [part0_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part0_metrics.py)
- Part 1:
  - [part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
  - [metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py)
  - [pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/pipeline.py)
  - [loaders.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/loaders.py)
  - [models.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/models.py)

## 仍保留为后续项

- Part 1 事件库与完整事件驱动模型
- Part 1 更长时间窗的 demand-sales lag 建模
- API connector 层的正式调度而非 demo CSV
- 更完整的图表模板库

## 当前状态

当前 Part 0-1 已从“章节框架 + 基础指标”升级为：

- 治理层有战略 Gate 家族
- 市场规模层有参考面板
- 渠道层有基准偏差
- 决策摘要层会显式反映这些新增约束
