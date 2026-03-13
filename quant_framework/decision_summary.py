from __future__ import annotations

from .stats_utils import clip, score_level


def _clamp01(value: float) -> float:
    return clip(value, 0.0, 1.0)


def _score_row(score: float) -> dict[str, float | str]:
    normalized = round(_clamp01(score), 4)
    return {
        "score": normalized,
        "level": score_level(normalized),
    }


def _format_pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def build_part1_decision_summary(section_metrics: dict[str, dict]) -> dict:
    demand = section_metrics.get("1.1", {})
    market = section_metrics.get("1.3", {})
    channels = section_metrics.get("1.4", {})
    pricing = section_metrics.get("1.5", {})
    transactions = section_metrics.get("1.6", {})

    trend = demand.get("trend", {})
    bottom_up = market.get("bottom_up", {})
    triangulation = market.get("triangulation", {})
    totals = channels.get("totals", {})
    channel_rows = channels.get("channels", [])

    growth_rate = trend.get("growth_rate", 0.0)
    cagr = trend.get("cagr", 0.0)
    volatility = trend.get("volatility", 0.0)
    hhi = bottom_up.get("hhi", 0.0)
    gap_ratio = triangulation.get("top_down_vs_bottom_up_gap_ratio", 1.0)
    price_realization = transactions.get("price_realization_rate", 0.0)
    average_discount = transactions.get("average_discount_rate", 0.0)
    strongest_brand_premium = max(pricing.get("brand_premium", {}).values(), default=0.0)
    overall_roas = totals.get("overall_roas") or 0.0
    overall_conversion = totals.get("overall_conversion_rate", 0.0)

    demand_strength = (
        _clamp01((growth_rate + 0.05) / 0.2) * 0.45
        + _clamp01((cagr + 0.02) / 0.18) * 0.35
        + _clamp01(1 - volatility / 0.25) * 0.2
    )
    market_accessibility = (
        _clamp01(1 - max(hhi - 1000, 0) / 2600) * 0.6
        + _clamp01(1 - gap_ratio / 0.15) * 0.4
    )
    channel_efficiency = (
        _clamp01(overall_conversion / 0.1) * 0.55
        + _clamp01(overall_roas / 8.0) * 0.45
    )
    pricing_power = (
        _clamp01((price_realization - 0.8) / 0.18) * 0.55
        + _clamp01((strongest_brand_premium + 0.1) / 0.8) * 0.45
    )
    decision_score = round(
        demand_strength * 0.35
        + market_accessibility * 0.25
        + channel_efficiency * 0.2
        + pricing_power * 0.2,
        4,
    )

    if decision_score >= 0.68:
        decision_signal = "attractive"
        recommended_next_step = "进入 Part 2，继续做 SKU 结构、价格甜蜜带和白空间扫描。"
    elif decision_score >= 0.5:
        decision_signal = "watchlist"
        recommended_next_step = "补充更多平台和区域样本，再进入 Part 2。"
    else:
        decision_signal = "caution"
        recommended_next_step = "先复核需求趋势和渠道样本，再决定是否继续推进。"

    top_channel = channel_rows[0]["channel"] if channel_rows else ""
    concentration_level = bottom_up.get("concentration_level", "")
    top_region = next(iter(demand.get("top_regions", {}).keys()), "")
    key_findings = [
        f"需求端当前 CAGR 为 {_format_pct(cagr)}，重点区域集中在 {top_region or '头部州市场'}。",
        f"市场年化规模约 {bottom_up.get('estimated_annual_market_size', 0.0):,.0f} USD，集中度为 {concentration_level}。",
        f"当前主成交渠道为 {top_channel or '未知'}，平均实际成交价为 {transactions.get('average_actual_price', 0.0):.2f} USD。",
    ]

    risk_flags = []
    if hhi >= 1800:
        risk_flags.append("市场集中度较高，头部品牌挤压明显。")
    if gap_ratio > 0.1:
        risk_flags.append("市场规模双口径偏差较大，需要补样本校准。")
    if overall_roas and overall_roas < 4:
        risk_flags.append("渠道广告回报偏弱，冷启动成本可能偏高。")
    if price_realization < 0.85 or average_discount > 0.15:
        risk_flags.append("真实成交价折让偏深，挂牌价并不等于可成交价格。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "demand_strength": _score_row(demand_strength),
            "market_accessibility": _score_row(market_accessibility),
            "channel_efficiency": _score_row(channel_efficiency),
            "pricing_power": _score_row(pricing_power),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }


def build_part2_decision_summary(section_metrics: dict[str, dict]) -> dict:
    market_structure = section_metrics.get("2.1", {})
    price = section_metrics.get("2.2", {})
    attributes = section_metrics.get("2.4", {})
    reviews = section_metrics.get("2.5", {})
    shelf = section_metrics.get("2.6", {})

    top_sku_share = market_structure.get("top_sku_share", 1.0)
    long_tail_share = market_structure.get("long_tail_share", 0.0)
    brand_hhi = market_structure.get("brand_hhi", 0.0)
    sweet_spot_share = price.get("sweet_spot_band", {}).get("share", 0.0)
    price_realization = price.get("price_realization_rate", 0.0)
    discount_rate = price.get("discount_depth", {}).get("weighted_average_discount_rate", 0.0)
    whitespace = attributes.get("whitespace_opportunities", [])
    top_whitespace = max(
        [row.get("adjusted_outperformance", 0.0) for row in whitespace],
        default=0.0,
    )
    negative_rate = reviews.get("sentiment_mix", {}).get("negative", 0.0)
    active_rate = shelf.get("active_rate", 0.0)
    median_lifetime_days = shelf.get("median_lifetime_days", 0.0)

    structure_headroom = (
        _clamp01(long_tail_share / 0.5) * 0.45
        + _clamp01((1 - top_sku_share) / 0.5) * 0.3
        + _clamp01(1 - max(brand_hhi - 1000, 0) / 3000) * 0.25
    )
    pricing_fit = (
        _clamp01(sweet_spot_share / 0.35) * 0.4
        + _clamp01(price_realization / 0.95) * 0.35
        + _clamp01(1 - discount_rate / 0.18) * 0.25
    )
    whitespace_depth = (
        _clamp01(len(whitespace) / 3) * 0.5
        + _clamp01(top_whitespace / 0.2) * 0.5
    )
    shelf_stability = (
        _clamp01(median_lifetime_days / 90) * 0.4
        + _clamp01(active_rate) * 0.3
        + _clamp01(1 - negative_rate / 0.4) * 0.3
    )
    decision_score = round(
        structure_headroom * 0.25
        + pricing_fit * 0.25
        + whitespace_depth * 0.25
        + shelf_stability * 0.25,
        4,
    )

    if decision_score >= 0.65:
        decision_signal = "promising"
        recommended_next_step = "进入 Part 3，围绕甜蜜带和白空间属性做 RFQ 与 landed cost 验证。"
    elif decision_score >= 0.48:
        decision_signal = "selective"
        recommended_next_step = "只围绕高表现属性和主甜蜜带做定向 RFQ，避免全面铺货。"
    else:
        decision_signal = "crowded"
        recommended_next_step = "先收窄价格带或属性范围，再决定是否进入 Part 3。"

    top_whitespace_attribute = whitespace[0]["attribute"] if whitespace else ""
    key_findings = [
        f"当前总 GMV 为 {market_structure.get('total_gmv', 0.0):,.0f} USD，Top SKU 份额为 {_format_pct(top_sku_share)}。",
        f"主成交甜蜜带位于 {price.get('sweet_spot_band', {}).get('label', '未知区间')}，价格实现率约 {_format_pct(price_realization)}。",
        f"当前最强白空间属性为 {top_whitespace_attribute or '未识别'}，货架中位生存期为 {median_lifetime_days:.0f} 天。",
    ]

    risk_flags = []
    if top_sku_share > 0.7:
        risk_flags.append("成交过度集中在少数 SKU，上新后进入头部难度较高。")
    if negative_rate > 0.35:
        risk_flags.append("负评占比较高，质量或履约痛点可能拖累新品转化。")
    if median_lifetime_days < 45:
        risk_flags.append("货架稳定性偏弱，长尾 SKU 容易快速退出。")
    if not whitespace:
        risk_flags.append("未识别出明显白空间属性，差异化切入点不足。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "structure_headroom": _score_row(structure_headroom),
            "pricing_fit": _score_row(pricing_fit),
            "whitespace_depth": _score_row(whitespace_depth),
            "shelf_stability": _score_row(shelf_stability),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }


def build_part3_decision_summary(section_metrics: dict[str, dict]) -> dict:
    supply = section_metrics.get("3.1", {})
    quotes = section_metrics.get("3.2", {})
    compliance = section_metrics.get("3.3", {})
    logistics = section_metrics.get("3.4", {})
    margin = section_metrics.get("3.5", {})
    risk = section_metrics.get("3.6", {})
    entry = section_metrics.get("3.7", {})

    supply_readiness = (
        supply.get("supply_maturity_score", 0.0) * 0.65
        + supply.get("sample_confidence_score", 0.0) * 0.35
    )
    quote_quality = quotes.get("quote_quality", {})
    sampled_coverage = quotes.get("sampled_supplier_coverage", {})
    if isinstance(sampled_coverage, dict):
        sampled_coverage_ratio = sampled_coverage.get("coverage_ratio", 0.0)
    else:
        sampled_coverage_ratio = float(sampled_coverage or 0.0)
    quote_reliability = (
        quote_quality.get("average_quote_confidence", 0.0) * 0.55
        + sampled_coverage_ratio * 0.2
        + quote_quality.get("fresh_quote_share", 0.0) * 0.15
        + quote_quality.get("included_items_coverage", 0.0) * 0.1
    )
    mandatory_days = compliance.get("mandatory_estimated_days", 0.0)
    mandatory_cost_per_unit = compliance.get("mandatory_cost_per_unit", 0.0)
    compliance_readiness = (
        _clamp01(1 - compliance.get("high_risk_mandatory_share", 0.0)) * 0.45
        + _clamp01(1 - mandatory_days / 90) * 0.35
        + _clamp01(1 - mandatory_cost_per_unit / 60) * 0.2
    )
    best_scenario = margin.get("best_scenario", {})
    monte_carlo = margin.get("monte_carlo", {})
    margin_safety = (
        _clamp01(best_scenario.get("net_margin_rate", 0.0) / 0.25) * 0.45
        + _clamp01(1 - monte_carlo.get("loss_probability", 0.0) / 0.25) * 0.35
        + _clamp01(1 - risk.get("overall_risk_score", 1.0)) * 0.2
    )
    decision_score = round(
        supply_readiness * 0.25
        + quote_reliability * 0.25
        + compliance_readiness * 0.2
        + margin_safety * 0.3,
        4,
    )

    recommendation = entry.get("recommendation", "")
    if recommendation == "recommended_entry":
        decision_signal = "high_priority"
        recommended_next_step = "进入打样与首单执行阶段，锁定供应商和路径。"
    elif recommendation == "pilot_first":
        decision_signal = "pilot_candidate"
        recommended_next_step = "先做小批量试单，优先验证物流与费用透明度。"
    else:
        decision_signal = "hold"
        recommended_next_step = "暂停推进，优先补齐报价透明度、合规或利润安全边际。"

    key_findings = [
        f"供应链成熟度为 {supply.get('supply_maturity_level', 'unknown')}，样本置信度为 {_format_pct(supply.get('sample_confidence_score', 0.0))}。",
        f"最佳情景下到岸成本为 {best_scenario.get('landed_cost', 0.0):.2f} USD，净利率为 {_format_pct(best_scenario.get('net_margin_rate', 0.0))}。",
        f"总体风险等级为 {risk.get('overall_risk_level', 'unknown')}，当前进入建议为 {recommendation or 'unknown'}。",
    ]

    risk_flags = []
    if compliance.get("high_risk_mandatory_share", 0.0) > 0.3:
        risk_flags.append("强制合规项中的高风险占比较高，准入门槛不可低估。")
    if logistics.get("delay_rate", 0.0) > 0.2:
        risk_flags.append("历史物流延迟偏高，补货稳定性仍需验证。")
    if best_scenario.get("scenario_confidence_score", 0.0) < 0.7:
        risk_flags.append("最佳情景的数据置信度偏低，报价或费用边界仍需补强。")
    if best_scenario.get("assumption_flags"):
        risk_flags.append("关键成本情景仍依赖假设项，需在试单阶段优先去假设化。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "supply_readiness": _score_row(supply_readiness),
            "quote_reliability": _score_row(quote_reliability),
            "compliance_readiness": _score_row(compliance_readiness),
            "margin_safety": _score_row(margin_safety),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }
