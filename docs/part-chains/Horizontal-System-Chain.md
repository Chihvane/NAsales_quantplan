# Horizontal System Unified Chain

## 定位

横向系统不是新的业务章节，而是跨 `Part 0-5` 的控制塔。

## 核心问题

- 主数据口径是否统一
- 证据链是否完整
- 审计链是否可追溯
- 决策规则是否真正进入执行系统

## 统一链条

### 1. 数据字典与主数据

覆盖对象：

- `sku`
- `channel`
- `calendar`
- `price_metric`
- `supplier`

### 2. 证据链与审计链

覆盖：

- source
- dataset version
- transform steps
- script version
- approval ref
- audit events

### 3. 决策门槛系统

覆盖：

- market entry
- pilot scale
- sku exit
- channel exit
- ad pause

### 4. 代码层

- [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
- [horizontal_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_pipeline.py)

## 当前状态

- 已有治理结构稿
- 已有量化结构
- 已有 demo 报告与图表
- 已接入统一 contract

## source references

- [Horizontal-System-Management-Module.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Management-Module.md)
- [Horizontal-System-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-Quantitative-Structure.md)
- [Horizontal-System-DOCX-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Horizontal-System-DOCX-Crosswalk.md)
- [Horizontal-System-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Horizontal-System-README.md)
