# 第一部分量化结构设计（草稿）

## 一、量化部分要解决什么问题

第一部分的量化难点不在于“有没有数据”，而在于不同平台、不同口径、不同商品类目之间的数据无法直接横向比较。  
要解决这个问题，必须先做三件事：

1. 把外部数据统一映射成固定表结构。
2. 把每个章节要输出的指标定义成固定公式。
3. 把指标计算结果组织成统一的章节输出格式。

所以量化部分的核心思路不是先写图表，而是先建立：

- 标准数据表
- 标准指标库
- 标准章节输出结构
- 标准代码入口

---

## 二、建议采用的量化架构

建议第一部分按四层结构搭建：

### 2.1 数据源层

原始数据来自不同平台与工具，包括：

- Google Trends
- Amazon 类工具
- eBay 成交数据
- TikTok Shop 数据工具
- SimilarWeb / Ahrefs / SEMrush
- 评论文本与社媒数据
- 行业报告与宏观市场数据

### 2.2 标准化表层

无论数据来自哪里，进入系统后都应先转成以下标准表：

- `search_trends`
- `region_demand`
- `customer_segments`
- `listings`
- `transactions`
- `channels`

这一步的目的，是让后续所有品类都使用同一套字段和同一套计算函数。

在本轮细化后，第一部分不再只吃“基础六张表”，而是升级为：

- 基础观测表：`search_trends / region_demand / customer_segments / listings / transactions / channels`
- 参考治理表：`market_size_inputs / channel_benchmarks / event_library / source_registry / part1_threshold_registry`

前者回答“市场发生了什么”，后者回答“这些结论是否有外部基准和可审计参考”。

### 2.3 指标引擎层

指标引擎负责把标准表计算成固定的量化结论。  
第一部分建议优先固化以下指标组：

- 需求趋势指标
- 季节性指标
- 区域需求指标
- 客户分布指标
- 市场规模指标
- 渠道效率指标
- 货架价格指标
- 实际成交价格指标

### 2.4 章节输出层

所有量化结果最终统一输出到第一部分六个章节中：

- `1.1 市场现状与需求概览`
- `1.2 客户画像分析`
- `1.3 市场规模分析`
- `1.4 购买渠道分析`
- `1.5 货架商品价格分析`
- `1.6 实际成交价格分析`

---

## 三、第一部分标准表结构

### 3.1 `search_trends`

用途：计算需求趋势、增长率、季节性指数。

建议字段：

- `month`
- `keyword`
- `interest`

### 3.2 `region_demand`

用途：计算重点区域需求占比。

建议字段：

- `region`
- `demand_score`

### 3.3 `customer_segments`

用途：统一表达客户年龄、性别、收入、场景、决策因素等分布。

建议字段：

- `dimension`
- `value`
- `count`

### 3.4 `listings`

用途：计算市场规模、价格带、品牌溢价、市场集中度。

建议字段：

- `sku_id`
- `platform`
- `brand`
- `list_price`
- `monthly_sales_estimate`
- `rating`
- `review_count`

### 3.5 `transactions`

用途：计算真实成交价、折扣率、价格弹性。

建议字段：

- `sku_id`
- `platform`
- `date`
- `list_price`
- `actual_price`
- `units`

### 3.6 `channels`

用途：计算渠道收入占比、转化率、客单价、ROAS。

建议字段：

- `channel`
- `visits`
- `orders`
- `revenue`
- `ad_spend`

### 3.7 `market_size_inputs`

用途：把 TAM / SAM / SOM 的 Top-Down 估算从单点假设升级成可审计参考面板。

建议字段：

- `market_segment`
- `tam`
- `sam`
- `som`
- `ecommerce_penetration`
- `importable_share`
- `cagr`
- `source`
- `confidence_grade`

### 3.8 `channel_benchmarks`

用途：把渠道判断从“绝对值”升级成“相对行业基准”。

建议字段：

- `channel`
- `benchmark_conversion_rate`
- `benchmark_average_order_value`
- `benchmark_roas`
- `benchmark_cac`

---

## 四、第一部分章节与指标映射

### 4.1 `1.1 市场现状与需求概览`

核心指标：

- 需求增长率
- CAGR
- 波动率
- 市场热度波动系数
- 季节性指数
- 旺季/淡季月份
- 区域需求占比
- 需求热度与销量滞后关系

主要输入表：

- `search_trends`
- `region_demand`

### 4.2 `1.2 客户画像分析`

核心指标：

- 年龄分布
- 性别分布
- 收入分布
- 使用场景分布
- 决策因素分布

主要输入表：

- `customer_segments`

### 4.3 `1.3 市场规模分析`

核心指标：

- TAM
- SAM
- SOM
- 市场规模参考面板一致性
- 假设值与参考面板偏差
- 样本月 GMV
- 推算年度市场规模
- 品牌收入份额
- HHI

主要输入表：

- `listings`
- `market_size_inputs`

额外假设参数：

- `tam`
- `online_penetration`
- `importable_share`
- `target_capture_share`
- `sample_coverage`

### 4.4 `1.4 购买渠道分析`

核心指标：

- 渠道收入占比
- 转化率
- 平均客单价
- ROAS
- 渠道基准偏差
- 基准覆盖率
- 高于基准渠道占比

主要输入表：

- `channels`
- `channel_benchmarks`

### 4.5 `1.5 货架商品价格分析`

核心指标：

- 最低价
- 最高价
- 平均价
- 中位数价格
- 价格带占比
- 品牌溢价系数

主要输入表：

- `listings`

