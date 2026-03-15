# Part 2 Unified Chain

## 定位

`Part 2` 是商品竞争与成交 intelligence 层，负责把“市场机会”压缩成“什么商品画像值得切入”。

## 核心问题

- 现在卖得好的商品到底长什么样
- 什么价格带最容易成交
- 哪些属性存在白空间
- 哪些评论痛点会拖累商品表现

## 统一链条

### 1. 结构层

章节固定为：

- 在售商品与成交结构
- 成交价格带与折扣深度
- 价格-评分价值矩阵
- 属性画像与白空间机会
- 评论情绪与痛点主题
- 货架动态与生存分析

### 2. 数据层

标准输入：

- `listing_snapshots.csv`
- `sold_transactions.csv`
- `product_catalog.csv`
- `reviews.csv`

并支持 Amazon / eBay / TikTok 原始导出清洗到标准四表。

### 3. 代码层

- [part2.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2.py)
- [part2_metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_metrics.py)
- [part2_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part2_pipeline.py)

### 3.1 优化计划层

- [Part2-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Quantitative-Optimization-Plan.md)
- [Part2-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Deep-Optimization-Crosswalk.md)
- [part2_quant_plan.yaml](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/decision-os/config/part2_quant_plan.yaml)

### 4. 因子层

当前已实现因子已覆盖：

- `FAC-COMPETITION-HEADROOM`
- `FAC-PRICING-FIT`
- `FAC-WHITESPACE-DEPTH`
- `FAC-SHELF-STABILITY`

优化计划中的目标因子会扩到：

- `FAC-VALUE-ADVANTAGE`
- `FAC-VOC-RISK`

并继续补：

- 证据分层
- 概率化输出
- calibration / drift monitoring

### 5. 回测与桥接层

- 已有 Part 2 专用回测
- 已有 GitHub 开源样本实跑
- 已可桥接到 `Decision OS`

## 当前状态

- 已完成量化结构
- 已有清洗链
- 已有报告、图表、回测
- 已对齐统一 contract

## source references

- [Part2-Quantitative-Structure.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Quantitative-Structure.md)
- [Part2-Quantitative-Optimization-Plan.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Quantitative-Optimization-Plan.md)
- [Part2-Deep-Optimization-Crosswalk.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part2-Deep-Optimization-Crosswalk.md)
- [Part2-README.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/docs/part-readmes/Part2-README.md)
- [Part1-Part2-DecisionOS-Bridge.md](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/Part1-Part2-DecisionOS-Bridge.md)
