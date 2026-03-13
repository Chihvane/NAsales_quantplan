from __future__ import annotations

from collections import defaultdict
from datetime import date

from .models import (
    B2BAccountRecord,
    ChannelRateCardRecord,
    CustomerCohortRecord,
    ExperimentRecord,
    InventoryPositionRecord,
    LandedCostScenarioRecord,
    MarketingSpendRecord,
    Part4Assumptions,
    Part4Dataset,
    ReturnClaimRecord,
    SoldTransactionRecord,
    TrafficSessionRecord,
)
from .stats_utils import (
    mean_or_zero as _mean_or_zero,
    safe_divide as _safe_divide,
    score_level,
)


DTC_CHANNELS = {"dtc", "shopify", "independent site", "direct website"}
B2B_CHANNELS = {"b2b", "wholesale", "distributor", "dealer"}
PAID_SOURCES = {
    "paid_search",
    "paid_social",
    "affiliate",
    "amazon_ads",
    "tiktok_ads",
    "walmart_ads",
    "ebay_promoted",
}
OWNED_SOURCES = {"direct", "email", "sms", "organic_search", "organic_social"}

def _level(score: float) -> str:
    return score_level(score)


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _channel_family(channel: str) -> str:
    normalized = channel.strip().lower()
    if normalized in DTC_CHANNELS:
        return "dtc"
    if normalized in B2B_CHANNELS:
        return "b2b"
    return "platform"


def _source_family(source: str) -> str:
    normalized = source.strip().lower()
    if normalized in PAID_SOURCES:
        return "paid"
    if normalized in OWNED_SOURCES:
        return "owned"
    return "other"


def _rate_bucket(fee_type: str) -> str:
    normalized = fee_type.strip().lower()
    if "payment" in normalized:
        return "payment_cost_total"
    if "storage" in normalized or "warehouse" in normalized:
        return "storage_cost_total"
    if "fulfill" in normalized or "shipping" in normalized or "fba" in normalized:
        return "fulfillment_cost_total"
    if "refund" in normalized or "claim" in normalized or "dispute" in normalized:
        return "refund_and_return_total"
    return "channel_fees_total"


def _scenario_lookup(
    scenarios: list[LandedCostScenarioRecord],
) -> tuple[dict[tuple[str, str], LandedCostScenarioRecord], dict[str, dict[str, float]]]:
    lookup: dict[tuple[str, str], LandedCostScenarioRecord] = {}
    channel_values: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"p10": [], "p50": [], "p90": [], "confidence": []}
    )
    for record in scenarios:
        key = (record.channel, record.canonical_sku)
        current = lookup.get(key)
        if current is None or record.scenario_confidence_score > current.scenario_confidence_score:
            lookup[key] = record
        channel_values[record.channel]["p10"].append(record.landed_cost_p10 + record.working_capital_cost + record.return_reserve)
        channel_values[record.channel]["p50"].append(record.landed_cost_p50 + record.working_capital_cost + record.return_reserve)
        channel_values[record.channel]["p90"].append(record.landed_cost_p90 + record.working_capital_cost + record.return_reserve)
        channel_values[record.channel]["confidence"].append(record.scenario_confidence_score)
    fallback = {}
    for channel, values in channel_values.items():
        fallback[channel] = {
            "p10": round(_mean_or_zero(values["p10"]), 2),
            "p50": round(_mean_or_zero(values["p50"]), 2),
            "p90": round(_mean_or_zero(values["p90"]), 2),
            "confidence": round(_mean_or_zero(values["confidence"]), 4),
        }
    return lookup, fallback


def _sales_lookup(
    sold_transactions: list[SoldTransactionRecord],
) -> dict[str, dict]:
    channel_sales: dict[str, dict] = defaultdict(
        lambda: {
            "orders": 0,
            "units": 0,
            "revenue": 0.0,
            "sku_units": defaultdict(int),
            "sku_revenue": defaultdict(float),
        }
    )
    for record in sold_transactions:
        revenue = (record.transaction_price + record.shipping_fee) * record.units
        bucket = channel_sales[record.platform]
        bucket["orders"] += 1
        bucket["units"] += record.units
        bucket["revenue"] += revenue
        bucket["sku_units"][record.canonical_sku] += record.units
        bucket["sku_revenue"][record.canonical_sku] += revenue
    return channel_sales


