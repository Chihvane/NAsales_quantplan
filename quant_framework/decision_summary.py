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


def build_part0_decision_summary(section_metrics: dict[str, dict]) -> dict:
    tree = section_metrics.get("0.1", {})
    governance = section_metrics.get("0.2", {})
    assumptions = section_metrics.get("0.3", {})
    gates = section_metrics.get("0.4", {})
    approvals = section_metrics.get("0.5", {})
    updates = section_metrics.get("0.6", {})
    dictionary = section_metrics.get("0.7", {})
    localization = section_metrics.get("0.8", {})

    operating_system_readiness = (
        tree.get("decision_tree_score", 0.0) * 0.25
        + gates.get("gate_operability_score", 0.0) * 0.2
        + gates.get("strategic_gate_score", 0.0) * 0.05
        + approvals.get("signature_chain_score", 0.0) * 0.2
        + updates.get("refresh_policy_score", 0.0) * 0.15
        + dictionary.get("dictionary_reuse_score", 0.0) * 0.1
        + localization.get("localization_governance_score", 0.0) * 0.05
    )
    evidence_rigour = (
        governance.get("auditability_score", 0.0) * 0.55
        + assumptions.get("assumption_governance_score", 0.0) * 0.45
    )
    control_discipline = (
        gates.get("gate_operability_score", 0.0) * 0.3
        + gates.get("strategic_gate_score", 0.0) * 0.1
        + approvals.get("signature_chain_score", 0.0) * 0.35
        + updates.get("refresh_policy_score", 0.0) * 0.25
    )
    decision_score = round(
        operating_system_readiness * 0.4
        + evidence_rigour * 0.3
        + control_discipline * 0.3,
        4,
    )

    if decision_score >= 0.75:
        decision_signal = "ready_for_execution_system"
        recommended_next_step = "进入 Part 1–5 的统一治理接入阶段，把 Gate、证据链和主数据约束落到各章节。"
    elif decision_score >= 0.55:
        decision_signal = "governance_needs_hardening"
        recommended_next_step = "先补关键 Gate、签字链和更新失效规则，再作为经营控制系统对外使用。"
    else:
        decision_signal = "not_ready"
        recommended_next_step = "先完成 Part 0 主数据、责任链和证据链，不建议直接把 Part 1–5 当经营系统使用。"

    key_findings = [
        f"当前决策树覆盖率为 {_format_pct(tree.get('gate_coverage_ratio', 0.0))}，决策操作系统分为 {_format_pct(operating_system_readiness)}。",
        f"数据治理审计分为 {_format_pct(governance.get('auditability_score', 0.0))}，假设治理分为 {_format_pct(assumptions.get('assumption_governance_score', 0.0))}。",
        f"Gate 可执行性为 {_format_pct(gates.get('gate_operability_score', 0.0))}，战略 Gate 覆盖为 {_format_pct(gates.get('strategic_metric_family_coverage_ratio', 0.0))}。",
        f"本地化治理分为 {_format_pct(localization.get('localization_governance_score', 0.0))}，当前已覆盖 {localization.get('active_market_count', 0)} 个可进入市场。",
    ]

    risk_flags = []
    if tree.get("gate_coverage_ratio", 0.0) < 1.0:
        risk_flags.append("Gate1–5 尚未完全覆盖，后续章节难以统一 Go / Hold / Kill。")
    if governance.get("confidence_mix", {}).get("A", 0.0) < 0.3:
        risk_flags.append("A级证据占比偏低，关键结论仍可能依赖估算或外推。")
    if assumptions.get("overdue_assumption_count", 0) > 0:
        risk_flags.append("存在逾期未验证假设，策略前提仍在漂移。")
    if gates.get("strategic_metric_family_coverage_ratio", 0.0) < 1.0:
        risk_flags.append("ROIC/HHI/热度稳定/回本/风险五类战略 Gate 尚未完全覆盖。")
    if approvals.get("minimum_step_pass_ratio", 0.0) < 1.0:
        risk_flags.append("并非所有 Gate 都具备完整签字链，问责与否决权定义还不够硬。")
    if updates.get("refresh_expiry_alignment_ratio", 0.0) < 0.8:
        risk_flags.append("更新周期与失效窗口未充分对齐，存在过期结论继续流转的风险。")
    if localization.get("weight_profile_coverage_ratio", 0.0) < 1.0:
        risk_flags.append("并非所有目标市场都具备独立权重 profile，仍存在跨区域模型混用风险。")
    if localization.get("consumer_habit_distance_score", 0.0) < 0.2:
        risk_flags.append("市场间消费习惯向量分离度偏低，需检查是否错误复用了同一消费模型。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "operating_system_readiness": _score_row(operating_system_readiness),
            "evidence_rigour": _score_row(evidence_rigour),
            "control_discipline": _score_row(control_discipline),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }


