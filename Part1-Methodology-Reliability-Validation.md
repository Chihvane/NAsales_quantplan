# 第一部分量化方法可靠性对照与验证

更新时间：2026-03-11

## 一、验证目的

第一部分的量化代码不能只做到“能算”，还必须回答两个问题：

1. 这些指标是否符合公开可核验的方法论。
2. 这些指标是否存在明显的口径风险或误导风险。

因此本轮验证采用“代码实现 vs. 网上公开方法”逐项对照的方式，优先使用官方、学术或统计方法来源。

---

## 二、对照结论摘要

目前第一部分量化代码已完成的核心对照如下：

| 模块 | 我们的实现 | 对照来源 | 结论 |
|---|---|---|---|
| 需求趋势 | 使用 Google Trends 风格 0-100 相对指数，在同一时间窗内计算增长率、波动率与季节性 | Google Trends Help | 对齐 |
| 市场规模 | 同时保留 Top-Down 与 Bottom-Up，并计算 gap 做 triangulation | HolonIQ / Umbrex | 对齐 |
| 市场集中度 | HHI 阈值按最新 DOJ/FTC 标准分类 | DOJ / FTC | 对齐 |
| 渠道效率 | 转化率 = 订单 / 访问，ROAS = 收入 / 广告花费 | Google Ads Help | 对齐 |
| 价格分布 | 使用四分位数 + IQR/Tukey fences 识别异常值 | NIST | 对齐 |
| 价格弹性 | 使用 midpoint method 计算价格弹性 | OpenStax | 对齐 |

这意味着当前第一部分的核心量化口径，已经不是经验公式堆砌，而是尽量映射到了公开可核验的方法。

---

## 三、逐项对照说明

### 3.1 需求趋势与季节性

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L157)

当前实现：

- 输入 `search_trends`
- 聚合月度兴趣值
- 计算增长率、CAGR、波动率
- 计算月度季节性指数
- 补充 3 个月移动平均平滑趋势

对照来源：

- [Google Trends Help](https://support.google.com/trends/answer/4365533)

对照结论：

- Google Trends 的数值本质是相对指数，不是绝对搜索量。
- 数值基于同一查询窗口标准化到 `0-100`。
- 因此代码中只在同一时间窗、同一关键词组合下计算趋势与季节性，这是合理的。

可靠性说明：

- 这部分对“趋势方向”和“季节性模式”是可靠的。
- 这部分不能替代绝对搜索量估算。

---

### 3.2 市场规模估算

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L272)
- [quant_framework/part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py#L84)

当前实现：

- Top-Down：`TAM -> online_market -> SAM -> SOM`
- Bottom-Up：`样本月 GMV / 样本覆盖率 * 12`
- 增加 `top_down_vs_bottom_up_gap_ratio`

对照来源：

- [HolonIQ - Market Sizing 101](https://www.holoniq.com/notes/market-sizing-101)
- [Umbrex - Bottom-Up Analysis](https://umbrex.com/resources/market-sizing-playbook/how-to-estimate-market-size/how-to-estimate-market-size-using-bottom-up-analysis/)

对照结论：

- 网上主流市场规模策略并不建议只依赖单一路径。
- 当前代码同时保留 Top-Down 和 Bottom-Up，并显式计算差距，这符合更稳妥的 triangulation 思路。
- 参考 Umbrex 的建议，双口径差异过大时应回头复查，而不是直接采用单一结果。

可靠性说明：

- 双口径并行比单口径可靠。
- 但 Bottom-Up 依赖平台销量估算工具时，可靠性仍受第三方工具算法影响。

---

### 3.3 市场集中度 HHI

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L145)
- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L318)

当前实现：

- 以品牌收入份额计算 HHI
- 使用 `1000 / 1800` 作为分类阈值
- 输出 `unconcentrated / moderately_concentrated / highly_concentrated`

对照来源：

- [U.S. DOJ and FTC Merger Guidelines](https://www.justice.gov/atr/merger-guidelines)

对照结论：

- 这部分已从旧版常见的 `1500 / 2500` 阈值，修正为当前更合适的口径。
- 因此当前代码在“竞争分散度”判断上更接近最新公开标准。

可靠性说明：

- 只要品牌份额输入可信，HHI 计算本身可靠。
- 不可靠点不在公式，而在品牌份额样本是否覆盖足够完整。

---

### 3.4 渠道转化率与 ROAS

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L353)

当前实现：

- `conversion_rate = orders / visits`
- `roas = revenue / ad_spend`
- 同时输出 `traffic_share`、`order_share`、`average_order_value`、`cost_per_order`

对照来源：

- [Google Ads Help - About conversion tracking](https://support.google.com/google-ads/answer/1722022)
- [Google Ads Help - About target ROAS bidding](https://support.google.com/google-ads/answer/6268637)

对照结论：

- 公式口径与公开广告指标定义一致。
- 因此该部分适合做跨渠道效率对比。

可靠性说明：

- 若 `visits` 或 `ad_spend` 缺失，代码会输出 `null`，避免制造假精度。
- 这比强行写成 `0` 更可靠。

---

### 3.5 价格分布与异常值处理

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L65)
- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L395)
- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L445)