def _traffic_lookup(
    traffic_sessions: list[TrafficSessionRecord],
) -> tuple[dict[str, dict], dict[str, dict]]:
    channel_traffic: dict[str, dict] = defaultdict(
        lambda: {
            "sessions": 0,
            "product_page_views": 0,
            "add_to_cart": 0,
            "checkout_start": 0,
            "orders": 0,
        }
    )
    source_traffic: dict[str, dict] = defaultdict(
        lambda: {
            "sessions": 0,
            "product_page_views": 0,
            "add_to_cart": 0,
            "checkout_start": 0,
            "orders": 0,
        }
    )
    for record in traffic_sessions:
        channel_bucket = channel_traffic[record.channel]
        source_bucket = source_traffic[record.traffic_source or "unknown"]
        for bucket in (channel_bucket, source_bucket):
            bucket["sessions"] += record.sessions
            bucket["product_page_views"] += record.product_page_views
            bucket["add_to_cart"] += record.add_to_cart
            bucket["checkout_start"] += record.checkout_start
            bucket["orders"] += record.orders
    return channel_traffic, source_traffic


def _marketing_lookup(
    marketing_spend: list[MarketingSpendRecord],
) -> tuple[dict[str, dict], dict[str, dict]]:
    channel_marketing: dict[str, dict] = defaultdict(
        lambda: {
            "spend": 0.0,
            "impressions": 0,
            "clicks": 0,
            "attributed_orders": 0,
            "attributed_revenue": 0.0,
        }
    )
    source_marketing: dict[str, dict] = defaultdict(
        lambda: {
            "spend": 0.0,
            "impressions": 0,
            "clicks": 0,
            "attributed_orders": 0,
            "attributed_revenue": 0.0,
        }
    )
    for record in marketing_spend:
        channel_bucket = channel_marketing[record.channel]
        source_bucket = source_marketing[record.traffic_source or "unknown"]
        for bucket in (channel_bucket, source_bucket):
            bucket["spend"] += record.spend
            bucket["impressions"] += record.impressions
            bucket["clicks"] += record.clicks
            bucket["attributed_orders"] += record.attributed_orders
            bucket["attributed_revenue"] += record.attributed_revenue
    return channel_marketing, source_marketing


def _returns_lookup(
    returns_claims: list[ReturnClaimRecord],
) -> dict[str, dict]:
    channel_returns: dict[str, dict] = defaultdict(
        lambda: {
            "return_orders": 0,
            "refund_amount_total": 0.0,
            "claim_cost_total": 0.0,
            "dispute_count": 0,
        }
    )
    for record in returns_claims:
        bucket = channel_returns[record.channel]
        bucket["return_orders"] += 1 if record.return_flag else 0
        bucket["refund_amount_total"] += record.refund_amount
        bucket["claim_cost_total"] += record.claim_cost
        bucket["dispute_count"] += 1 if record.dispute_flag else 0
    return channel_returns


def _cohort_lookup(
    customer_cohorts: list[CustomerCohortRecord],
) -> dict[str, dict]:
    channel_cohorts: dict[str, dict] = defaultdict(
        lambda: {
            "customers": 0,
            "repeat_customers": 0,
            "repeat_orders": 0,
            "repeat_revenue": 0.0,
        }
    )
    for record in customer_cohorts:
        bucket = channel_cohorts[record.channel]
        bucket["customers"] += record.customers
        bucket["repeat_customers"] += record.repeat_customers
        bucket["repeat_orders"] += record.repeat_orders
        bucket["repeat_revenue"] += record.repeat_revenue
    return channel_cohorts


def _inventory_lookup(
    inventory_positions: list[InventoryPositionRecord],
) -> dict[str, dict]:
    channel_inventory: dict[str, dict] = defaultdict(
        lambda: {
            "on_hand_units": [],
            "inbound_units": [],
            "sell_through_units": 0,
            "storage_cost_total": 0.0,
            "dates": [],
        }
    )
    for record in inventory_positions:
        bucket = channel_inventory[record.channel]
        bucket["on_hand_units"].append(record.on_hand_units)
        bucket["inbound_units"].append(record.inbound_units)
        bucket["sell_through_units"] += record.sell_through_units
        bucket["storage_cost_total"] += record.storage_cost
        parsed = _parse_date(record.date)
        if parsed is not None:
            bucket["dates"].append(parsed)

    summary = {}
    for channel, bucket in channel_inventory.items():
        dates = bucket["dates"]
        window_days = 30
        if len(dates) >= 2:
            window_days = max((max(dates) - min(dates)).days + 1, 1)
        summary[channel] = {
            "avg_on_hand_units": round(_mean_or_zero(bucket["on_hand_units"]), 2),
            "avg_inbound_units": round(_mean_or_zero(bucket["inbound_units"]), 2),
            "sell_through_units": bucket["sell_through_units"],
            "storage_cost_total": round(bucket["storage_cost_total"], 2),
            "window_days": window_days,
        }
    return summary