def build_horizontal_system_decision_summary(section_metrics: dict[str, dict]) -> dict:
    master_data = section_metrics.get("H1", {})
    audit = section_metrics.get("H2", {})
    gates = section_metrics.get("H3", {})

    data_governance = (
        master_data.get("master_data_health_score", 0.0) * 0.7
        + master_data.get("dictionary_approval_ratio", 0.0) * 0.3
    )
    audit_rigour = (
        audit.get("audit_trace_score", 0.0) * 0.7
        + audit.get("traceback_sla_ratio", 0.0) * 0.3
    )
    gate_discipline = (
        gates.get("decision_gate_control_score", 0.0) * 0.65
        + gates.get("trigger_resolution_ratio", 0.0) * 0.2
        + gates.get("stop_loss_rule_ratio", 0.0) * 0.15
    )

    decision_score = round(
        data_governance * 0.34
        + audit_rigour * 0.33
        + gate_discipline * 0.33,
        4,
    )

    if decision_score >= 0.78:
        decision_signal = "control_tower_ready"
        recommended_next_step = "把横向模块接入 Part 0–5 的字段校验、证据索引和 Gate 结果回填。"
    elif decision_score >= 0.58:
        decision_signal = "control_tower_needs_hardening"
        recommended_next_step = "先补主数据审批、证据链 SLA 或触发闭环，再作为统一控制塔使用。"
    else:
        decision_signal = "control_tower_not_ready"
        recommended_next_step = "暂不建议将横向模块作为经营总控层，先补齐审计链和规则闭环。"

    key_findings = [
        f"主数据健康分为 {_format_pct(master_data.get('master_data_health_score', 0.0))}，实体类型覆盖率为 {_format_pct(master_data.get('entity_type_coverage_ratio', 0.0))}。",
        f"证据链追溯分为 {_format_pct(audit.get('audit_trace_score', 0.0))}，30 分钟追溯达标率为 {_format_pct(audit.get('traceback_sla_ratio', 0.0))}。",
        f"决策门槛控制分为 {_format_pct(gates.get('decision_gate_control_score', 0.0))}，规则场景覆盖率为 {_format_pct(gates.get('scenario_coverage_ratio', 0.0))}。",
    ]

    risk_flags = []
    if master_data.get("duplicate_free_ratio", 0.0) < 0.95:
        risk_flags.append("主数据仍存在重复实体，跨品类分析口径可能漂移。")
    if audit.get("traceback_sla_ratio", 0.0) < 0.8:
        risk_flags.append("证据链追溯 SLA 偏弱，关键结论无法稳定在 30 分钟内还原。")
    if audit.get("immutable_audit_ratio", 0.0) < 0.9:
        risk_flags.append("审计日志不可篡改覆盖不足，过程留痕还不够硬。")
    if gates.get("trigger_resolution_ratio", 0.0) < 0.8:
        risk_flags.append("规则触发后的解决闭环不足，告警可能停留在记录层。")
    if gates.get("stop_loss_rule_ratio", 0.0) < 0.2:
        risk_flags.append("止损规则覆盖不足，系统更像监控而不是控制塔。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "data_governance": _score_row(data_governance),
            "audit_rigour": _score_row(audit_rigour),
            "gate_discipline": _score_row(gate_discipline),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }


def build_part1_decision_summary(section_metrics: dict[str, dict]) -> dict:
    demand = section_metrics.get("1.1", {})
    customer = section_metrics.get("1.2", {})
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
    heat_volatility = trend.get("heat_volatility_coefficient", volatility)
    hhi = bottom_up.get("hhi", 0.0)
    gap_ratio = triangulation.get("top_down_vs_bottom_up_gap_ratio", 1.0)
    price_realization = transactions.get("price_realization_rate", 0.0)
    average_discount = transactions.get("average_discount_rate", 0.0)
    strongest_brand_premium = max(pricing.get("brand_premium", {}).values(), default=0.0)
    overall_roas = totals.get("overall_roas") or 0.0
    overall_conversion = totals.get("overall_conversion_rate", 0.0)
    benchmark_coverage = totals.get("benchmark_coverage_ratio", 0.0)
    over_benchmark_ratio = totals.get("over_benchmark_channel_ratio", 0.0)
    size_reference = market.get("market_size_inputs", {})
    size_reference_gap = size_reference.get("assumption_vs_reference_gap_ratio", 1.0)

    demand_strength = demand.get("demand_strength_score")
    if demand_strength is None:
        demand_strength = (
            _clamp01((growth_rate + 0.05) / 0.2) * 0.45
            + _clamp01((cagr + 0.02) / 0.18) * 0.35
            + _clamp01(1 - heat_volatility / 0.25) * 0.2
        )
    market_accessibility = size_reference.get("market_attractiveness_factor")
    if market_accessibility is None:
        market_accessibility = (
            _clamp01(1 - max(hhi - 1000, 0) / 2600) * 0.45
            + _clamp01(1 - gap_ratio / 0.15) * 0.35
            + _clamp01(1 - size_reference_gap / 0.2) * 0.2
        )
    channel_efficiency = channels.get("channel_efficiency_factor")
    if channel_efficiency is None:
        channel_efficiency = (
            _clamp01(overall_conversion / 0.1) * 0.45
            + _clamp01(overall_roas / 8.0) * 0.35
            + _clamp01(benchmark_coverage) * 0.1
            + _clamp01(over_benchmark_ratio) * 0.1
        )
    pricing_power = transactions.get("price_realization_factor")
    if pricing_power is None:
        pricing_power = (
            _clamp01((price_realization - 0.8) / 0.18) * 0.55
            + _clamp01((strongest_brand_premium + 0.1) / 0.8) * 0.45
        )
    customer_fit = (
        float(customer.get("customer_fit_score", 0.0)) * 0.6
        + float(customer.get("persona_confidence_score", 0.0)) * 0.25
        + float(customer.get("persona_concentration_score", 0.0)) * 0.15
    )
    decision_score = round(
        demand_strength * 0.35
        + market_accessibility * 0.2
        + customer_fit * 0.15
        + channel_efficiency * 0.15
        + pricing_power * 0.15,
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
    lag_analysis = demand.get("lag_analysis", {})
    lag_label = (
        f"{lag_analysis.get('best_lag_months')} 个月"
        if lag_analysis.get("best_lag_months") is not None
        else "样本不足"
    )
    key_findings = [
        f"需求端当前 CAGR 为 {_format_pct(cagr)}，热度波动系数为 {_format_pct(heat_volatility)}，重点区域集中在 {top_region or '头部州市场'}。",
        f"市场年化规模约 {bottom_up.get('estimated_annual_market_size', 0.0):,.0f} USD，集中度为 {concentration_level}，Top-Down 与参考面板偏差为 {_format_pct(size_reference_gap)}。",
        f"当前主成交渠道为 {top_channel or '未知'}，渠道领先滞后信号为 {lag_label}，平均实际成交价为 {transactions.get('average_actual_price', 0.0):.2f} USD。",
    ]

    risk_flags = []
    if hhi >= 1800:
        risk_flags.append("市场集中度较高，头部品牌挤压明显。")
    if gap_ratio > 0.1:
        risk_flags.append("市场规模双口径偏差较大，需要补样本校准。")
    if size_reference_gap > 0.15:
        risk_flags.append("显式 TAM/SAM/SOM 参考面板与当前假设偏差较大，Top-Down 需要复核来源。")
    if overall_roas and overall_roas < 4:
        risk_flags.append("渠道广告回报偏弱，冷启动成本可能偏高。")
    if benchmark_coverage < 0.5:
        risk_flags.append("渠道基准覆盖不足，当前渠道判断更多依赖绝对值而非相对行业基准。")
    if price_realization < 0.85 or average_discount > 0.15:
        risk_flags.append("真实成交价折让偏深，挂牌价并不等于可成交价格。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "demand_strength": _score_row(demand_strength),
            "market_accessibility": _score_row(market_accessibility),
            "customer_fit": _score_row(customer_fit),
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


def build_part4_decision_summary(section_metrics: dict[str, dict]) -> dict:
    dtc = section_metrics.get("4.1", {})
    platform = section_metrics.get("4.2", {})
    b2b = section_metrics.get("4.3", {})
    traffic = section_metrics.get("4.4", {})
    roi = section_metrics.get("4.5", {})
    readiness = section_metrics.get("4.6", {})
    entry = section_metrics.get("4.7", {})

    dtc_fit = dtc.get("dtc_fit_score", 0.0)
    platform_fit = platform.get("best_platform_fit_score", 0.0)
    b2b_fit = b2b.get("b2b_viability_score", 0.0)
    channel_optionality = (
        _clamp01(max(dtc_fit, platform_fit, b2b_fit)) * 0.6
        + _clamp01((dtc_fit + platform_fit + b2b_fit) / 3) * 0.4
    )

    traffic_mix = traffic.get("paid_vs_owned", {})
    paid_share = traffic_mix.get("paid_share", traffic_mix.get("paid", entry.get("traffic_paid_share", 1.0))) or 0.0
    owned_share = traffic_mix.get("owned_share", traffic_mix.get("owned", 0.0)) or 0.0
    traffic_quality = (
        _clamp01(1 - paid_share / 0.8) * 0.45
        + _clamp01(traffic.get("funnel", {}).get("session_to_order_rate", 0.0) / 0.04) * 0.3
        + _clamp01(owned_share / 0.4) * 0.25
    )

    blended = roi.get("blended", {})
    monte_carlo = roi.get("monte_carlo", {}).get("overall", {})
    unit_economics = (
        _clamp01(blended.get("contribution_margin_rate", 0.0) / 0.18) * 0.45
        + _clamp01(1 - monte_carlo.get("loss_probability", 1.0) / 0.25) * 0.35
        + _clamp01(1 - blended.get("payback_period_months", 12.0) / 12.0) * 0.2
    )

    operating_readiness = (
        readiness.get("readiness_score", 0.0) * 0.6
        + _clamp01(1 - readiness.get("service_risk_score", 1.0)) * 0.2
        + _clamp01(1 - readiness.get("inventory_risk_score", 1.0)) * 0.2
    )

    decision_score = round(
        channel_optionality * 0.3
        + traffic_quality * 0.2
        + unit_economics * 0.3
        + operating_readiness * 0.2,
        4,
    )

    recommendation = entry.get("recommendation", "")
    if recommendation == "go":
        decision_signal = "go"
        recommended_next_step = "按主攻渠道启动试点，并把预算、SKU 与库存控制在 90 天计划内。"
    elif recommendation == "pilot_first":
        decision_signal = "pilot"
        recommended_next_step = "只做小规模试点，优先验证流量质量与单位经济。"
    else:
        decision_signal = "hold"
        recommended_next_step = "暂停进入，先修复 ROI、组织承接或流量结构问题。"

    primary_channel = entry.get("primary_channel", "")
    best_platform = platform.get("best_platform", "")
    key_findings = [
        f"当前推荐状态为 {recommendation or 'unknown'}，主攻渠道为 {primary_channel or '未指定'}。",
        f"最佳平台为 {best_platform or '未识别'}，综合贡献毛利率约 {_format_pct(blended.get('contribution_margin_rate', 0.0))}。",
        f"组织承接分为 {_format_pct(readiness.get('readiness_score', 0.0))}，总体亏损概率为 {_format_pct(monte_carlo.get('loss_probability', 0.0))}。",
    ]

    risk_flags = []
    if paid_share > 0.7:
        risk_flags.append("流量结构过度依赖付费流量，冷启动成本与放量波动都偏高。")
    if monte_carlo.get("loss_probability", 0.0) > 0.2:
        risk_flags.append("ROI 模型中的亏损概率偏高，试点预算需要更严格上限。")
    if readiness.get("readiness_score", 0.0) < 0.6:
        risk_flags.append("组织承接能力不足，履约、实验或服务链路还不能稳定支持放量。")
    if entry.get("gate_results"):
        failed_gates = [key for key, value in entry["gate_results"].items() if not value]
        if failed_gates:
            risk_flags.append(f"当前仍有未通过的进入门禁：{', '.join(failed_gates)}。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "channel_optionality": _score_row(channel_optionality),
            "traffic_quality": _score_row(traffic_quality),
            "unit_economics": _score_row(unit_economics),
            "operating_readiness": _score_row(operating_readiness),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }


def build_part5_decision_summary(section_metrics: dict[str, dict]) -> dict:
    operating = section_metrics.get("5.1", {})
    monitoring = section_metrics.get("5.2", {})
    growth = section_metrics.get("5.3", {})
    pricing = section_metrics.get("5.4", {})
    inventory = section_metrics.get("5.5", {})
    experiments = section_metrics.get("5.6", {})
    scale = section_metrics.get("5.7", {})

    operating_stability = (
        operating.get("operating_health_score", 0.0) * 0.65
        + _clamp01(1 - operating.get("gate_breach_rate", 1.0)) * 0.35
    )
    monitoring_readiness = (
        monitoring.get("data_coverage_score", 0.0) * 0.55
        + monitoring.get("fee_version_coverage", 0.0) * 0.25
        + monitoring.get("policy_monitoring_completeness", 0.0) * 0.2
    )
    growth_quality = (
        _clamp01(growth.get("repeat_rate", 0.0) / 0.2) * 0.35
        + _clamp01(growth.get("new_customer_efficiency", {}).get("session_to_order_rate", 0.0) / 0.04) * 0.3
        + growth.get("growth_leverage_score", 0.0) * 0.35
    )
    scale_safety = (
        pricing.get("margin_protection_score", 0.0) * 0.35
        + experiments.get("causal_confidence_score", 0.0) * 0.25
        + inventory.get("reorder_readiness_score", 0.0) * 0.2
        + scale.get("scale_readiness_score", 0.0) * 0.2
    )
    decision_score = round(
        operating_stability * 0.3
        + monitoring_readiness * 0.15
        + growth_quality * 0.25
        + scale_safety * 0.3,
        4,
    )

    expansion_gate_status = scale.get("expansion_gate_status", "")
    if expansion_gate_status == "scale_up":
        decision_signal = "ready_to_scale"
        recommended_next_step = "进入加预算与扩渠道阶段，但保持每周经营复盘与门禁监控。"
    elif expansion_gate_status == "hold_and_optimize":
        decision_signal = "optimize_before_scale"
        recommended_next_step = "保持当前渠道节奏，优先修复利润、监控或实验链路后再扩张。"
    elif expansion_gate_status == "pilot_only":
        decision_signal = "pilot_only"
        recommended_next_step = "维持试运营，继续补齐数据、实验和库存周转能力。"
    else:
        decision_signal = "rollback_risk"
        recommended_next_step = "暂停扩张，先处理高优先级预警和回滚触发项。"

    alert_count = scale.get("alerts", {}).get("alert_count", 0)
    change_signal_count = scale.get("change_signal_count", 0)
    top_budget_channel = next(iter(scale.get("budget_allocation", {}).keys()), "")
    key_findings = [
        f"当前经营健康分为 {_format_pct(operating.get('operating_health_score', 0.0))}，扩张状态为 {expansion_gate_status or 'unknown'}。",
        f"增长杠杆分为 {_format_pct(growth.get('growth_leverage_score', 0.0))}，利润保护分为 {_format_pct(pricing.get('margin_protection_score', 0.0))}。",
        f"当前预算建议优先投向 {top_budget_channel or '主力渠道'}，系统共识别 {alert_count} 条经营预警，其中变点信号 {change_signal_count} 条。",
    ]

    risk_flags = []
    if operating.get("gate_breach_rate", 0.0) > 0.2:
        risk_flags.append("门禁突破率偏高，经营稳定性不足以支持直接放量。")
    if monitoring.get("data_coverage_score", 0.0) < 0.7:
        risk_flags.append("监控覆盖不足，异常可能无法被及时识别。")
    if pricing.get("promo_dependency_score", 0.0) > 0.5:
        risk_flags.append("促销依赖度偏高，利润保护能力仍然偏弱。")
    if inventory.get("stockout_risk", 0.0) > 0.25 or inventory.get("overstock_risk", 0.0) > 0.25:
        risk_flags.append("库存结构存在明显偏差，现金和履约风险需要前置处理。")
    if experiments.get("causal_confidence_score", 0.0) < 0.6:
        risk_flags.append("实验系统置信度不足，扩张决策仍缺少稳定因果证据。")
    if change_signal_count > 0:
        risk_flags.append("近期经营序列已出现变点信号，放量前需要先完成根因排查和回滚动作。")
    if expansion_gate_status == "rollback":
        risk_flags.append("当前存在高优先级预警，扩张建议已降级为回滚或止损。")

    return {
        "decision_signal": decision_signal,
        "decision_score": decision_score,
        "scorecard": {
            "operating_stability": _score_row(operating_stability),
            "monitoring_readiness": _score_row(monitoring_readiness),
            "growth_quality": _score_row(growth_quality),
            "scale_safety": _score_row(scale_safety),
        },
        "key_findings": key_findings,
        "risk_flags": risk_flags,
        "recommended_next_step": recommended_next_step,
    }
