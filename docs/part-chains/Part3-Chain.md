# Part 3 Unified Chain

## 定位

`Part 3` 是供应链、出口路径与 landed cost 决策层，负责把市场机会变成可落地的中国供应方案。

## 核心问题

- 中国供应链能不能稳定承接
- 报价、MOQ、交期是否有竞争力
- 合规、认证、物流、关税是否可控
- landed cost 之后还有没有利润安全边际

## 统一链条

### 1. 策略层

固定回答：

- 供应端结构是否成熟
- 国内采购与报价策略
- 合规与准入门槛
- 出口路径与物流履约
- 到岸成本与利润安全边际
- 风险矩阵
- 推荐进入路径与首批执行方案

### 2. 数据层

标准输入：

- `suppliers.csv`
- `rfq_quotes.csv`
- `compliance_requirements.csv`
- `logistics_quotes.csv`
- `tariff_tax.csv`
- `shipment_events.csv`

### 3. 代码层

- [part3.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3.py)
- [part3_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_metrics.py)
- [part3_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_pipeline.py)
- [part3_simulation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part3_simulation.py)

### 3.1 优化计划层

- [Part3-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Optimization-Plan.md)
- [Part3-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Deep-Optimization-Crosswalk.md)
- [part3_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part3_quant_plan.yaml)

### 4. 模型层

已覆盖：

- landed cost 方案比较
- 蒙特卡洛利润带
- 敏感度分析
- 供应链风险评分

优化计划中的目标能力会扩到：

- `VaR / ES / tail-risk`
- `constraint-based optimization`
- `stress suite`
- `golden scenario regression`

### 5. 决策层

`Part 3` 输出：

- 推荐进入建议
- 最优供应与 Incoterm 路径
- 净利率区间
- 风险等级

## 当前状态

- 已有策略稿
- 已有量化结构
- 已有 RFQ 清洗器
- 已有蒙特卡洛模拟
- 已有报告、图表、回测 demo

## source references

- [Part3-China-Supply-Chain-Export-Strategy.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-China-Supply-Chain-Export-Strategy.md)
- [Part3-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Structure.md)
- [Part3-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Quantitative-Optimization-Plan.md)
- [Part3-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part3-Deep-Optimization-Crosswalk.md)
- [Part3-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Part3-README.md)
