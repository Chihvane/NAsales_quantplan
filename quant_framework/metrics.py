from __future__ import annotations

from collections import defaultdict
from math import sqrt
from statistics import mean, median, pstdev

from .models import (
    ChannelRecord,
    CustomerSegmentRecord,
    ListingRecord,
    MarketSizeAssumptions,
    RegionDemandRecord,
    SearchTrendRecord,
    TransactionRecord,
)
from .stats_utils import (
    clip as _common_clip,
    percentile as _common_percentile,
    round_mapping as _common_round_mapping,
    safe_divide as _common_safe_divide,
)


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    return _common_safe_divide(numerator, denominator, default=default)


def _round_dict(values: dict[str, float], digits: int = 4) -> dict[str, float]:
    return _common_round_mapping(values, digits)


def _clip(value: float, lower: float, upper: float) -> float:
    return _common_clip(value, lower, upper)


def _month_bucket(month_value: str) -> str:
    if len(month_value) >= 7:
        return month_value[5:7]
    return month_value


def _percentile(values: list[float], percentile: float) -> float:
    return _common_percentile(values, percentile)


def _moving_average(series: dict[str, float], window: int) -> dict[str, float]:
    labels = list(series.keys())
    values = list(series.values())
    result = {}
    for index, label in enumerate(labels):
        start = max(0, index - window + 1)
        result[label] = mean(values[start : index + 1])
    return result