当前实现：

- 计算 `P10/Q1/Median/Q3/P90`
- 用 Tukey fences 识别 mild / extreme outliers
- 价格带基于四分位数而不是简单均价倍数

对照来源：

- [NIST/SEMATECH e-Handbook of Statistical Methods](https://www.itl.nist.gov/div898/handbook/prc/section1/prc16.htm)

对照结论：

- 对于价格这类容易右偏、长尾的数据，四分位数和 IQR 比均值倍数更稳健。
- 因此当前代码比旧版“均价乘系数”的价格带划分更可靠。

可靠性说明：

- 当样本很少时，四分位数仍然会受样本离散程度影响。
- 但整体上它比简单均价更不容易被高价 SKU 扭曲。

---

### 3.6 实际成交价格与价格弹性

当前实现位置：

- [quant_framework/metrics.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/metrics.py#L445)

当前实现：

- 平均挂牌价
- 平均实际成交价
- 平均折扣率
- 价格实现率
- 实际成交价格带
- 使用 `midpoint method` 计算价格弹性

对照来源：

- [OpenStax - Price Elasticity of Demand and Price Elasticity of Supply](https://openstax.org/books/principles-economics-3e/pages/5-1-price-elasticity-of-demand-and-price-elasticity-of-supply)

对照结论：

- 旧版代码使用“首尾点直接相除”，容易受到基期影响。
- 当前代码改成 midpoint method 后，更符合常见经济学教学与分析口径。

可靠性说明：

- 该方法适合比较相邻价格变动段。
- 但若销量变化同时受广告、库存、季节性影响，弹性结果仍需结合业务背景解释。

---

## 四、代码中的自动验证模块

自动验证入口：

- [quant_framework/validation.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/validation.py)

当前自动检查：

- Google Trends 相对指数范围检查
- 区域份额合计检查
- HHI 分类阈值检查
- Top-Down / Bottom-Up 差异检查
- 转化率公式检查
- ROAS 公式检查
- IQR 异常值方法检查
- midpoint elasticity 方法检查

报告输出位置：

- [quant_framework/part1.py](/Users/zhiwenxiang/Documents/Playground/北美市场量化报告/quant_framework/part1.py#L66)

也就是说，后续每次跑第一部分分析时，不只是输出指标，还会一并输出方法验证结果。

---

## 五、当前仍然存在的可靠性边界

下面这些问题，本轮已经标记，但无法仅靠代码彻底解决：

### 5.1 平台销量估算并非平台官方公开成交明细

例如 Amazon 类工具导出的 `monthly_sales_estimate` 往往基于排名模型推算。  
因此 Bottom-Up 市场规模的误差，主要取决于第三方数据工具的估算能力，而不是公式本身。

### 5.2 客户画像依赖样本来源质量

如果 `customer_segments` 来自评论抽样、问卷或社媒抓取，那么画像是否可靠，取决于抽样是否偏向某一平台或某类用户。

### 5.3 价格弹性不是纯因果结果

即使公式正确，价格下降后销量上升，也不一定完全由价格变化造成。  
广告投放、库存补货、促销曝光和季节性都可能共同影响成交数量。

---

## 六、结论

当前第一部分量化代码已经达到以下状态：

- 核心指标不再依赖纯经验写法，而是尽量对应公开方法论。
- 关键口径已加入自动验证，而不是只输出结果不解释方法。
- 相比旧版，价格、弹性、市场规模和集中度判断都更稳健。

但也要明确：

- 代码可靠，不代表原始数据天然可靠。
- 真正决定最终结论可信度的，仍然是原始样本质量、平台数据覆盖度和时间窗设定。

因此当前最合理的使用方式是：

1. 用这套代码保证分析口径统一。
2. 用自动验证模块筛出明显不可靠的结果。
3. 用真实平台导出表和访谈样本继续提升输入数据质量。

