# Part 2 Deep Optimization Crosswalk

这份对照稿用于把 `deep-research-report (15).md` 的深度要求，映射到当前工作区已经存在的 `Part 2` 计划与代码结构。

## 已吸收的方向

- 把 `Part 2` 从竞品分析模块升级为 `Product Intelligence Engine`
- 增加 `A / B / C / D` 证据分层
- 增加概率化输出与 `confidence_band`
- 增加 `Bayesian evidence scoring`、`Monte Carlo`、`AHP`、`SHAP` 等模型/工具模块
- 增加 `calibration / PPC / drift monitor` 作为正式验证对象
- 增加 `2-6 周 MVP` 路线，而不是只写长期目标

## 与当前系统的对接方式

### 1. 文档层

主计划文件：

- [Part2-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Quantitative-Optimization-Plan.md)

链条入口：

- [Part2-Chain.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-chains/Part2-Chain.md)

### 2. 配置层

计划配置：

- [part2_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part2_quant_plan.yaml)

### 3. 后续代码层

本轮还没有直接改 `part2.py` 和 `part2_metrics.py` 的指标实现，当前落地的是：

- 正式优化计划
- `Decision OS` 配置骨架
- 统一链条入口

下一轮 coding 的第一批对象应当是：

- `Part2Dataset` 新增治理表
- `FAC-VALUE-ADVANTAGE`
- `FAC-VOC-RISK`
- `confidence_band`
- `calibration_report`
- `drift_report`

## 当前建议

下一步最合理的动作不是继续扩文档，而是开始把 `part2_source_registry / part2_threshold_registry / part2_benchmark_registry / voc_event_registry` 接进 `Part 2Dataset`，然后补 `FAC-VALUE-ADVANTAGE` 和 `FAC-VOC-RISK`。
