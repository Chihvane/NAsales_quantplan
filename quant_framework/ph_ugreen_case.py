from __future__ import annotations

import csv
import json
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from statistics import mean
from typing import Any

import pandas as pd

from .advanced_quant_tools import (
    bayesian_shrinkage_mean,
    entropy_growth_profile,
    fibonacci_retracement_levels,
    recursive_ewma,
)
from .io_utils import write_json
from .loaders import (
    load_consumer_habit_vectors,
    load_market_destination_registry,
    load_region_weight_profiles,
)
from .part4 import build_part4_quant_report
from .part4_pipeline import DEFAULT_PART4_ASSUMPTIONS, build_part4_dataset_from_directory
from .part5 import build_part5_quant_report
from .part5_pipeline import DEFAULT_PART5_ASSUMPTIONS, build_part5_dataset_from_directory
from .time_series_metrics import approximate_entropy, fft_seasonality_features, shannon_entropy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = ROOT / "artifacts" / "ph_ugreen_case"
CASE_SKU = "UGREEN-PH-LIVE-001"
CASE_CHANNEL = "TikTok Shop"
CASE_PLATFORM = "TikTok Shop"


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _duration_seconds(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, timedelta):
        return int(value.total_seconds())
    if isinstance(value, time):
        return value.hour * 3600 + value.minute * 60 + value.second
    if isinstance(value, pd.Timedelta):
        return int(value.total_seconds())
    text = str(value).strip()
    if not text:
        return 0
    parts = text.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = (int(float(part)) for part in parts)
        return hours * 3600 + minutes * 60 + seconds
    return int(float(text))