def _experiment_summary(
    experiments: list[ExperimentRecord],
    minimum_days: int,
) -> dict:
    if not experiments:
        return {
            "coverage_ratio": 0.0,
            "completed_count": 0,
            "active_count": 0,
            "minimum_duration_pass_rate": 0.0,
            "channels_covered": [],
        }

    channels_covered = sorted({record.channel for record in experiments if record.channel})
    completed_count = sum(1 for record in experiments if record.status.lower() == "completed")
    active_count = sum(1 for record in experiments if record.status.lower() == "active")
    duration_flags = []
    for record in experiments:
        start_date = _parse_date(record.start_date)
        end_date = _parse_date(record.end_date)
        if start_date is None or end_date is None:
            continue
        duration_flags.append((end_date - start_date).days >= minimum_days)
    return {
        "coverage_ratio": round(len(channels_covered) / max(len(channels_covered), 1), 4),
        "completed_count": completed_count,
        "active_count": active_count,
        "minimum_duration_pass_rate": round(
            sum(1 for flag in duration_flags if flag) / len(duration_flags),
            4,
        )
        if duration_flags
        else 0.0,
        "channels_covered": channels_covered,
    }


def _fee_cost_from_card(
    card: ChannelRateCardRecord,
    revenue: float,
    orders: int,
    units: int,
    sessions: int,
    spend: float,
    avg_inventory_units: float,
) -> float:
    basis = card.fee_basis.lower()
    fee_rate = card.fee_rate
    fixed_fee = card.fixed_fee
    if basis == "revenue":
        return revenue * fee_rate + orders * fixed_fee
    if basis in {"orders", "order"}:
        return orders * (fixed_fee + fee_rate)
    if basis in {"units", "unit"}:
        return units * (fixed_fee + fee_rate)
    if basis == "inventory_units":
        return avg_inventory_units * (fixed_fee + fee_rate)
    if basis == "spend":
        return spend * fee_rate + fixed_fee
    if basis == "sessions":
        return sessions * (fixed_fee + fee_rate)
    if basis == "fixed_monthly":
        return fixed_fee + revenue * fee_rate
    return revenue * fee_rate + fixed_fee