def _pearson_correlation(x_values: list[float], y_values: list[float]) -> float:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0
    x_mean = mean(x_values)
    y_mean = mean(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_variance = sum((x - x_mean) ** 2 for x in x_values)
    y_variance = sum((y - y_mean) ** 2 for y in y_values)
    denominator = sqrt(x_variance * y_variance)
    return _safe_divide(numerator, denominator)


def _winsorize_values(
    values: list[float],
    lower_percentile: float = 5,
    upper_percentile: float = 95,
) -> tuple[list[float], dict[str, float]]:
    if not values:
        return [], {"lower_cap": 0.0, "upper_cap": 0.0}
    lower_cap = _percentile(values, lower_percentile)
    upper_cap = _percentile(values, upper_percentile)
    return (
        [_clip(value, lower_cap, upper_cap) for value in values],
        {
            "lower_cap": round(lower_cap, 2),
            "upper_cap": round(upper_cap, 2),
        },
    )


def _compute_distribution_summary(values: list[float]) -> dict:
    if not values:
        return {}

    q1 = _percentile(values, 25)
    med = _percentile(values, 50)
    q3 = _percentile(values, 75)
    p10 = _percentile(values, 10)
    p90 = _percentile(values, 90)
    iqr = q3 - q1

    lower_inner = q1 - 1.5 * iqr
    upper_inner = q3 + 1.5 * iqr
    lower_outer = q1 - 3.0 * iqr
    upper_outer = q3 + 3.0 * iqr

    mild_outliers = [
        value
        for value in values
        if (lower_outer <= value < lower_inner) or (upper_inner < value <= upper_outer)
    ]
    extreme_outliers = [value for value in values if value < lower_outer or value > upper_outer]

    filtered_values = [value for value in values if lower_inner <= value <= upper_inner]
    if not filtered_values:
        filtered_values = list(values)

    return {
        "summary": {
            "min": round(min(values), 2),
            "p10": round(p10, 2),
            "q1": round(q1, 2),
            "median": round(med, 2),
            "q3": round(q3, 2),
            "p90": round(p90, 2),
            "max": round(max(values), 2),
            "average": round(mean(values), 2),
        },
        "iqr_fences": {
            "lower_inner": round(lower_inner, 2),
            "upper_inner": round(upper_inner, 2),
            "lower_outer": round(lower_outer, 2),
            "upper_outer": round(upper_outer, 2),
        },
        "outliers": {
            "mild_count": len(mild_outliers),
            "extreme_count": len(extreme_outliers),
        },
        "filtered_values": filtered_values,
    }


def _build_quantile_price_bands(values: list[float]) -> list[tuple[str, float, float | None]]:
    if not values:
        return []
    q1 = _percentile(values, 25)
    med = _percentile(values, 50)
    q3 = _percentile(values, 75)
    return [
        ("budget", min(values), q1),
        ("mass", q1, med),
        ("upper_mid", med, q3),
        ("premium", q3, None),
    ]


def _weighted_median(values_with_weights: list[tuple[float, int]]) -> float:
    if not values_with_weights:
        return 0.0
    ordered = sorted(values_with_weights, key=lambda item: item[0])
    total_weight = sum(weight for _, weight in ordered)
    midpoint = total_weight / 2
    cumulative = 0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= midpoint:
            return value
    return ordered[-1][0]


def _match_quantile_price_band(
    price: float,
    price_bands: list[tuple[str, float, float | None]],
) -> str:
    for band_name, lower, upper in price_bands:
        if upper is None and price >= lower:
            return band_name
        if lower <= price <= upper:
            return band_name
    return "unclassified"


def _classify_hhi(hhi: float) -> str:
    if hhi < 1000:
        return "unconcentrated"
    if hhi < 1800:
        return "moderately_concentrated"
    return "highly_concentrated"


def _midpoint_change(start_value: float, end_value: float) -> float:
    midpoint = (start_value + end_value) / 2
    return _safe_divide(end_value - start_value, midpoint)


def compute_demand_metrics(
    search_trends: list[SearchTrendRecord],
    region_demand: list[RegionDemandRecord],
) -> dict:
    if not search_trends:
        return {
            "trend": {},
            "seasonality_index": {},
            "regional_share": {},
        }

    monthly_interest: dict[str, list[float]] = defaultdict(list)
    keywords = set()
    for record in search_trends:
        monthly_interest[record.month].append(record.interest)
        keywords.add(record.keyword)

    ordered_months = sorted(monthly_interest)
    monthly_average = {
        month: mean(monthly_interest[month])
        for month in ordered_months
    }
    moving_average_3m = _moving_average(monthly_average, window=3)

    values = list(monthly_average.values())
    first_value = values[0]
    last_value = values[-1]
    periods = max(len(values) - 1, 1)
    annualization_factor = 12 / periods
    cagr = 0.0
    if first_value > 0 and last_value > 0:
        cagr = (last_value / first_value) ** annualization_factor - 1

    last_3 = values[-3:] if len(values) >= 3 else values
    previous_3 = values[-6:-3] if len(values) >= 6 else values[: len(last_3)]
    last_3_avg = mean(last_3)
    previous_3_avg = mean(previous_3) if previous_3 else last_3_avg
    three_month_momentum = _safe_divide(last_3_avg - previous_3_avg, previous_3_avg)

    overall_average = mean(values)
    seasonality_buckets: dict[str, list[float]] = defaultdict(list)
    for month, interest in monthly_average.items():
        seasonality_buckets[_month_bucket(month)].append(interest)
    seasonality_index = {
        month: _safe_divide(mean(bucket_values), overall_average) * 100
        for month, bucket_values in sorted(seasonality_buckets.items())
    }

    regional_total = sum(record.demand_score for record in region_demand)
    regional_share = {
        record.region: _safe_divide(record.demand_score, regional_total)
        for record in sorted(region_demand, key=lambda item: item.demand_score, reverse=True)
    }
    top_regions = dict(list(regional_share.items())[:3])

    peak_months = [
        month for month, index_value in seasonality_index.items() if index_value >= 120
    ]
    low_months = [
        month for month, index_value in seasonality_index.items() if index_value <= 80
    ]

    return {
        "trend": {
            "monthly_average_interest": _round_dict(monthly_average, digits=2),
            "moving_average_3m": _round_dict(moving_average_3m, digits=2),
            "average_interest": round(overall_average, 2),
            "growth_rate": round(_safe_divide(last_value - first_value, first_value), 4),
            "cagr": round(cagr, 4),
            "volatility": round(_safe_divide(pstdev(values), overall_average), 4),
            "three_month_momentum": round(three_month_momentum, 4),
        },
        "seasonality_index": _round_dict(seasonality_index, digits=2),
        "peak_months": peak_months,
        "low_months": low_months,
        "regional_share": _round_dict(regional_share, digits=4),
        "top_regions": _round_dict(top_regions, digits=4),
        "data_quality": {
            "months_covered": len(monthly_average),
            "keyword_count": len(keywords),
            "google_trends_index_range_check": all(0 <= value <= 100 for value in values),
        },
    }


def compute_customer_profile(
    customer_segments: list[CustomerSegmentRecord],
) -> dict[str, dict]:
    grouped: dict[str, list[CustomerSegmentRecord]] = defaultdict(list)
    for record in customer_segments:
        grouped[record.dimension].append(record)

    profile: dict[str, dict] = {}
    for dimension, records in grouped.items():
        dimension_total = sum(record.count for record in records)
        sorted_records = sorted(records, key=lambda item: item.count, reverse=True)
        distribution = [
            {
                "value": record.value,
                "count": record.count,
                "share": round(_safe_divide(record.count, dimension_total), 4),
            }
            for record in sorted_records
        ]
        concentration_hhi = sum(item["share"] ** 2 for item in distribution) * 10000
        profile[dimension] = {
            "distribution": distribution,
            "sample_size": dimension_total,
            "top_segment": distribution[0]["value"],
            "top_segment_share": distribution[0]["share"],
            "segment_concentration_hhi": round(concentration_hhi, 2),
        }
    return profile


def compute_top_down_market_size(
    assumptions: MarketSizeAssumptions,
) -> dict[str, float]:
    online_market = assumptions.tam * assumptions.online_penetration
    sam = online_market * assumptions.importable_share
    som = sam * assumptions.target_capture_share
    return {
        "tam": round(assumptions.tam, 2),
        "online_market": round(online_market, 2),
        "sam": round(sam, 2),
        "serviceable_import_market": round(sam, 2),
        "som": round(som, 2),
    }


def compute_bottom_up_market_size(
    listings: list[ListingRecord],
    sample_coverage: float,
) -> dict:
    if not listings:
        return {}

    monthly_gmv_by_brand: dict[str, float] = defaultdict(float)
    monthly_gmv_by_platform: dict[str, float] = defaultdict(float)
    prices = []
    units = [record.monthly_sales_estimate for record in listings]
    winsorized_units, unit_caps = _winsorize_values(units, lower_percentile=5, upper_percentile=95)
    weighted_price_numerator = 0.0
    weighted_units_denominator = 0.0
    raw_sample_monthly_gmv = 0.0
    review_coverage_count = 0
    rating_coverage_count = 0

    for record, adjusted_units in zip(listings, winsorized_units):
        adjusted_units = min(record.monthly_sales_estimate, adjusted_units)
        raw_sample_monthly_gmv += record.list_price * record.monthly_sales_estimate
        sku_gmv = record.list_price * adjusted_units
        monthly_gmv_by_brand[record.brand] += sku_gmv
        monthly_gmv_by_platform[record.platform] += sku_gmv
        prices.append(record.list_price)
        weighted_price_numerator += record.list_price * adjusted_units
        weighted_units_denominator += adjusted_units
        if record.review_count > 0:
            review_coverage_count += 1
        if record.rating > 0:
            rating_coverage_count += 1

    sample_monthly_gmv = sum(monthly_gmv_by_brand.values())
    estimated_total_monthly_gmv = _safe_divide(sample_monthly_gmv, sample_coverage)
    annual_market_size = estimated_total_monthly_gmv * 12

    brand_market_share = {
        brand: _safe_divide(revenue, sample_monthly_gmv)
        for brand, revenue in sorted(
            monthly_gmv_by_brand.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    }
    platform_market_share = {
        platform: _safe_divide(revenue, sample_monthly_gmv)
        for platform, revenue in sorted(
            monthly_gmv_by_platform.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    }
    brand_shares = list(brand_market_share.values())
    hhi = sum(share ** 2 for share in brand_shares) * 10000

    return {
        "sample_monthly_gmv_raw": round(raw_sample_monthly_gmv, 2),
        "sample_monthly_gmv": round(sample_monthly_gmv, 2),
        "estimated_total_monthly_gmv": round(estimated_total_monthly_gmv, 2),
        "estimated_annual_market_size": round(annual_market_size, 2),
        "weighted_average_list_price": round(
            _safe_divide(weighted_price_numerator, weighted_units_denominator),
            2,
        ),
        "median_list_price": round(median(prices), 2),
        "winsorized_sales_caps": unit_caps,
        "brand_market_share": _round_dict(brand_market_share, digits=4),
        "platform_market_share": _round_dict(platform_market_share, digits=4),
        "top3_concentration_ratio": round(sum(brand_shares[:3]), 4),
        "top5_concentration_ratio": round(sum(brand_shares[:5]), 4),
        "hhi": round(hhi, 2),
        "concentration_level": _classify_hhi(hhi),
        "sample_coverage": round(sample_coverage, 4),
        "data_quality": {
            "listing_count": len(listings),
            "review_coverage_rate": round(_safe_divide(review_coverage_count, len(listings)), 4),
            "rating_coverage_rate": round(_safe_divide(rating_coverage_count, len(listings)), 4),
            "winsorization_ratio": round(
                _safe_divide(raw_sample_monthly_gmv - sample_monthly_gmv, raw_sample_monthly_gmv),
                4,
            ) if raw_sample_monthly_gmv else 0.0,
        },
    }


def compute_channel_metrics(channels: list[ChannelRecord]) -> dict:
    total_revenue = sum(record.revenue for record in channels)
    total_visits = sum(record.visits for record in channels)
    total_orders = sum(record.orders for record in channels)
    total_ad_spend = sum(record.ad_spend for record in channels)
    channel_rows = []
    for record in sorted(channels, key=lambda item: item.revenue, reverse=True):
        conversion_rate = None if record.visits == 0 else round(record.orders / record.visits, 4)
        roas = None if record.ad_spend == 0 else round(record.revenue / record.ad_spend, 2)
        cost_per_order = None if record.orders == 0 or record.ad_spend == 0 else round(
            record.ad_spend / record.orders,
            2,
        )
        channel_rows.append(
            {
                "channel": record.channel,
                "visits": record.visits,
                "orders": record.orders,
                "revenue": round(record.revenue, 2),
                "ad_spend": round(record.ad_spend, 2),
                "traffic_share": round(_safe_divide(record.visits, total_visits), 4),
                "order_share": round(_safe_divide(record.orders, total_orders), 4),
                "revenue_share": round(_safe_divide(record.revenue, total_revenue), 4),
                "conversion_rate": conversion_rate,
                "average_order_value": round(_safe_divide(record.revenue, record.orders), 2),
                "revenue_per_visit": None if record.visits == 0 else round(record.revenue / record.visits, 2),
                "roas": roas,
                "cost_per_order": cost_per_order,
                "efficiency_index": round(
                    _safe_divide(
                        _safe_divide(record.revenue, total_revenue),
                        _safe_divide(record.visits, total_visits),
                    ),
                    4,
                ) if record.visits else None,
                "net_revenue_after_ads": round(record.revenue - record.ad_spend, 2),
            }
        )
    return {
        "totals": {
            "revenue": round(total_revenue, 2),
            "visits": total_visits,
            "orders": total_orders,
            "ad_spend": round(total_ad_spend, 2),
            "overall_conversion_rate": round(_safe_divide(total_orders, total_visits), 4),
            "overall_average_order_value": round(_safe_divide(total_revenue, total_orders), 2),
            "overall_roas": round(_safe_divide(total_revenue, total_ad_spend), 2) if total_ad_spend else None,
        },
        "channels": channel_rows,
    }


def compute_listed_price_metrics(listings: list[ListingRecord]) -> dict:
    if not listings:
        return {}

    prices = [record.list_price for record in listings]
    distribution_summary = _compute_distribution_summary(prices)
    filtered_prices = distribution_summary["filtered_values"]
    inner_fences = distribution_summary["iqr_fences"]
    filtered_records = [
        record
        for record in listings
        if inner_fences["lower_inner"] <= record.list_price <= inner_fences["upper_inner"]
    ] or listings
    ratings = [record.rating for record in filtered_records]
    filtered_price_values = [record.list_price for record in filtered_records]
    distribution_summary = _compute_distribution_summary(prices)
    price_bands = _build_quantile_price_bands(filtered_prices)

    band_distribution: dict[str, int] = defaultdict(int)
    sales_weighted_band_distribution: dict[str, float] = defaultdict(float)
    brand_price_map: dict[str, list[float]] = defaultdict(list)

    for record in listings:
        band_name = _match_quantile_price_band(record.list_price, price_bands)
        band_distribution[band_name] += 1
        sales_weighted_band_distribution[band_name] += max(record.monthly_sales_estimate, 0)
        if inner_fences["lower_inner"] <= record.list_price <= inner_fences["upper_inner"]:
            brand_price_map[record.brand].append(record.list_price)

    sku_count = len(listings)
    total_sales_estimate = sum(max(record.monthly_sales_estimate, 0) for record in listings)
    market_median = distribution_summary["summary"]["median"]
    band_share = {
        band_name: _safe_divide(count, sku_count)
        for band_name, count in sorted(band_distribution.items())
    }
    sales_weighted_band_share = {
        band_name: _safe_divide(units, total_sales_estimate)
        for band_name, units in sorted(sales_weighted_band_distribution.items())
    }
    brand_premium = {
        brand: _safe_divide(median(price_values), market_median, default=1.0) - 1
        for brand, price_values in sorted(
            brand_price_map.items(),
            key=lambda item: median(item[1]),
            reverse=True,
        )
        if price_values
    }

    return {
        "price_summary": {
            "min_price": distribution_summary["summary"]["min"],
            "p10_price": distribution_summary["summary"]["p10"],
            "q1_price": distribution_summary["summary"]["q1"],
            "median_price": distribution_summary["summary"]["median"],
            "q3_price": distribution_summary["summary"]["q3"],
            "p90_price": distribution_summary["summary"]["p90"],
            "max_price": distribution_summary["summary"]["max"],
            "average_price": distribution_summary["summary"]["average"],
            "weighted_average_price": round(
                _weighted_average([(record.list_price, max(record.monthly_sales_estimate, 0)) for record in listings]),
                2,
            ),
        },
        "outlier_analysis": {
            "method": "tukey_iqr_fences_1.5_3.0",
            "fences": distribution_summary["iqr_fences"],
            "counts": distribution_summary["outliers"],
        },
        "price_band_share": _round_dict(band_share, digits=4),
        "sales_weighted_price_band_share": _round_dict(sales_weighted_band_share, digits=4),
        "brand_premium": _round_dict(brand_premium, digits=4),
        "price_rating_correlation": round(_pearson_correlation(filtered_price_values, ratings), 4),
    }


def _weighted_average(values: list[tuple[float, int]]) -> float:
    weighted_sum = sum(value * weight for value, weight in values)
    total_weight = sum(weight for _, weight in values)
    return _safe_divide(weighted_sum, total_weight)


def compute_transaction_metrics(transactions: list[TransactionRecord]) -> dict:
    if not transactions:
        return {}

    weighted_actual_prices = [(record.actual_price, record.units) for record in transactions]
    weighted_list_prices = [(record.list_price, record.units) for record in transactions]
    average_actual_price = _weighted_average(weighted_actual_prices)
    average_list_price = _weighted_average(weighted_list_prices)
    actual_prices = [record.actual_price for record in transactions]
    actual_distribution = _compute_distribution_summary(actual_prices)
    actual_price_bands = _build_quantile_price_bands(actual_distribution["filtered_values"])

    valid_discount_pairs = []
    for record in transactions:
        if record.list_price <= 0:
            continue
        raw_discount = _safe_divide(record.list_price - record.actual_price, record.list_price)
        valid_discount_pairs.append((_clip(raw_discount, 0.0, 0.9), record.units))

    weighted_discount = _weighted_average(valid_discount_pairs)

    units_by_band: dict[str, int] = defaultdict(int)
    for record in transactions:
        units_by_band[_match_quantile_price_band(record.actual_price, actual_price_bands)] += record.units

    total_units = sum(record.units for record in transactions)
    transaction_band_share = {
        band_name: _safe_divide(units, total_units)
        for band_name, units in sorted(units_by_band.items())
    }

    transactions_by_sku: dict[str, list[TransactionRecord]] = defaultdict(list)
    for record in transactions:
        transactions_by_sku[record.sku_id].append(record)

    elasticity_by_sku: dict[str, float] = {}
    elasticity_pairs = []
    valid_elasticity_values: list[tuple[float, int]] = []
    consistent_pairs = 0
    total_pairs = 0

    for sku_id, sku_records in transactions_by_sku.items():
        if len(sku_records) < 2:
            continue
        ordered_records = sorted(sku_records, key=lambda item: item.date)
        sku_elasticities = []
        for start_record, end_record in zip(ordered_records, ordered_records[1:]):
            total_pairs += 1
            price_change_rate = _midpoint_change(start_record.actual_price, end_record.actual_price)
            volume_change_rate = _midpoint_change(start_record.units, end_record.units)
            if price_change_rate == 0:
                continue
            if abs(price_change_rate) < 0.02 or abs(volume_change_rate) < 0.02:
                continue
            elasticity = min(abs(volume_change_rate / price_change_rate), 10.0)
            directionally_consistent = price_change_rate * volume_change_rate < 0
            pair_weight = int(round((start_record.units + end_record.units) / 2))
            elasticity_pairs.append(
                {
                    "sku_id": sku_id,
                    "start_date": start_record.date,
                    "end_date": end_record.date,
                    "price_change_rate": round(price_change_rate, 4),
                    "volume_change_rate": round(volume_change_rate, 4),
                    "elasticity": round(elasticity, 4),
                    "directionally_consistent": directionally_consistent,
                }
            )
            if directionally_consistent:
                consistent_pairs += 1
                valid_elasticity_values.append((elasticity, max(pair_weight, 1)))
            sku_elasticities.append(elasticity)
        if sku_elasticities:
            elasticity_by_sku[sku_id] = mean(sku_elasticities)

    average_elasticity = _weighted_average(valid_elasticity_values) if valid_elasticity_values else 0.0

    return {
        "total_units": total_units,
        "total_gmv": round(sum(record.actual_price * record.units for record in transactions), 2),
        "average_list_price": round(average_list_price, 2),
        "average_actual_price": round(average_actual_price, 2),
        "median_actual_price": actual_distribution["summary"]["median"],
        "weighted_median_actual_price": round(_weighted_median(weighted_actual_prices), 2),
        "price_realization_rate": round(_safe_divide(average_actual_price, average_list_price), 4),
        "average_discount_rate": round(weighted_discount, 4),
        "transaction_price_band_share": _round_dict(transaction_band_share, digits=4),
        "outlier_analysis": {
            "method": "tukey_iqr_fences_1.5_3.0",
            "fences": actual_distribution["iqr_fences"],
            "counts": actual_distribution["outliers"],
        },
        "elasticity_method": "midpoint_absolute",
        "average_price_elasticity": round(average_elasticity, 4),
        "elasticity_consistency_ratio": round(_safe_divide(consistent_pairs, total_pairs), 4),
        "elasticity_observation_count": len(valid_elasticity_values),
        "elasticity_by_sku": _round_dict(elasticity_by_sku, digits=4),
        "elasticity_pairs": elasticity_pairs,
    }
