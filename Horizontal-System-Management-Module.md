# 横向系统管理模块

横向系统管理模块不是新的市场章节，而是跨 `Part 0–5` 的控制塔。

它负责三类事情：

1. 统一数据字典与主数据口径
2. 统一证据链、审计链与版本追溯
3. 统一 Go / No-Go / Stop-Loss 规则库

## 模块定位

这套模块解决的不是“某个品类是否有机会”，而是：

- 同一套研究框架换品类、换人、换季度后，数据口径是否仍然稳定
- 任意结论能否在短时间内回溯到原始数据、脚本版本和审批人
- 决策门槛是否真正可执行，而不是只写在报告里

## 三个子模块

### H1 数据字典与主数据管理

覆盖对象：

- SKU / SPU / 品牌
- 渠道
- 供应商
- 地区
- 时间
- 价格与利润指标

按当前框架，最小必备主数据族至少包括：

- `sku`
- `channel`
- `calendar`
- `price_metric`
- `supplier`

输出重点：

- 字段定义
- 类型约束
- 枚举约束
- 审批版本
- 主数据健康评分

建议最少维护四类模板：

- `SKU 属性字段表`
- `渠道字段表`
- `时间维度表`
- `价格指标字段表`

### H2 证据链与审计链

覆盖对象：

- 数据来源
- 数据版本
- 处理步骤
- 脚本版本
- 审批引用
- 审计事件

输出重点：

- 血缘覆盖率
- 可复现实验率
- 30 分钟追溯 SLA
- 审计日志不可篡改覆盖

记录粒度建议固定为：

- 数据源
- 抓取日期
- 数据版本
- 加工步骤
- 脚本版本
- 审批引用
- 审计状态

### H3 决策门槛系统

覆盖对象：

- 市场进入
- 试点放大
- SKU 下线
- 渠道退出
- 投放中止

当前规则库按这 5 类核心情景建模：

- `market_entry`
- `pilot_scale`
- `sku_exit`
- `channel_exit`
- `ad_pause`

输出重点：

- 规则库覆盖率
- 止损规则占比
- 触发后闭环解决率
- 审批路由覆盖
- 决策控制评分

## 与 Part 0–5 的关系

- `Part 0` 提供治理原则和 Gate 哲学
- 横向模块把这些原则变成可执行的主数据、证据链和规则库
- `Part 1–5` 的量化章节继续做业务分析
- 横向模块负责判断这些分析是否具备统一口径、可审计性和执行闭环

## 本次与 DOCX 总稿的对齐

本模块已经与 [北美市场量化报告框架.docx](/Users/zhiwenxiang/Downloads/北美市场量化报告框架.docx) 对齐到同一颗粒度：

- `第一部分：数据字典与主数据管理` 对应 `H1`
- `第二部分：证据链与审计链` 对应 `H2`
- `第三部分：决策门槛系统` 对应 `H3`

差异上，当前代码版比 `docx` 多了一层可执行约束：

- 明确的标准输入表
- 可计算的治理评分
- 验证层
- CLI
- demo 数据与图表

## 当前代码入口

- [horizontal_system.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_system.py)
- [horizontal_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_metrics.py)
- [horizontal_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/horizontal_pipeline.py)

## 当前 demo

- 输入目录：[horizontal_system_demo](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/horizontal_system_demo)
- 输出目录：[output_horizontal_system](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/output_horizontal_system)