def compute_channel_pnl_rows(dataset: Part4Dataset, assumptions: Part4Assumptions) -> list[dict]:
    sales_lookup = _sales_lookup(dataset.sold_transactions)
    traffic_lookup, source_traffic = _traffic_lookup(dataset.traffic_sessions)
    marketing_lookup, source_marketing = _marketing_lookup(dataset.marketing_spend)
    returns_lookup = _returns_lookup(dataset.returns_claims)
    cohort_lookup = _cohort_lookup(dataset.customer_cohorts)
    inventory_lookup = _inventory_lookup(dataset.inventory_positions)
    scenario_lookup, scenario_fallback = _scenario_lookup(dataset.landed_cost_scenarios)

    rate_cards_by_channel: dict[str, list[ChannelRateCardRecord]] = defaultdict(list)
    for record in dataset.channel_rate_cards:
        rate_cards_by_channel[record.channel].append(record)

    channel_names = set(sales_lookup) | set(traffic_lookup) | set(marketing_lookup) | set(scenario_fallback) | set(rate_cards_by_channel) | set(cohort_lookup) | set(inventory_lookup) | set(returns_lookup)
    rows = []
    for channel in sorted(channel_names):
        sales = sales_lookup.get(channel, {})
        traffic = traffic_lookup.get(channel, {})
        marketing = marketing_lookup.get(channel, {})
        returns = returns_lookup.get(channel, {})
        cohorts = cohort_lookup.get(channel, {})
        inventory = inventory_lookup.get(channel, {})
        units = int(sales.get("units", 0))
        orders = int(sales.get("orders", 0) or traffic.get("orders", 0))
        revenue = float(sales.get("revenue", 0.0) or marketing.get("attributed_revenue", 0.0))
        sessions = int(traffic.get("sessions", 0))
        product_page_views = int(traffic.get("product_page_views", 0))
        add_to_cart = int(traffic.get("add_to_cart", 0))
        checkout_start = int(traffic.get("checkout_start", 0))
        spend = float(marketing.get("spend", 0.0))
        impressions = int(marketing.get("impressions", 0))
        clicks = int(marketing.get("clicks", 0))
        avg_on_hand_units = float(inventory.get("avg_on_hand_units", 0.0))
        avg_inbound_units = float(inventory.get("avg_inbound_units", 0.0))
        storage_cost_inventory = float(inventory.get("storage_cost_total", 0.0))

        landed_cost_total = 0.0
        landed_cost_p10_total = 0.0
        landed_cost_p90_total = 0.0
        scenario_confidence_scores = []
        sku_units = sales.get("sku_units", {})
        fallback = scenario_fallback.get(channel, {"p10": 0.0, "p50": 0.0, "p90": 0.0, "confidence": 0.0})
        for canonical_sku, sku_unit_count in sku_units.items():
            scenario = scenario_lookup.get((channel, canonical_sku))
            if scenario is None:
                landed_cost_total += fallback["p50"] * sku_unit_count
                landed_cost_p10_total += fallback["p10"] * sku_unit_count
                landed_cost_p90_total += fallback["p90"] * sku_unit_count
                scenario_confidence_scores.append(fallback["confidence"])
                continue
            landed_cost_total += (
                scenario.landed_cost_p50 + scenario.working_capital_cost + scenario.return_reserve
            ) * sku_unit_count
            landed_cost_p10_total += (
                scenario.landed_cost_p10 + scenario.working_capital_cost + scenario.return_reserve
            ) * sku_unit_count
            landed_cost_p90_total += (
                scenario.landed_cost_p90 + scenario.working_capital_cost + scenario.return_reserve
            ) * sku_unit_count
            scenario_confidence_scores.append(scenario.scenario_confidence_score)

        if units <= 0 and fallback["p50"] > 0 and revenue > 0:
            inferred_units = max(round(revenue / max(fallback["p50"] * 1.8, 1)), 1)
            units = inferred_units
            orders = max(orders, inferred_units)
            landed_cost_total = fallback["p50"] * inferred_units
            landed_cost_p10_total = fallback["p10"] * inferred_units
            landed_cost_p90_total = fallback["p90"] * inferred_units
            scenario_confidence_scores.append(fallback["confidence"])

        fee_totals = {
            "channel_fees_total": 0.0,
            "fulfillment_cost_total": 0.0,
            "payment_cost_total": 0.0,
            "storage_cost_total": 0.0,
            "refund_and_return_total": 0.0,
        }
        rate_cards = rate_cards_by_channel.get(channel, [])
        fee_effective_dates = []
        for card in rate_cards:
            cost = _fee_cost_from_card(
                card,
                revenue,
                orders,
                units,
                sessions,
                spend,
                avg_on_hand_units,
            )
            fee_totals[_rate_bucket(card.fee_type)] += cost
            if card.effective_date:
                fee_effective_dates.append(card.effective_date)

        refund_and_return_total = (
            fee_totals["refund_and_return_total"]
            + returns.get("refund_amount_total", 0.0)
            + returns.get("claim_cost_total", 0.0)
        )
        storage_cost_total = fee_totals["storage_cost_total"] + storage_cost_inventory
        channel_fees_total = fee_totals["channel_fees_total"]
        fulfillment_cost_total = fee_totals["fulfillment_cost_total"]
        payment_cost_total = fee_totals["payment_cost_total"]

        contribution_profit = (
            revenue
            - landed_cost_total
            - channel_fees_total
            - fulfillment_cost_total
            - payment_cost_total
            - storage_cost_total
            - spend
            - refund_and_return_total
        )
        contribution_margin_rate = _safe_divide(contribution_profit, revenue)
        aov = _safe_divide(revenue, orders)
        conversion_rate = _safe_divide(orders, sessions)
        avg_sell_price = _safe_divide(revenue, units)
        return_rate = _safe_divide(returns.get("return_orders", 0), orders)
        dispute_rate = _safe_divide(returns.get("dispute_count", 0), orders)
        repeat_rate = _safe_divide(cohorts.get("repeat_customers", 0), cohorts.get("customers", 0))
        repeat_orders_per_customer = _safe_divide(cohorts.get("repeat_orders", 0), cohorts.get("customers", 0))
        ltv = aov * max(contribution_margin_rate, 0.0) * (1 + repeat_orders_per_customer)
        cac = _safe_divide(spend, orders)
        contribution_per_customer = aov * max(contribution_margin_rate, 0.01) * (1 + max(repeat_rate, 0.0))
        payback_period_months = _safe_divide(cac, contribution_per_customer)
        daily_sell_through = _safe_divide(inventory.get("sell_through_units", 0), inventory.get("window_days", 30))
        inventory_days = _safe_divide(avg_on_hand_units + 0.5 * avg_inbound_units, daily_sell_through)
        cost_base = (
            landed_cost_total
            + channel_fees_total
            + fulfillment_cost_total
            + payment_cost_total
            + storage_cost_total
            + spend
            + refund_and_return_total
        )
        roi = _safe_divide(contribution_profit, cost_base)

        row = {
            "channel": channel,
            "channel_family": _channel_family(channel),
            "impressions": impressions,
            "clicks": clicks,
            "sessions": sessions,
            "product_page_views": product_page_views,
            "add_to_cart": add_to_cart,
            "checkout_start": checkout_start,
            "orders": orders,
            "units": units,
            "revenue": round(revenue, 2),
            "avg_sell_price": round(avg_sell_price, 2),
            "aov": round(aov, 2),
            "landed_cost_total": round(landed_cost_total, 2),
            "landed_cost_unit_p10": round(_safe_divide(landed_cost_p10_total, max(units, 1)), 2),
            "landed_cost_unit_p50": round(_safe_divide(landed_cost_total, max(units, 1)), 2),
            "landed_cost_unit_p90": round(_safe_divide(landed_cost_p90_total, max(units, 1)), 2),
            "channel_fees_total": round(channel_fees_total, 2),
            "fulfillment_cost_total": round(fulfillment_cost_total, 2),
            "payment_cost_total": round(payment_cost_total, 2),
            "storage_cost_total": round(storage_cost_total, 2),
            "acquisition_cost_total": round(spend, 2),
            "refund_and_return_total": round(refund_and_return_total, 2),
            "contribution_profit": round(contribution_profit, 2),
            "contribution_margin_rate": round(contribution_margin_rate, 4),
            "roi": round(roi, 4),
            "conversion_rate": round(conversion_rate, 4),
            "page_view_rate": round(_safe_divide(product_page_views, sessions), 4),
            "add_to_cart_rate": round(_safe_divide(add_to_cart, product_page_views), 4),
            "checkout_start_rate": round(_safe_divide(checkout_start, add_to_cart), 4),
            "checkout_completion_rate": round(_safe_divide(orders, checkout_start), 4),
            "cac": round(cac, 2),
            "repeat_rate": round(repeat_rate, 4),
            "ltv": round(ltv, 2),
            "payback_period_months": round(payback_period_months, 2),
            "return_rate": round(return_rate, 4),
            "dispute_rate": round(dispute_rate, 4),
            "avg_inventory_units": round(avg_on_hand_units, 2),
            "inventory_days": round(inventory_days, 2),
            "scenario_confidence_score": round(_mean_or_zero(scenario_confidence_scores), 4),
            "fee_version_count": len(fee_effective_dates),
            "latest_fee_effective_date": max(fee_effective_dates) if fee_effective_dates else "",
        }
        rows.append(row)

    rows.sort(key=lambda item: item["revenue"], reverse=True)
    return rows


def compute_dtc_metrics(
    channel_rows: list[dict],
    assumptions: Part4Assumptions,
) -> dict:
    dtc_rows = [row for row in channel_rows if row["channel_family"] == "dtc"]
    if not dtc_rows:
        return {}
    revenue = sum(row["revenue"] for row in dtc_rows)
    sessions = sum(row["sessions"] for row in dtc_rows)
    orders = sum(row["orders"] for row in dtc_rows)
    repeat_rate = _safe_divide(
        sum(row["repeat_rate"] * row["orders"] for row in dtc_rows),
        sum(row["orders"] for row in dtc_rows),
    )
    contribution_margin_rate = _safe_divide(
        sum(row["contribution_profit"] for row in dtc_rows),
        revenue,
    )
    payback = _safe_divide(
        sum(row["payback_period_months"] * row["orders"] for row in dtc_rows),
        max(orders, 1),
    )
    owned_share_proxy = 1 - _safe_divide(
        sum(row["acquisition_cost_total"] for row in dtc_rows),
        max(revenue, 1),
    )
    brandability_score = min(
        1.0,
        max(repeat_rate / max(assumptions.target_repeat_rate, 0.01), 0.0) * 0.35
        + max(owned_share_proxy, 0.0) * 0.2
        + max(contribution_margin_rate / max(assumptions.min_contribution_margin_rate, 0.01), 0.0) * 0.3
        + max(1 - payback / max(assumptions.target_payback_months, 1), 0.0) * 0.15,
    )
    fit_score = min(
        1.0,
        brandability_score * 0.55
        + max(0.0, 1 - payback / max(assumptions.target_payback_months, 1)) * 0.25
        + max(0.0, contribution_margin_rate) * 0.2,
    )
    return {
        "dtc_channels": dtc_rows,
        "revenue": round(revenue, 2),
        "sessions": sessions,
        "orders": orders,
        "conversion_rate": round(_safe_divide(orders, sessions), 4),
        "weighted_repeat_rate": round(repeat_rate, 4),
        "weighted_contribution_margin_rate": round(contribution_margin_rate, 4),
        "weighted_payback_period_months": round(payback, 2),
        "brandability_score": round(brandability_score, 4),
        "dtc_fit_score": round(fit_score, 4),
        "fit_level": _level(fit_score),
    }


