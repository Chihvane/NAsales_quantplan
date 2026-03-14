# Part 5 GitHub 架构对照

## 对照目标

这份对照不是为了照搬大型开源系统，而是为了验证 Part 5 的代码骨架是否遵循了更成熟的拆分方式，避免把“上线后经营优化”继续写成单文件脚本。

本轮主要参考了四类 GitHub 开源项目：

- [GrowthBook](https://github.com/growthbook/growthbook)
- [Great Expectations](https://github.com/great-expectations/great_expectations)
- [Evidently](https://github.com/evidentlyai/evidently)
- [Prophet](https://github.com/facebook/prophet)
- [CVXPY](https://github.com/cvxpy/cvxpy)

## 本地骨架与开源项目的对应关系

### 1. 实验系统: 对齐 GrowthBook

GrowthBook 的核心价值不是单一实验公式，而是把实验注册、指标、最小样本量、实验状态管理拆成独立系统。

Part 5 当前对齐方式：

- [part5_experiments.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_experiments.py)
- [experiment_registry.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/part5_demo/experiment_registry.csv)

已吸收的结构：

- 用独立实验注册表而不是把实验字段散落在报表逻辑里
- 单独输出 `coverage_ratio / test_velocity / sample_size_guidance / causal_confidence_score`
- 将实验系统放在 `5.6`，而不是混入增长章节

当前差距：

- 还没有真正的实验结果归因层
- 还没有实验模板、变体配置和停止规则执行器

### 2. 数据质量与监控: 对齐 Great Expectations / Evidently

Great Expectations 强调“校验”和“数据本身”分离，Evidently 强调“持续监控”和“漂移/异常面板”分离。

Part 5 当前对齐方式：

- [validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)
- [part5_alerts.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_alerts.py)
- [part5.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5.py)

已吸收的结构：

- `validation` 负责方法与结果边界校验
- `alerts` 负责经营异常识别
- 报告生成层只做装配，不混入规则细节

当前差距：

- 还没有字段级 expectation catalog
- 还没有时间滚动的漂移监控视图
- 目前告警还是规则式，不是统计过程控制或异常检测模型

### 3. 预测层: 对齐 Prophet

Prophet 的关键启发不是必须使用其模型，而是把预测层做成可替换模块，而不是把趋势判断硬编码在报表函数里。

Part 5 当前对齐方式：

- [part5_forecasting.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_forecasting.py)

已吸收的结构：

- 把 `daily_revenue / moving_average / trend_direction / next_7d forecast` 放在独立模块
- `5.3` 只消费预测结果，不直接实现预测逻辑

当前差距：

- 现在仍是轻量趋势汇总器，不是真正的时间序列模型
- 后续可直接替换成 Prophet、SARIMAX 或分渠道分 SKU 的分层预测器

### 4. 优化器: 对齐 CVXPY

CVXPY 的启发是把预算分配和资源约束问题写成独立优化模块，而不是嵌在业务逻辑里手搓排序。

Part 5 当前对齐方式：

- [part5_optimization.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part5_optimization.py)

已吸收的结构：

- 预算分配模块独立
- 支持 `cvxpy` 求解器，有 fallback heuristic
- 约束包括预算总和、单渠道上限、平滑惩罚

当前差距：

- 目标函数仍是经验打分，不是历史回报拟合
- 还没有库存、现金流、服务水平的联合约束

## 为什么当前骨架是合理的

Part 5 现在已经形成了与成熟 GitHub 项目相近的分层：

- `pipeline` 负责输入装配
- `metrics` 负责业务指标计算
- `forecasting` 负责趋势预测
- `experiments` 负责实验系统
- `alerts` 负责经营监控
- `optimization` 负责预算分配
- `uncertainty / validation / charts / cli` 负责通用横切层

这个拆法的好处是：

- 后续替换单一模块成本低
- 可以逐步把 demo 规则升级成真实模型
- 报告层不会被训练、监控、优化代码污染

## 下一步建议

按优先级建议继续推进：

1. 把 `part5_forecasting.py` 升级成真正的时间序列预测器
2. 把 `part5_alerts.py` 从阈值告警升级成统计异常检测
3. 把 `part5_experiments.py` 加入实验结果归因和止损逻辑
4. 把 `part5_optimization.py` 接入真实预算和库存约束