### 4.6 `1.6 实际成交价格分析`

核心指标：

- 平均挂牌价
- 平均成交价
- 平均折扣率
- 成交价带占比
- 平均价格弹性

主要输入表：

- `transactions`

---

## 五、量化代码的组织方式

目前已经按以下结构落代码：

- [quant_framework/models.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/models.py)
- [quant_framework/registry.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/registry.py)
- [quant_framework/loaders.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/loaders.py)
- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py)
- [quant_framework/part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py)
- [quant_framework/validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)
- [quant_framework/pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/pipeline.py)
- [quant_framework/cli.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/cli.py)
- [quant_framework/uncertainty.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/uncertainty.py)
- [quant_framework/backtest.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/backtest.py)
- [tests/test_pipeline.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/tests/test_pipeline.py)

职责划分如下：

### 5.1 `models.py`

定义第一部分所需的标准数据模型。  
作用是把未来不同来源的数据先统一成同一套字段结构。

### 5.2 `registry.py`

定义指标注册表。  
这里不直接做计算，而是固定每个指标属于哪个章节、依赖什么表、公式是什么、输出说明是什么。

### 5.3 `loaders.py`

负责从 CSV 读取标准化数据。  
后续如果接入 API 或数据库，也建议仍然先转为相同的数据模型。

### 5.4 `metrics.py`

负责核心量化计算。  
目前已经实现：

- 需求趋势计算
- 3 个月移动平均趋势
- 季节性指数
- 市场热度波动系数
- 搜索热度与成交量领先滞后扫描
- 客户分布
- 市场规模 Top-Down / Bottom-Up
- 市场规模参考面板一致性
- HHI
- 市场规模双口径 triangulation gap
- 渠道效率
- 渠道基准 gap
- IQR 异常值识别
- 分位数价格带
- 品牌溢价
- 成交价、折扣率与价格实现率
- 使用 midpoint method 的价格弹性

### 5.5 `part1.py`

负责把所有指标按第一部分的六个章节拼装成统一的输出结果。  
后续无论输出到 Markdown、Excel、BI 看板还是可视化图表，都应该优先消费这一层的结果。

### 5.6 `validation.py`

负责把当前量化方法与公开方法论做对照验证。  
目前已经覆盖：

- Google Trends 相对指数口径检查
- DOJ/FTC HHI 阈值检查
- Google Ads 转化率与 ROAS 公式检查
- NIST IQR 异常值方法检查
- OpenStax midpoint elasticity 方法检查
- Top-Down 与 Bottom-Up 市场规模差异检查

### 5.7 `pipeline.py`

负责把标准目录结构中的 CSV 文件装配成 `Part1Dataset`，并维护默认假设参数。  
这样示例脚本、CLI 和测试都不用重复写一套加载逻辑。

### 5.8 `cli.py`

提供统一命令行入口，当前支持：

- `report`
- `charts`
- `clean`

这意味着以后你不需要分别找示例脚本，可以直接通过 CLI 跑报告、出图和清洗原始导出表。

### 5.9 `tests/test_pipeline.py`

提供最基础的回归测试，覆盖：

- 报告生成
- 图表生成
- 原始平台表清洗
- CLI 入口

### 5.10 `uncertainty.py`

负责对关键指标做 bootstrap 置信区间估计。  
当前已经给第一部分补上：

- 底层市场规模区间
- 标价中位数区间
- 平均成交价区间
- 平均折扣率区间
- 平均价格弹性区间

### 5.11 `backtest.py`

负责“市场机会信号”的滚动回测。  
当前提供：

- 类别面板 demo 数据生成
- 机会信号回测
- 策略曲线 SVG 输出
- 回测结果 JSON 输出

---

## 六、当前代码如何使用

目前已提供一套最小示例数据与运行入口：

- [examples/search_trends.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/search_trends.csv)
- [examples/region_demand.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/region_demand.csv)
- [examples/customer_segments.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/customer_segments.csv)
- [examples/listings.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/listings.csv)
- [examples/transactions.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/transactions.csv)
- [examples/channels.csv](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/channels.csv)
- [examples/run_part1_demo.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/examples/run_part1_demo.py)

运行方式：

```bash
python3 examples/run_part1_demo.py
```

运行结果会输出一份标准 JSON 结构，用于后续生成报告正文、图表或仪表盘。

现在也可以直接通过 CLI 运行：

```bash
python3 -m quant_framework.cli report --data-dir examples --output-json /tmp/part1_report.json
python3 -m quant_framework.cli charts --data-dir examples --output-dir /tmp/part1_charts
python3 -m quant_framework.cli clean --platform amazon --input-csv examples/raw_amazon_listing_export.csv --output-csv /tmp/amazon_listings.csv
python3 -m quant_framework.cli backtest-demo --output-dir /tmp/backtest_demo
```

测试运行方式：

```bash
python3 -m unittest discover -s tests -v
```

---

## 七、下一步应该怎么继续

当前这套代码已经能解决“第一部分怎么量化”和“不同品类如何统一口径”的基础问题，但还只是第一版骨架。  
下一步最值得继续补的是三项：

1. 为每个章节补充图表生成代码。
2. 为不同平台设计原始数据到标准表的映射脚本。
3. 增加结论模板，把 JSON 指标自动转成研究报告段落。

如果继续往下做，最合理的顺序是：

1. 先把 `1.1` 到 `1.6` 的图表代码补齐。
2. 再为 Amazon、eBay、TikTok Shop 设计原始抓取数据清洗模板。
3. 最后做报告自动生成功能。