def compute_platform_metrics(
    channel_rows: list[dict],
    assumptions: Part4Assumptions,
) -> dict:
    platform_rows = [row for row in channel_rows if row["channel_family"] == "platform"]
    if not platform_rows:
        return {}
    scored = []
    for row in platform_rows:
        fit_score = min(
            1.0,
            max(row["contribution_margin_rate"] / max(assumptions.min_contribution_margin_rate, 0.01), 0.0) * 0.4
            + max(row["conversion_rate"] / 0.12, 0.0) * 0.25
            + max(1 - row["return_rate"] / 0.12, 0.0) * 0.15
            + max(1 - row["payback_period_months"] / max(assumptions.target_payback_months, 1), 0.0) * 0.2,
        )
        scored.append({**row, "platform_fit_score": round(fit_score, 4)})
    scored.sort(key=lambda item: item["platform_fit_score"], reverse=True)
    return {
        "platforms": scored,
        "best_platform": scored[0]["channel"],
        "best_platform_fit_score": scored[0]["platform_fit_score"],
        "platform_count": len(scored),
        "weighted_platform_margin_rate": round(
            _safe_divide(sum(row["contribution_profit"] for row in platform_rows), sum(row["revenue"] for row in platform_rows)),
            4,
        ),
    }


def compute_b2b_metrics(
    channel_rows: list[dict],
    b2b_accounts: list[B2BAccountRecord],
) -> dict:
    b2b_rows = [row for row in channel_rows if row["channel_family"] == "b2b"]
    if not b2b_rows and not b2b_accounts:
        return {}
    total_target = sum(account.annual_target for account in b2b_accounts)
    weighted_terms = _safe_divide(
        sum(account.payment_terms_days * account.annual_target for account in b2b_accounts),
        max(total_target, 1),
    )
    weighted_discount = _safe_divide(
        sum(account.discount_rate * account.annual_target for account in b2b_accounts),
        max(total_target, 1),
    )
    weighted_rebate = _safe_divide(
        sum(account.rebate_rate * account.annual_target for account in b2b_accounts),
        max(total_target, 1),
    )
    revenue = sum(row["revenue"] for row in b2b_rows)
    margin_rate = _safe_divide(sum(row["contribution_profit"] for row in b2b_rows), revenue)
    direct_margin = max(
        [row["contribution_margin_rate"] for row in channel_rows if row["channel_family"] != "b2b"],
        default=0.0,
    )
    viability_score = min(
        1.0,
        max(margin_rate, 0.0) * 0.45
        + max(1 - weighted_terms / 90, 0.0) * 0.25
        + max(1 - weighted_discount, 0.0) * 0.2
        + max(1 - weighted_rebate, 0.0) * 0.1,
    )
    return {
        "account_count": len(b2b_accounts),
        "annual_target_total": round(total_target, 2),
        "weighted_payment_terms_days": round(weighted_terms, 2),
        "weighted_discount_rate": round(weighted_discount, 4),
        "weighted_rebate_rate": round(weighted_rebate, 4),
        "b2b_channels": b2b_rows,
        "b2b_margin_rate": round(margin_rate, 4),
        "margin_gap_vs_best_direct_channel": round(margin_rate - direct_margin, 4),
        "b2b_viability_score": round(viability_score, 4),
        "viability_level": _level(viability_score),
    }


