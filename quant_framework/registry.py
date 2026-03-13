from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    section_id: str
    metric_id: str
    label: str
    required_tables: tuple[str, ...]
    formula: str
    output_note: str


PART1_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        section_id="1.1",
        metric_id="demand_growth_rate",
        label="需求增长率",
        required_tables=("search_trends",),
        formula="(末期兴趣值 - 初期兴趣值) / 初期兴趣值",
        output_note="用于判断需求增长、平稳或下滑。",
    ),
    MetricSpec(
        section_id="1.1",
        metric_id="seasonality_index",
        label="季节性指数",
        required_tables=("search_trends",),
        formula="月均兴趣值 / 全期均值 * 100",
        output_note="高于 120 视为旺季，低于 80 视为淡季。",
    ),
    MetricSpec(
        section_id="1.1",
        metric_id="regional_demand_share",
        label="区域需求占比",
        required_tables=("region_demand",),
        formula="区域需求分值 / 全区域需求分值合计",
        output_note="用于找出重点州、省或区域。",
    ),
    MetricSpec(
        section_id="1.2",
        metric_id="customer_distribution",
        label="客户分布",
        required_tables=("customer_segments",),
        formula="各维度 count / 该维度总 count",
        output_note="统一支持年龄、性别、收入、场景、决策因素等维度。",
    ),
    MetricSpec(
        section_id="1.3",
        metric_id="bottom_up_market_size",
        label="自下而上市场规模",
        required_tables=("listings",),
        formula="样本月 GMV / 样本覆盖率 * 12",
        output_note="用于估算平台口径的年度市场规模。",
    ),
    MetricSpec(
        section_id="1.3",
        metric_id="top_down_market_size",
        label="自上而下市场规模",
        required_tables=(),
        formula="SAM = TAM * 线上渗透率 * 可服务比例；SOM = SAM * 目标份额",
        output_note="用于形成 TAM、SAM、SOM 三层估算。",
    ),
    MetricSpec(
        section_id="1.3",
        metric_id="market_hhi",
        label="市场集中度 HHI",
        required_tables=("listings",),
        formula="sum(品牌收入份额^2) * 10000",
        output_note="用于判断市场分散度和进入难度。",
    ),
    MetricSpec(
        section_id="1.4",
        metric_id="channel_share",
        label="渠道收入占比",
        required_tables=("channels",),
        formula="单渠道收入 / 全渠道收入",
        output_note="用于识别成交主渠道。",
    ),
    MetricSpec(
        section_id="1.4",
        metric_id="channel_conversion_rate",
        label="渠道转化率",
        required_tables=("channels",),
        formula="订单数 / 访问量",
        output_note="用于比较平台成交效率。",
    ),
    MetricSpec(
        section_id="1.5",
        metric_id="listed_price_bands",
        label="货架价格带分布",
        required_tables=("listings",),
        formula="按价格分布四分位数划分价格带，并结合 IQR 异常值处理统计 SKU 占比",
        output_note="用于识别红海价格带与潜在空白带。",
    ),
    MetricSpec(
        section_id="1.5",
        metric_id="brand_premium",
        label="品牌溢价系数",
        required_tables=("listings",),
        formula="品牌价格中位数 / 类目价格中位数 - 1",
        output_note="用于判断品牌溢价能力。",
    ),
    MetricSpec(
        section_id="1.6",
        metric_id="average_transaction_price",
        label="平均实际成交价",
        required_tables=("transactions",),
        formula="sum(成交价 * 销量) / sum(销量)",
        output_note="用于识别真实支付区间。",
    ),
    MetricSpec(
        section_id="1.6",
        metric_id="average_discount_rate",
        label="平均折扣率",
        required_tables=("transactions",),
        formula="sum((挂牌价-成交价) / 挂牌价 * 销量) / sum(销量)",
        output_note="用于判断市场折扣深度。",
    ),
    MetricSpec(
        section_id="1.6",
        metric_id="price_elasticity",
        label="价格弹性系数",
        required_tables=("transactions",),
        formula="使用 midpoint method: |销量变化率 / 价格变化率|",
        output_note="用于判断品类是否适合以促销驱动销量。",
    ),
)


