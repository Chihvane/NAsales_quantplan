# `deep-research-report.md` 与当前代码的交叉优化说明

## 已吸收进代码的部分

### 1. 不确定性表达

深度报告建议对关键指标输出 bootstrap 置信区间，而不是只给点估计。  
当前已落地：

- [quant_framework/uncertainty.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/uncertainty.py)
- 在 [quant_framework/part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py) 中新增 `report["uncertainty"]`

当前覆盖：

- 底层市场规模年化估算区间
- 加权平均标价区间
- 平均成交价区间
- 平均折扣率区间
- 平均价格弹性区间
- 标价中位数区间

### 2. 时间滚动验证 / 回测

深度报告建议不要只做静态分析，而要做可重放、可验证的时间序列验证。  
当前已落地：

- [quant_framework/backtest.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/backtest.py)
- [examples/run_backtest_demo.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/run_backtest_demo.py)

当前回测逻辑：

- 生成按月的类别面板数据
- 用历史 `lookback` 窗口计算机会信号
- 根据信号选出 Top N 类别
- 对比下一期收入增速与基准组合
- 输出累计收益、超额收益、命中率和选股记录

### 3. 更明确的工程入口

深度报告建议把研究流程模块化成数据管线而不是散落脚本。  
当前已落地：

- [quant_framework/pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/pipeline.py)
- [quant_framework/cli.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/cli.py)

当前 CLI 支持：

- `report`
- `charts`
- `clean`
- `backtest`
- `backtest-demo`

---

## 暂未落地、但值得继续做的部分

### 1. `source_confidence` 与 `field_quality_flags`

深度报告建议每条记录都带来源可信度和字段质量标记。  
这一点现在只在方法层和验证层体现，还没有真正沉到每条记录的 schema 中。

### 2. 星型模型 / DuckDB / Parquet

当前还是轻量 CSV + Python 对象。  
如果后续进入真实项目，应该继续演进为：

- raw / curated 分层
- DuckDB 或 Parquet 本地数仓
- listing snapshot / sold fact tables

### 3. 更高级的计量模型

深度报告提到：

- STL / Prophet
- log-log OLS
- IV / 2SLS
- Cox 生存分析

这些还没有在当前无第三方依赖的环境里完整落地。  
如果后续允许安装 `statsmodels`、`linearmodels`、`lifelines`，可以继续补齐。

---

## 当前结论

这次交叉优化后，代码已经从“静态量化框架”推进到了“带不确定性输出 + 带回测能力的研究引擎”。  
也就是说，现在这套代码不只是告诉你“市场看起来怎么样”，还能开始验证“当前信号是否对未来表现有预测价值”。