def compute_traffic_metrics(
    dataset: Part4Dataset,
    channel_rows: list[dict],
) -> dict:
    _, source_traffic = _traffic_lookup(dataset.traffic_sessions)
    _, source_marketing = _marketing_lookup(dataset.marketing_spend)
    source_names = set(source_traffic) | set(source_marketing)
    total_sessions = sum(bucket.get("sessions", 0) for bucket in source_traffic.values())
    total_orders = sum(bucket.get("orders", 0) for bucket in source_traffic.values())
    total_spend = sum(bucket.get("spend", 0.0) for bucket in source_marketing.values())
    source_rows = []
    paid_sessions = 0
    owned_sessions = 0
    for source_name in sorted(source_names):
        traffic = source_traffic.get(source_name, {})
        marketing = source_marketing.get(source_name, {})
        family = _source_family(source_name)
        sessions = int(traffic.get("sessions", 0))
        orders = int(traffic.get("orders", 0))
        spend = float(marketing.get("spend", 0.0))
        if family == "paid":
            paid_sessions += sessions
        elif family == "owned":
            owned_sessions += sessions
        source_rows.append(
            {
                "traffic_source": source_name,
                "source_family": family,
                "sessions": sessions,
                "session_share": round(_safe_divide(sessions, total_sessions), 4),
                "orders": orders,
                "order_share": round(_safe_divide(orders, total_orders), 4),
                "spend": round(spend, 2),
                "spend_share": round(_safe_divide(spend, total_spend), 4),
                "impressions": int(marketing.get("impressions", 0)),
                "clicks": int(marketing.get("clicks", 0)),
                "ctr": round(_safe_divide(marketing.get("clicks", 0), marketing.get("impressions", 0)), 4),
                "cpc": round(_safe_divide(spend, marketing.get("clicks", 0)), 2),
                "cpa": round(_safe_divide(spend, max(orders, 1)), 2) if spend else 0.0,
            }
        )
    source_rows.sort(key=lambda row: row["sessions"], reverse=True)
    total_channel_sessions = sum(row["sessions"] for row in channel_rows)
    total_channel_orders = sum(row["orders"] for row in channel_rows)
    funnel = {
        "sessions": total_channel_sessions,
        "product_page_views": sum(row["product_page_views"] for row in channel_rows),
        "add_to_cart": sum(row["add_to_cart"] for row in channel_rows),
        "checkout_start": sum(row["checkout_start"] for row in channel_rows),
        "orders": total_channel_orders,
        "page_view_rate": round(
            _safe_divide(sum(row["product_page_views"] for row in channel_rows), total_channel_sessions),
            4,
        ),
        "add_to_cart_rate": round(
            _safe_divide(sum(row["add_to_cart"] for row in channel_rows), sum(row["product_page_views"] for row in channel_rows)),
            4,
        ),
        "checkout_start_rate": round(
            _safe_divide(sum(row["checkout_start"] for row in channel_rows), sum(row["add_to_cart"] for row in channel_rows)),
            4,
        ),
        "checkout_completion_rate": round(
            _safe_divide(total_channel_orders, sum(row["checkout_start"] for row in channel_rows)),
            4,
        ),
    }
    return {
        "source_rows": source_rows,
        "traffic_source_sessions_share": {
            row["traffic_source"]: row["session_share"]
            for row in source_rows
        },
        "paid_vs_owned": {
            "paid": round(_safe_divide(paid_sessions, total_sessions), 4),
            "owned": round(_safe_divide(owned_sessions, total_sessions), 4),
            "other": round(max(0.0, 1 - _safe_divide(paid_sessions + owned_sessions, total_sessions)), 4),
        },
        "funnel": funnel,
    }


def compute_roi_metrics(
    channel_rows: list[dict],
    monte_carlo: dict,
) -> dict:
    if not channel_rows:
        return {}
    total_revenue = sum(row["revenue"] for row in channel_rows)
    total_profit = sum(row["contribution_profit"] for row in channel_rows)
    total_spend = sum(row["acquisition_cost_total"] for row in channel_rows)
    blended_margin_rate = _safe_divide(total_profit, total_revenue)
    best_channel = max(channel_rows, key=lambda row: row["contribution_margin_rate"])
    return {
        "channel_pnl": channel_rows,
        "blended": {
            "revenue": round(total_revenue, 2),
            "contribution_profit": round(total_profit, 2),
            "contribution_margin_rate": round(blended_margin_rate, 4),
            "acquisition_cost_total": round(total_spend, 2),
            "roi": round(_safe_divide(total_profit, max(total_spend, 1)), 4),
        },
        "best_channel": {
            "channel": best_channel["channel"],
            "contribution_margin_rate": best_channel["contribution_margin_rate"],
            "roi": best_channel["roi"],
            "payback_period_months": best_channel["payback_period_months"],
        },
        "monte_carlo": monte_carlo,
    }


def compute_team_readiness_metrics(
    dataset: Part4Dataset,
    channel_rows: list[dict],
    assumptions: Part4Assumptions,
    traffic_metrics: dict,
) -> dict:
    experiment_summary = _experiment_summary(
        dataset.experiment_registry,
        assumptions.minimum_experiment_days,
    )
    paid_share = traffic_metrics.get("paid_vs_owned", {}).get("paid", 0.0)
    inventory_days = [row["inventory_days"] for row in channel_rows if row["inventory_days"] > 0]
    return_rates = [row["return_rate"] for row in channel_rows]
    dispute_rates = [row["dispute_rate"] for row in channel_rows]
    inventory_risk_score = min(
        1.0,
        _safe_divide(_mean_or_zero(inventory_days), max(assumptions.target_inventory_days, 1)),
    )
    service_risk_score = min(1.0, _mean_or_zero(return_rates) * 4 + _mean_or_zero(dispute_rates) * 3)
    readiness_score = min(
        1.0,
        experiment_summary["minimum_duration_pass_rate"] * 0.25
        + min(len(experiment_summary["channels_covered"]) / max(len(channel_rows), 1), 1.0) * 0.2
        + max(1 - paid_share, 0.0) * 0.2
        + max(1 - inventory_risk_score, 0.0) * 0.2
        + max(1 - service_risk_score, 0.0) * 0.15,
    )
    return {
        "experiment_summary": experiment_summary,
        "paid_dependency_score": round(paid_share, 4),
        "inventory_risk_score": round(inventory_risk_score, 4),
        "service_risk_score": round(service_risk_score, 4),
        "readiness_score": round(readiness_score, 4),
        "readiness_level": _level(readiness_score),
    }