PART2_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        section_id="2.1",
        metric_id="sku_gmv_leaderboard",
        label="平台 Top SKU / 品牌成交结构",
        required_tables=("listing_snapshots", "sold_transactions"),
        formula="GMV = sum((成交价 + 运费) * 销量)，并计算 Top SKU/Top Brand 份额与集中度",
        output_note="用于识别哪个 SKU、品牌、平台真正拿走成交。",
    ),
    MetricSpec(
        section_id="2.2",
        metric_id="realized_price_distribution",
        label="实际成交价格分布与甜蜜带",
        required_tables=("listing_snapshots", "sold_transactions"),
        formula="对 realized price = 成交价 + 运费 计算分位数，并以销量加权价格带识别 sweet spot",
        output_note="用于识别最容易成交的价格带和折扣深度。",
    ),
    MetricSpec(
        section_id="2.3",
        metric_id="price_rating_matrix",
        label="价格-评分价值矩阵",
        required_tables=("listing_snapshots", "sold_transactions"),
        formula="将 SKU 映射到价格四分位 × 评分桶，比较 SKU 密度与销量占比",
        output_note="用于识别高价值集群和高风险定价集群。",
    ),
    MetricSpec(
        section_id="2.4",
        metric_id="attribute_outperformance",
        label="属性画像与白空间机会",
        required_tables=("product_catalog", "sold_transactions"),
        formula="属性 outperformance = 属性 GMV 占比 - 属性 SKU 占比",
        output_note="用于识别供给相对少但成交贡献更高的属性组合。",
    ),
    MetricSpec(
        section_id="2.5",
        metric_id="review_sentiment_topics",
        label="评论情绪与负面主题强度",
        required_tables=("reviews",),
        formula="规则情绪分类 + 主题词典统计，pain_point_intensity = 负面主题提及率 × 负面情绪权重",
        output_note="用于量化痛点而不是只看星级均值。",
    ),
    MetricSpec(
        section_id="2.6",
        metric_id="listing_survival_dynamics",
        label="货架动态与生存分析",
        required_tables=("listing_snapshots",),
        formula="基于首末观察时间与退出事件构造 survival curve，并计算 entry/exit velocity",
        output_note="用于衡量 SKU 是否稳定留在货架上。",
    ),
)


PART3_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        section_id="3.1",
        metric_id="supply_structure",
        label="供应端成熟度与结构",
        required_tables=("suppliers",),
        formula="统计供应商数量、类型占比、产业带占比、MOQ、打样周期、量产周期与能力评分。",
        output_note="用于判断该品类在中国是否属于成熟供应链品类。",
    ),
    MetricSpec(
        section_id="3.2",
        metric_id="rfq_quote_structure",
        label="RFQ 报价结构与 MOQ 曲线",
        required_tables=("rfq_quotes", "suppliers"),
        formula="quoted_unit_cost = 单价 + 包装 + 定制 + 样品费/MOQ + 模具费/MOQ；再按 Incoterm 与 MOQ 分组统计。",
        output_note="用于识别采购主流价带、条款差异与工厂/贸易商价差。",
    ),
    MetricSpec(
        section_id="3.3",
        metric_id="compliance_gating",
        label="合规门槛与认证成本",
        required_tables=("compliance_requirements",),
        formula="统计 mandatory 要求数量、关键路径天数、总成本与高风险项占比。",
        output_note="用于判断货能否顺利进入北美并完成平台上架。",
    ),
    MetricSpec(
        section_id="3.4",
        metric_id="logistics_route_efficiency",
        label="出口路径与物流效率",
        required_tables=("logistics_quotes", "shipment_events"),
        formula="基于 cost、lead_time、volatility 构建 route_score，并计算实际交期、准时率与清关延迟率。",
        output_note="用于识别试单期和稳定补货期的推荐路径。",
    ),
    MetricSpec(
        section_id="3.5",
        metric_id="landed_cost_margin",
        label="到岸成本与利润安全边际",
        required_tables=("rfq_quotes", "logistics_quotes", "tariff_tax", "compliance_requirements"),
        formula="sellable_cost = landed_cost + working_capital + return_reserve；net_margin = 售价 - 渠道费 - 营销费 - sellable_cost。",
        output_note="用于判断该品类是否具备中国供应链落地优势。",
    ),
    MetricSpec(
        section_id="3.6",
        metric_id="risk_matrix",
        label="风险矩阵与优先级",
        required_tables=("suppliers", "compliance_requirements", "logistics_quotes", "shipment_events"),
        formula="综合供应、合规、物流、关税和利润安全边际构造 severity_score。",
        output_note="用于形成高优先级风险和对应 mitigation 动作。",
    ),
    MetricSpec(
        section_id="3.7",
        metric_id="entry_strategy",
        label="推荐进入路径与首批执行方案",
        required_tables=("rfq_quotes", "logistics_quotes", "suppliers"),
        formula="基于最佳成本情景、风险分数与供应成熟度输出 recommendation 与 first batch plan。",
        output_note="用于形成首批试单和 90 天执行建议。",
    ),
)