def _parse_currency(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    normalized = re.sub(r"[^0-9.\\-]", "", str(value))
    return float(normalized or 0.0)


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def load_ph_livestream_excel(path: str | Path) -> pd.DataFrame:
    source_path = Path(path)
    frame = pd.read_excel(source_path)
    rename_map = {
        "数据期间": "period",
        "主播ID": "host_id",
        "序号": "session_rank",
        "直播名称": "live_name",
        "直播开始时间": "live_start_time",
        "时长": "duration",
        "有参与观众数": "engaged_viewers",
        "评论": "comments",
        "加入购物车次数": "add_to_cart",
        "平均观看时长": "avg_watch_time",
        "观众人数": "viewers",
        "订单数(已下订单)": "orders_created",
        "订单数(已确认订单)": "orders_confirmed",
        "已售商品数(已下订单)": "units_created",
        "已售商品数(已确认订单)": "units_confirmed",
        "销售金额(已下订单)": "gmv_created",
        "销售金额(已确认订单)": "gmv_confirmed",
    }
    frame = frame.rename(columns=rename_map)
    frame["live_start_time"] = pd.to_datetime(frame["live_start_time"])
    frame["date"] = frame["live_start_time"].dt.date.astype(str)
    frame["duration_seconds"] = frame["duration"].apply(_duration_seconds)
    frame["avg_watch_seconds"] = frame["avg_watch_time"].apply(_duration_seconds)
    for column in [
        "engaged_viewers",
        "comments",
        "add_to_cart",
        "viewers",
        "orders_created",
        "orders_confirmed",
        "units_created",
        "units_confirmed",
        "host_id",
        "session_rank",
    ]:
        frame[column] = frame[column].fillna(0).astype(int)
    frame["gmv_created"] = frame["gmv_created"].apply(_parse_currency)
    frame["gmv_confirmed"] = frame["gmv_confirmed"].apply(_parse_currency)
    frame["confirmed_unit_price"] = frame.apply(
        lambda row: _safe_divide(float(row["gmv_confirmed"]), float(row["units_confirmed"]), 0.0),
        axis=1,
    )
    frame["confirmed_order_value"] = frame.apply(
        lambda row: _safe_divide(float(row["gmv_confirmed"]), float(row["orders_confirmed"]), 0.0),
        axis=1,
    )
    frame["engagement_rate"] = frame.apply(
        lambda row: _safe_divide(float(row["engaged_viewers"]), float(row["viewers"]), 0.0),
        axis=1,
    )
    frame["confirmed_conversion_rate"] = frame.apply(
        lambda row: _safe_divide(float(row["orders_confirmed"]), float(row["viewers"]), 0.0),
        axis=1,
    )
    frame["cart_rate"] = frame.apply(
        lambda row: _safe_divide(float(row["add_to_cart"]), float(row["viewers"]), 0.0),
        axis=1,
    )
    frame["session_id"] = frame.apply(
        lambda row: f"PHLIVE-{row['live_start_time'].strftime('%Y%m%d%H%M')}-{int(row['session_rank']):03d}",
        axis=1,
    )
    return frame.sort_values("live_start_time").reset_index(drop=True)


def build_daily_livestream_summary(session_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for date_value, group in session_frame.groupby("date", sort=True):
        viewers = int(group["viewers"].sum())
        engaged_viewers = int(group["engaged_viewers"].sum())
        add_to_cart = int(group["add_to_cart"].sum())
        orders_confirmed = int(group["orders_confirmed"].sum())
        units_confirmed = int(group["units_confirmed"].sum())
        gmv_confirmed = float(group["gmv_confirmed"].sum())
        watch_seconds = _safe_divide(
            float((group["avg_watch_seconds"] * group["viewers"]).sum()),
            float(viewers),
            0.0,
        )
        rows.append(
            {
                "date": date_value,
                "session_count": int(group.shape[0]),
                "viewers": viewers,
                "engaged_viewers": engaged_viewers,
                "comments": int(group["comments"].sum()),
                "add_to_cart": add_to_cart,
                "orders_confirmed": orders_confirmed,
                "units_confirmed": units_confirmed,
                "gmv_confirmed": round(gmv_confirmed, 2),
                "avg_watch_seconds": round(watch_seconds, 2),
                "engagement_rate": round(_safe_divide(engaged_viewers, viewers), 4),
                "confirmed_conversion_rate": round(_safe_divide(orders_confirmed, viewers), 4),
                "cart_rate": round(_safe_divide(add_to_cart, viewers), 4),
                "unit_price": round(_safe_divide(gmv_confirmed, units_confirmed), 2),
                "order_value": round(_safe_divide(gmv_confirmed, orders_confirmed), 2),
            }
        )
    return pd.DataFrame(rows)


def _proxy_margin_inputs(daily_frame: pd.DataFrame) -> dict[str, float]:
    sale_price = float(daily_frame["unit_price"].replace(0, pd.NA).dropna().mean())
    if not sale_price:
        sale_price = 499.0
    landed_cost_p50 = round(sale_price * 0.56, 2)
    landed_cost_p10 = round(sale_price * 0.50, 2)
    landed_cost_p90 = round(sale_price * 0.63, 2)
    fee_rate = 0.075
    marketing_rate = 0.055
    reserve_rate = 0.03
    return {
        "sale_price": round(sale_price, 2),
        "list_price": round(sale_price * 1.08, 2),
        "landed_cost_p10": landed_cost_p10,
        "landed_cost_p50": landed_cost_p50,
        "landed_cost_p90": landed_cost_p90,
        "fee_rate": fee_rate,
        "marketing_rate": marketing_rate,
        "reserve_rate": reserve_rate,
        "contribution_margin_rate_proxy": round(1 - 0.56 - fee_rate - marketing_rate - reserve_rate, 4),
    }


def _build_localization_summary(session_frame: pd.DataFrame, daily_frame: pd.DataFrame) -> dict[str, Any]:
    market_registry = {row.market_code: row for row in load_market_destination_registry(ROOT / "examples" / "market_destination_registry.csv")}
    habit_rows = [
        row
        for row in load_consumer_habit_vectors(ROOT / "examples" / "consumer_habit_vectors.csv")
        if row.market_code == "PH"
    ]
    weight_rows = {
        row.market_code: row
        for row in load_region_weight_profiles(ROOT / "examples" / "region_weight_profiles.csv")
        if row.active_flag
    }
    ph_market = market_registry["PH"]
    ph_weight = weight_rows["PH"]
    avg_comments_per_engaged = _safe_divide(float(session_frame["comments"].sum()), float(session_frame["engaged_viewers"].sum()))
    discount_title_ratio = _safe_divide(
        float(session_frame["live_name"].str.contains("sale", case=False, regex=False).sum()),
        float(session_frame.shape[0]),
    )
    cart_abandonment = 1 - _safe_divide(float(session_frame["orders_confirmed"].sum()), float(session_frame["add_to_cart"].sum()), 1.0)
    avg_watch_ratio = _safe_divide(float(daily_frame["avg_watch_seconds"].mean()), 120.0, 0.0)
    observed_vector = {
        "price_sensitivity": round(_clip(0.35 + discount_title_ratio * 0.4 + cart_abandonment * 0.25, 0.0, 1.0), 4),
        "social_proof_dependency": round(_clip(0.25 + avg_comments_per_engaged * 8, 0.0, 1.0), 4),
        "discount_dependency": round(_clip(0.4 + discount_title_ratio * 0.45 + cart_abandonment * 0.2, 0.0, 1.0), 4),
        "content_driven_discovery": round(
            _clip(float(daily_frame["engagement_rate"].mean()) * 0.7 + avg_watch_ratio * 0.3, 0.0, 1.0),
            4,
        ),
        "cross_border_affinity": round(ph_market.cross_border_acceptance, 4),
        "payment_friction_tolerance": round(_clip(ph_market.digital_maturity * 0.82, 0.0, 1.0), 4),
    }
    habit_reference = habit_rows[0] if habit_rows else None
    habit_fit_score = None
    habit_proxy_flag = True
    if habit_reference is not None:
        reference_vector = {
            "price_sensitivity": habit_reference.price_sensitivity,
            "social_proof_dependency": habit_reference.social_proof_dependency,
            "discount_dependency": habit_reference.discount_dependency,
            "content_driven_discovery": habit_reference.content_driven_discovery,
            "cross_border_affinity": habit_reference.cross_border_affinity,
            "payment_friction_tolerance": habit_reference.payment_friction_tolerance,
        }
        mean_abs_gap = mean(abs(observed_vector[key] - reference_vector[key]) for key in reference_vector)
        habit_fit_score = round(_clip(1 - mean_abs_gap, 0.0, 1.0), 4)
    localization_score = round(
        _clip(
            ph_market.digital_maturity * 0.18
            + ph_market.cross_border_acceptance * 0.18
            + (1 - ph_market.logistics_complexity) * 0.12
            + observed_vector["content_driven_discovery"] * ph_weight.factor_weight_channel_efficiency
            + observed_vector["discount_dependency"] * ph_weight.factor_weight_price_realization
            + observed_vector["price_sensitivity"] * ph_weight.factor_weight_customer_fit
            - ph_market.fx_risk * ph_weight.penalty_fx_risk
            - ph_market.logistics_complexity * ph_weight.penalty_logistics_volatility,
            0.0,
            1.0,
        ),
        4,
    )
    return {
        "market_code": "PH",
        "market_name": ph_market.market_name,
        "region_group": ph_market.region_group,
        "analysis_method": ph_market.analysis_method,
        "habit_model_family": ph_market.habit_model_family,
        "regulatory_complexity": ph_market.regulatory_complexity,
        "logistics_complexity": ph_market.logistics_complexity,
        "fx_risk": ph_market.fx_risk,
        "digital_maturity": ph_market.digital_maturity,
        "cross_border_acceptance": ph_market.cross_border_acceptance,
        "region_weight_profile": {
            "profile_id": ph_weight.profile_id,
            "factor_weight_channel_efficiency": ph_weight.factor_weight_channel_efficiency,
            "factor_weight_price_realization": ph_weight.factor_weight_price_realization,
            "geo_fit_weight": ph_weight.geo_fit_weight,
            "habit_fit_weight": ph_weight.habit_fit_weight,
        },
        "observed_habit_vector_proxy": observed_vector,
        "habit_fit_score_proxy": habit_fit_score,
        "habit_proxy_flag": habit_proxy_flag,
        "localization_score": localization_score,
        "localization_notes": [
            "consumer_habit_vector reference is category-mismatched and treated as proxy",
            "Philippines is evaluated with Southeast Asia-specific market profile and weights",
            "livestream commerce behavior is analyzed separately from Europe/Japan/Korea baselines",
        ],
    }


def _build_advanced_signals(daily_frame: pd.DataFrame) -> dict[str, Any]:
    revenue_series = [float(value) for value in daily_frame["gmv_confirmed"].tolist()]
    order_series = [float(value) for value in daily_frame["orders_confirmed"].tolist()]
    prior_mean = mean(revenue_series[: max(len(revenue_series) // 2, 1)]) if revenue_series else 0.0
    observed_mean = mean(revenue_series) if revenue_series else 0.0
    return {
        "revenue_fourier": fft_seasonality_features(revenue_series, sample_spacing=1.0),
        "order_fourier": fft_seasonality_features(order_series, sample_spacing=1.0),
        "revenue_fibonacci": fibonacci_retracement_levels(revenue_series),
        "recursive_revenue": recursive_ewma(revenue_series),
        "entropy_growth": entropy_growth_profile(revenue_series),
        "revenue_shannon_entropy": round(shannon_entropy(revenue_series), 4),
        "revenue_approximate_entropy": round(approximate_entropy(revenue_series), 4),
        "bayesian_revenue_signal": bayesian_shrinkage_mean(
            observed_mean,
            prior_mean=prior_mean,
            prior_strength=max(len(revenue_series) / 2, 1),
            sample_size=len(revenue_series),
        ),
    }


def _build_period_coverage(session_frame: pd.DataFrame) -> dict[str, Any]:
    covered_periods = sorted({str(value) for value in session_frame["period"].dropna().unique().tolist()})
    live_timestamps = session_frame["live_start_time"]
    month_labels = sorted({timestamp.strftime("%Y-%m") for timestamp in live_timestamps})
    first_timestamp = live_timestamps.min()
    last_timestamp = live_timestamps.max()
    return {
        "covered_periods": covered_periods,
        "covered_months": month_labels,
        "source_period_start": first_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "source_period_end": last_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "case_id_suffix": f"{first_timestamp.strftime('%Y-%m')}_to_{last_timestamp.strftime('%Y-%m')}",
    }


def _write_header_only(path: Path, headers: list[str]) -> None:
    _write_rows(path, headers, [])


def _build_case_datasets(session_frame: pd.DataFrame, daily_frame: pd.DataFrame, output_root: Path) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    normalized_path = output_root / "normalized_sessions.csv"
    daily_path = output_root / "daily_livestream_summary.csv"
    session_frame.to_csv(normalized_path, index=False)
    daily_frame.to_csv(daily_path, index=False)

    part4_dir = output_root / "part4_case_data"
    part5_dir = output_root / "part5_case_data"
    part4_dir.mkdir(parents=True, exist_ok=True)
    part5_dir.mkdir(parents=True, exist_ok=True)

    proxy = _proxy_margin_inputs(daily_frame)
    host_id = str(int(session_frame["host_id"].iloc[0]))
    last_timestamp = session_frame["live_start_time"].max()
    first_timestamp = session_frame["live_start_time"].min()
    total_confirmed_units = int(session_frame["units_confirmed"].sum())
    total_confirmed_gmv = float(session_frame["gmv_confirmed"].sum())
    total_confirmed_orders = int(session_frame["orders_confirmed"].sum())
    last_date = str(last_timestamp.date())

    listing_rows = [
        {
            "platform": CASE_PLATFORM,
            "listing_id": "PH-TTS-UGREEN-LIVE",
            "canonical_sku": CASE_SKU,
            "brand": "UGREEN",
            "seller_id": host_id,
            "captured_at": last_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "list_price": proxy["list_price"],
            "sale_price": proxy["sale_price"],
            "currency": "PHP",
            "shipping_fee": 0,
            "rating_avg": 4.7,
            "review_count": int(session_frame["comments"].sum()),
            "sold_count_window": total_confirmed_units,
            "sales_rank": 1,
            "active_flag": "true",
            "seller_type": "brand",
            "fulfillment_type": "cross_border",
        }
    ]
    sold_rows = [
        {
            "platform": CASE_PLATFORM,
            "sold_id": row["session_id"],
            "listing_id": "PH-TTS-UGREEN-LIVE",
            "canonical_sku": CASE_SKU,
            "sold_at": row["live_start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_price": round(_safe_divide(row["gmv_confirmed"], row["units_confirmed"], proxy["sale_price"]), 2),
            "shipping_fee": 0,
            "units": int(row["units_confirmed"]),
            "seller_type": "brand",
        }
        for row in session_frame.to_dict(orient="records")
        if int(row["units_confirmed"]) > 0
    ]
    product_rows = [
        {
            "canonical_sku": CASE_SKU,
            "brand": "UGREEN",
            "category_path": "Consumer Electronics > Mobile Accessories",
            "title": "UGREEN Philippines TikTok Shop Livestream Featured SKU",
            "attribute_tokens": "ugreen,tiktok_shop,livestream,philippines,mobile_accessories",
            "first_available_date": str(first_timestamp.date()),
        }
    ]
    landed_rows = [
        {
            "scenario_id": "PH-LC-001",
            "canonical_sku": CASE_SKU,
            "channel": CASE_CHANNEL,
            "mode": "cross_border_live_commerce_proxy",
            "landed_cost_p10": proxy["landed_cost_p10"],
            "landed_cost_p50": proxy["landed_cost_p50"],
            "landed_cost_p90": proxy["landed_cost_p90"],
            "sell_price": proxy["sale_price"],
            "working_capital_cost": round(proxy["sale_price"] * 0.02, 2),
            "return_reserve": round(proxy["sale_price"] * proxy["reserve_rate"], 2),
            "scenario_confidence_score": 0.42,
        }
    ]
    rate_rows = [
        {
            "channel": CASE_CHANNEL,
            "fee_type": "platform_commission",
            "fee_basis": "revenue",
            "fee_rate": 0.05,
            "fixed_fee": 0,
            "effective_date": last_date,
            "source_ref": "proxy-ph-live-rate",
            "notes": "proxy based on live-commerce fee assumption",
        },
        {
            "channel": CASE_CHANNEL,
            "fee_type": "payment_processing",
            "fee_basis": "revenue",
            "fee_rate": 0.025,
            "fixed_fee": 0,
            "effective_date": last_date,
            "source_ref": "proxy-ph-live-rate",
            "notes": "proxy payment fee",
        },
    ]
    marketing_rows = []
    traffic_rows = []
    kpi_rows = []
    cash_rows = []
    for row in daily_frame.to_dict(orient="records"):
        spend = round(float(row["gmv_confirmed"]) * proxy["marketing_rate"], 2)
        reserve = round(float(row["gmv_confirmed"]) * proxy["reserve_rate"], 2)
        landed_cost = round(float(row["units_confirmed"]) * proxy["landed_cost_p50"], 2)
        fee_cost = round(float(row["gmv_confirmed"]) * proxy["fee_rate"], 2)
        contribution_profit = round(float(row["gmv_confirmed"]) - landed_cost - fee_cost - spend - reserve, 2)
        marketing_rows.append(
            {
                "date": row["date"],
                "channel": CASE_CHANNEL,
                "campaign_id": f"PH-LIVE-{row['date']}",
                "traffic_source": "livestream",
                "spend": spend,
                "impressions": int(round(float(row["viewers"]) * 1.12)),
                "clicks": int(row["engaged_viewers"]),
                "attributed_orders": int(row["orders_confirmed"]),
                "attributed_revenue": round(float(row["gmv_confirmed"]), 2),
            }
        )
        traffic_rows.append(
            {
                "date": row["date"],
                "channel": CASE_CHANNEL,
                "traffic_source": "livestream",
                "sessions": int(row["viewers"]),
                "product_page_views": int(row["engaged_viewers"]),
                "add_to_cart": int(row["add_to_cart"]),
                "checkout_start": min(int(row["add_to_cart"]), max(int(row["orders_confirmed"]), round(int(row["add_to_cart"]) * 0.65))),
                "orders": int(row["orders_confirmed"]),
            }
        )
        kpi_rows.append(
            {
                "date": row["date"],
                "channel": CASE_CHANNEL,
                "revenue": round(float(row["gmv_confirmed"]), 2),
                "contribution_profit": contribution_profit,
                "ad_spend": spend,
                "refunds": 0,
                "disputes": 0,
                "inventory_value": round(proxy["landed_cost_p50"] * max(int(row["units_confirmed"]) * 1.5, 10), 2),
                "operating_status": "healthy" if contribution_profit >= 0 else "watch",
            }
        )
        cash_rows.append(
            {
                "date": row["date"],
                "channel": CASE_CHANNEL,
                "receivable": round(float(row["gmv_confirmed"]) * 0.18, 2),
                "payable": round(landed_cost * 0.35, 2),
                "inventory_cash_lock": round(proxy["landed_cost_p50"] * max(int(row["units_confirmed"]) * 1.5, 10), 2),
                "ad_cash_out": spend,
                "refund_cash_out": 0,
            }
        )
    customer_rows = [
        {
            "cohort_month": first_timestamp.strftime("%Y-%m"),
            "channel": CASE_CHANNEL,
            "customers": total_confirmed_orders,
            "repeat_customers": round(total_confirmed_orders * 0.12),
            "repeat_orders": round(total_confirmed_orders * 0.18),
            "repeat_revenue": round(total_confirmed_gmv * 0.14, 2),
        }
    ]
    inventory_rows = [
        {
            "date": last_date,
            "channel": CASE_CHANNEL,
            "warehouse": "PH-CROSSBORDER",
            "sku_id": CASE_SKU,
            "on_hand_units": max(round(total_confirmed_units * 1.8), 20),
            "inbound_units": max(round(total_confirmed_units * 0.35), 0),
            "sell_through_units": total_confirmed_units,
            "storage_cost": round(max(round(total_confirmed_units * proxy["landed_cost_p50"] * 0.01, 2), 15.0), 2),
        }
    ]
    reorder_rows = [
        {
            "date": last_date,
            "sku_id": CASE_SKU,
            "warehouse": "PH-CROSSBORDER",
            "reorder_point": max(round(total_confirmed_units * 0.35), 10),
            "safety_stock": max(round(total_confirmed_units * 0.18), 6),
            "target_cover_days": 28,
            "planned_units": max(round(total_confirmed_units * 1.1), 24),
            "eta": (last_timestamp + pd.Timedelta(days=18)).strftime("%Y-%m-%d"),
        }
    ]
    pricing_rows = []
    prior_price = None
    for row in daily_frame.to_dict(orient="records"):
        current_price = float(row["unit_price"] or proxy["sale_price"])
        if prior_price is None:
            prior_price = current_price
            continue
        if abs(current_price - prior_price) / max(prior_price, 1.0) >= 0.03:
            pricing_rows.append(
                {
                    "date": row["date"],
                    "channel": CASE_CHANNEL,
                    "sku_id": CASE_SKU,
                    "action_type": "live_price_shift",
                    "old_price": round(prior_price, 2),
                    "new_price": round(current_price, 2),
                    "promo_flag": "true",
                    "bundle_flag": "false",
                    "owner": "livestream_ops",
                }
            )
        prior_price = current_price

    source_rows = [
        {
            "source_id": "PHSRC001",
            "topic": "livestream_sessions",
            "source_name": "UGREEN PH livestream xlsx export",
            "source_type": "platform_export",
            "confidence_grade": "A",
            "collected_at": last_timestamp.strftime("%Y-%m-%d"),
            "freshness_days": 1,
            "version": "v1",
            "status": "active",
            "owner_role": "growth_analyst",
        },
        {
            "source_id": "PHSRC002",
            "topic": "channel_fees",
            "source_name": "PH live commerce proxy fee model",
            "source_type": "proxy_model",
            "confidence_grade": "C",
            "collected_at": last_timestamp.strftime("%Y-%m-%d"),
            "freshness_days": 30,
            "version": "v1",
            "status": "active",
            "owner_role": "finance_ops",
        },
        {
            "source_id": "PHSRC003",
            "topic": "landed_cost",
            "source_name": "UGREEN accessory landed cost proxy",
            "source_type": "proxy_model",
            "confidence_grade": "C",
            "collected_at": last_timestamp.strftime("%Y-%m-%d"),
            "freshness_days": 30,
            "version": "v1",
            "status": "active",
            "owner_role": "supply_analyst",
        },
    ]
    threshold_rows = [
        {
            "gate_id": "PHGATE001",
            "gate_name": "Margin Gate",
            "metric_name": "contribution_margin_rate",
            "operator": ">=",
            "threshold_value": 0.08,
            "unit": "ratio",
            "source_grade_min": "C",
            "approver_role": "strategy_director",
            "decision_if_fail": "pilot_first",
        },
        {
            "gate_id": "PHGATE002",
            "gate_name": "Loss Gate",
            "metric_name": "loss_probability",
            "operator": "<=",
            "threshold_value": 0.30,
            "unit": "ratio",
            "source_grade_min": "C",
            "approver_role": "risk_officer",
            "decision_if_fail": "no_go",
        },
        {
            "gate_id": "PHGATE003",
            "gate_name": "Payback Gate",
            "metric_name": "payback_period_months",
            "operator": "<=",
            "threshold_value": 8,
            "unit": "months",
            "source_grade_min": "C",
            "approver_role": "finance_director",
            "decision_if_fail": "pilot_first",
        },
    ]
    benchmark_rows = [
        {
            "channel": CASE_CHANNEL,
            "benchmark_conversion_rate": round(float(daily_frame["confirmed_conversion_rate"].mean()) * 1.1, 4),
            "benchmark_average_order_value": round(float(daily_frame["order_value"].mean()) * 1.06, 2),
            "benchmark_roas": 2.2,
            "benchmark_cac": round(float(marketing_rows[-1]["spend"]) / max(float(daily_frame["orders_confirmed"].mean()), 1.0), 2),
        }
    ]
    optimizer_rows = [
        {
            "optimizer_id": "PHOPT001",
            "objective_name": "maximize_live_margin_under_proxy_risk",
            "objective_type": "constraint_rank",
            "risk_measure": "loss_probability",
            "max_loss_probability": 0.3,
            "min_contribution_margin_rate": 0.08,
            "min_priority_score": 0.08,
            "max_payback_months": 8,
            "max_paid_share": 0.85,
            "capital_limit": 150000,
            "objective_lambda": 0.35,
            "turnover_penalty_lambda": 0.10,
            "max_single_channel_weight": 0.9,
            "active_flag": 1,
        }
    ]
    stress_rows = [
        {
            "scenario_id": "PHSTR001",
            "scenario_name": "Live Revenue Compression",
            "shock_target": "revenue",
            "shock_multiplier": 0.9,
            "severity": "high",
            "channel_scope": CASE_CHANNEL,
            "active_flag": 1,
            "notes": "Stress weaker live conversion day",
        },
        {
            "scenario_id": "PHSTR002",
            "scenario_name": "Platform Fee Shock",
            "shock_target": "acquisition_cost",
            "shock_multiplier": 1.3,
            "severity": "medium",
            "channel_scope": CASE_CHANNEL,
            "active_flag": 1,
            "notes": "Stress fee or subsidy change",
        },
    ]

    common_targets = [part4_dir, part5_dir]
    for target in common_targets:
        _write_rows(target / "listing_snapshots.csv", list(listing_rows[0].keys()), listing_rows)
        _write_rows(target / "sold_transactions.csv", list(sold_rows[0].keys()), sold_rows)
        _write_rows(target / "product_catalog.csv", list(product_rows[0].keys()), product_rows)
        _write_rows(target / "landed_cost_scenarios.csv", list(landed_rows[0].keys()), landed_rows)
        _write_rows(target / "channel_rate_cards.csv", list(rate_rows[0].keys()), rate_rows)
        _write_rows(target / "marketing_spend.csv", list(marketing_rows[0].keys()), marketing_rows)
        _write_rows(target / "traffic_sessions.csv", list(traffic_rows[0].keys()), traffic_rows)
        _write_rows(target / "customer_cohorts.csv", list(customer_rows[0].keys()), customer_rows)
        _write_rows(target / "inventory_positions.csv", list(inventory_rows[0].keys()), inventory_rows)
        _write_rows(target / "experiment_registry.csv", ["experiment_id", "channel", "hypothesis", "start_date", "end_date", "primary_metric", "mde", "split_ratio", "stop_rule", "status"], [])
        _write_rows(target / "b2b_accounts.csv", ["account_id", "account_type", "region", "discount_rate", "payment_terms_days", "rebate_rate", "annual_target"], [])
        _write_rows(target / "returns_claims.csv", ["date", "channel", "order_id", "sku_id", "return_flag", "refund_amount", "return_reason", "claim_cost", "dispute_flag"], [])

    _write_rows(part4_dir / "part4_source_registry.csv", list(source_rows[0].keys()), source_rows)
    _write_rows(part4_dir / "part4_threshold_registry.csv", list(threshold_rows[0].keys()), threshold_rows)
    _write_rows(part4_dir / "part4_benchmark_registry.csv", list(benchmark_rows[0].keys()), benchmark_rows)
    _write_rows(part4_dir / "part4_optimizer_registry.csv", list(optimizer_rows[0].keys()), optimizer_rows)
    _write_rows(part4_dir / "part4_stress_registry.csv", list(stress_rows[0].keys()), stress_rows)

    _write_rows(part5_dir / "kpi_daily_snapshots.csv", list(kpi_rows[0].keys()), kpi_rows)
    _write_rows(part5_dir / "cash_flow_snapshots.csv", list(cash_rows[0].keys()), cash_rows)
    _write_rows(part5_dir / "reorder_plan.csv", list(reorder_rows[0].keys()), reorder_rows)
    _write_rows(part5_dir / "pricing_actions.csv", ["date", "channel", "sku_id", "action_type", "old_price", "new_price", "promo_flag", "bundle_flag", "owner"], pricing_rows)
    _write_rows(part5_dir / "policy_change_log.csv", ["platform", "policy_type", "effective_date", "source_url", "impact_level", "change_summary"], [])
    _write_rows(part5_dir / "experiment_assignments.csv", ["experiment_id", "entity_id", "variant", "assigned_at", "channel"], [])
    _write_rows(part5_dir / "experiment_metrics.csv", ["experiment_id", "date", "variant", "metric_name", "exposures", "conversions", "value", "ci_low", "ci_high"], [])

    return {
        "normalized_sessions": normalized_path,
        "daily_summary": daily_path,
        "part4_dir": part4_dir,
        "part5_dir": part5_dir,
    }


def run_ph_ugreen_case(excel_path: str | Path, output_root: str | Path | None = None) -> dict[str, str]:
    output_root = Path(output_root or DEFAULT_OUTPUT_ROOT)
    session_frame = load_ph_livestream_excel(excel_path)
    daily_frame = build_daily_livestream_summary(session_frame)
    dataset_paths = _build_case_datasets(session_frame, daily_frame, output_root)

    part4_report = build_part4_quant_report(
        build_part4_dataset_from_directory(dataset_paths["part4_dir"]),
        DEFAULT_PART4_ASSUMPTIONS,
    )
    part5_report = build_part5_quant_report(
        build_part5_dataset_from_directory(dataset_paths["part5_dir"]),
        DEFAULT_PART5_ASSUMPTIONS,
    )

    part4_report_path = write_json(output_root / "part4_report.json", part4_report)
    part5_report_path = write_json(output_root / "part5_report.json", part5_report)

    advanced_signals = _build_advanced_signals(daily_frame)
    localization_summary = _build_localization_summary(session_frame, daily_frame)
    proxy = _proxy_margin_inputs(daily_frame)
    period_coverage = _build_period_coverage(session_frame)
    summary = {
        "case_id": f"UGREEN-PH-LIVESTREAM-{period_coverage['case_id_suffix']}",
        "source_file": str(Path(excel_path)),
        "market_code": "PH",
        "channel": CASE_CHANNEL,
        "source_profile": {
            "session_count": int(session_frame.shape[0]),
            "covered_periods": period_coverage["covered_periods"],
            "covered_months": period_coverage["covered_months"],
            "host_id": str(int(session_frame["host_id"].iloc[0])),
            "first_session_at": period_coverage["source_period_start"],
            "last_session_at": period_coverage["source_period_end"],
            "currency": "PHP",
        },
        "operating_summary": {
            "total_confirmed_gmv": round(float(session_frame["gmv_confirmed"].sum()), 2),
            "total_confirmed_orders": int(session_frame["orders_confirmed"].sum()),
            "total_confirmed_units": int(session_frame["units_confirmed"].sum()),
            "total_viewers": int(session_frame["viewers"].sum()),
            "total_engaged_viewers": int(session_frame["engaged_viewers"].sum()),
            "engagement_rate": round(_safe_divide(float(session_frame["engaged_viewers"].sum()), float(session_frame["viewers"].sum())), 4),
            "confirmed_conversion_rate": round(_safe_divide(float(session_frame["orders_confirmed"].sum()), float(session_frame["viewers"].sum())), 4),
            "cart_rate": round(_safe_divide(float(session_frame["add_to_cart"].sum()), float(session_frame["viewers"].sum())), 4),
            "confirmed_aov": round(_safe_divide(float(session_frame["gmv_confirmed"].sum()), float(session_frame["orders_confirmed"].sum())), 2),
            "confirmed_unit_price": round(_safe_divide(float(session_frame["gmv_confirmed"].sum()), float(session_frame["units_confirmed"].sum())), 2),
            "average_watch_seconds": round(float(daily_frame["avg_watch_seconds"].mean()), 2),
            "contribution_margin_rate_proxy": proxy["contribution_margin_rate_proxy"],
        },
        "advanced_quant_signals": advanced_signals,
        "localization_summary": localization_summary,
        "part4_framework_result": {
            "decision_signal": part4_report.get("overview", {}).get("decision_signal", ""),
            "decision_score": part4_report.get("overview", {}).get("decision_score", 0.0),
            "confidence_band": part4_report.get("confidence_band", {}).get("label", ""),
            "best_channel": part4_report.get("overview", {}).get("headline_metrics", []),
            "factor_snapshots": part4_report.get("factor_snapshots", {}),
        },
        "part5_framework_result": {
            "decision_signal": part5_report.get("overview", {}).get("decision_signal", ""),
            "decision_score": part5_report.get("overview", {}).get("decision_score", 0.0),
            "confidence_band": part5_report.get("confidence_band", {}).get("label", ""),
            "proxy_usage_flags": part5_report.get("proxy_usage_flags", []),
            "factor_snapshots": part5_report.get("factor_snapshots", {}),
        },
        "proxy_assumptions": {
            "fee_rate": proxy["fee_rate"],
            "marketing_rate": proxy["marketing_rate"],
            "return_reserve_rate": proxy["reserve_rate"],
            "landed_cost_proxy_p50": proxy["landed_cost_p50"],
            "notes": [
                "No product-level cost file was provided, so landed cost is proxy-derived from observed unit price",
                "No refund / policy / experiment raw data was provided, so those sections remain proxy-thin",
                "This run is strongest on TikTok Shop livestream channel / operating diagnostics, not on full market sizing",
            ],
        },
    }
    summary_path = write_json(output_root / "ph_ugreen_case_summary.json", summary)
    return {
        "normalized_sessions_csv": str(dataset_paths["normalized_sessions"]),
        "daily_summary_csv": str(dataset_paths["daily_summary"]),
        "part4_report_json": str(part4_report_path),
        "part5_report_json": str(part5_report_path),
        "summary_json": str(summary_path),
    }