def compute_entry_plan_metrics(
    channel_rows: list[dict],
    dtc_metrics: dict,
    platform_metrics: dict,
    b2b_metrics: dict,
    traffic_metrics: dict,
    roi_metrics: dict,
    team_metrics: dict,
    assumptions: Part4Assumptions,
) -> dict:
    if not channel_rows:
        return {}

    monte_carlo_overall = roi_metrics.get("monte_carlo", {}).get("overall", {})
    best_channel = roi_metrics.get("best_channel", {})
    gate_results = {
        "margin_gate": best_channel.get("contribution_margin_rate", 0.0) >= assumptions.min_contribution_margin_rate,
        "payback_gate": best_channel.get("payback_period_months", 999) <= assumptions.target_payback_months,
        "loss_gate": monte_carlo_overall.get("loss_probability", 1.0) <= assumptions.max_loss_probability,
        "repeat_gate": dtc_metrics.get("weighted_repeat_rate", 0.0) >= assumptions.target_repeat_rate
        if dtc_metrics
        else True,
        "inventory_gate": max((row["inventory_days"] for row in channel_rows), default=0.0) <= assumptions.target_inventory_days * 1.25,
        "readiness_gate": team_metrics.get("readiness_score", 0.0) >= 0.55,
    }

    scored_channels = []
    channel_loss_lookup = roi_metrics.get("monte_carlo", {}).get("channels", {})
    for row in channel_rows:
        loss_probability = channel_loss_lookup.get(row["channel"], {}).get("loss_probability", 0.0)
        score = (
            row["contribution_margin_rate"] * 0.45
            + row["conversion_rate"] * 0.2
            + row["repeat_rate"] * 0.15
            + max(1 - row["payback_period_months"] / max(assumptions.target_payback_months, 1), 0.0) * 0.1
            + max(1 - loss_probability / max(assumptions.max_loss_probability, 0.01), 0.0) * 0.1
            - assumptions.risk_penalty_lambda * row["return_rate"]
        )
        scored_channels.append(
            {
                "channel": row["channel"],
                "channel_family": row["channel_family"],
                "priority_score": round(score, 4),
            }
        )
    scored_channels.sort(key=lambda item: item["priority_score"], reverse=True)
    total_positive_score = sum(max(item["priority_score"], 0.0) for item in scored_channels) or 1.0
    budget_allocation = {
        item["channel"]: round(max(item["priority_score"], 0.0) / total_positive_score, 4)
        for item in scored_channels[:3]
    }

    pass_count = sum(1 for value in gate_results.values() if value)
    if gate_results["margin_gate"] and gate_results["payback_gate"] and gate_results["loss_gate"] and pass_count >= 5:
        recommendation = "go"
    elif gate_results["margin_gate"] and pass_count >= 3:
        recommendation = "pilot_first"
    else:
        recommendation = "no_go"

    failed_risks = [name for name, status in gate_results.items() if not status]
    ninety_day_plan = [
        {
            "phase": "Day 1-30",
            "focus": "渠道试点与报价锁定",
            "target": scored_channels[0]["channel"] if scored_channels else "",
        },
        {
            "phase": "Day 31-60",
            "focus": "投放与页面实验",
            "target": "提升转化与缩短回本周期",
        },
        {
            "phase": "Day 61-90",
            "focus": "扩 SKU / 扩渠道",
            "target": "保留 ROI 达标渠道，淘汰低效率渠道",
        },
    ]
    return {
        "gate_results": gate_results,
        "recommendation": recommendation,
        "primary_channel": scored_channels[0]["channel"] if scored_channels else "",
        "secondary_channels": [item["channel"] for item in scored_channels[1:3]],
        "budget_allocation": budget_allocation,
        "priority_channels": scored_channels[:5],
        "top_risks": failed_risks,
        "ninety_day_plan": ninety_day_plan,
        "dtc_fit_score": dtc_metrics.get("dtc_fit_score", 0.0),
        "best_platform_fit_score": platform_metrics.get("best_platform_fit_score", 0.0),
        "b2b_viability_score": b2b_metrics.get("b2b_viability_score", 0.0),
        "traffic_paid_share": traffic_metrics.get("paid_vs_owned", {}).get("paid", 0.0),
        "readiness_score": team_metrics.get("readiness_score", 0.0),
    }
