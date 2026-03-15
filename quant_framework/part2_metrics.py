from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
import re

from .metrics import (
    _build_quantile_price_bands,
    _classify_hhi,
    _compute_distribution_summary,
    _match_quantile_price_band,
    _percentile,
    _safe_divide,
)
from .models import (
    ChannelBenchmarkRecord,
    EventLibraryRecord,
    EvidenceSourceRecord,
    GateThresholdRecord,
    ListingSnapshotRecord,
    Part2Assumptions,
    ProductCatalogRecord,
    ReviewRecord,
    SoldTransactionRecord,
)
from .stats_utils import clip


POSITIVE_TERMS = {
    "durable",
    "easy",
    "great",
    "quiet",
    "reliable",
    "solid",
    "value",
    "smooth",
    "fast",
    "fits",
    "powerful",
    "portable",
}

NEGATIVE_TERMS = {
    "broken",
    "damaged",
    "cheap",
    "late",
    "leak",
    "mismatch",
    "noisy",
    "return",
    "smell",
    "weak",
    "failed",
    "scratch",
    "poor",
}

THEME_KEYWORDS = {
    "quality_issue": {"broken", "cheap", "failed", "weak", "scratch", "poor"},
    "shipping_damage": {"damaged", "late", "shipping", "box", "packaging"},
    "fitment_mismatch": {"mismatch", "fit", "fits", "compatibility"},
    "power_performance": {"powerful", "quiet", "noisy", "runtime", "battery", "fuel"},
    "ease_of_use": {"easy", "setup", "start", "portable", "manual"},
    "value_for_money": {"value", "worth", "price", "overpriced"},
}

RATING_BUCKETS = (
    ("lt_4_0", 0.0, 4.0),
    ("4_0_to_4_3", 4.0, 4.3),
    ("4_3_to_4_6", 4.3, 4.6),
    ("gte_4_6", 4.6, None),
)


def _parse_date(value: str) -> datetime.date:
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def _parse_attribute_tokens(value: str) -> list[str]:
    return [token.strip() for token in value.split("|") if token.strip()]


def _latest_snapshots_by_listing(
    listing_snapshots: list[ListingSnapshotRecord],
) -> dict[str, ListingSnapshotRecord]:
    latest: dict[str, ListingSnapshotRecord] = {}
    for snapshot in listing_snapshots:
        current = latest.get(snapshot.listing_id)
        if current is None or snapshot.captured_at > current.captured_at:
            latest[snapshot.listing_id] = snapshot
    return latest


def _realized_price(record: SoldTransactionRecord) -> float:
    return record.transaction_price + record.shipping_fee


def _threshold_lookup(
    threshold_registry: list[GateThresholdRecord] | None,
    metric_names: set[str],
    default_value: float,
) -> float:
    for row in threshold_registry or []:
        if row.metric_name in metric_names:
            return row.threshold_value
    return default_value


def _event_theme_hint(event_name: str) -> str:
    normalized = event_name.lower()
    if "shipping" in normalized or "damage" in normalized or "box" in normalized:
        return "shipping_damage"
    if "reliability" in normalized or "failure" in normalized or "return" in normalized:
        return "quality_issue"
    if "start" in normalized or "manual" in normalized or "setup" in normalized:
        return "ease_of_use"
    if "price" in normalized or "value" in normalized or "overpriced" in normalized:
        return "value_for_money"
    return "quality_issue"


def _build_equal_frequency_price_bands(
    values: list[float],
    band_count: int,
) -> list[tuple[float, float, str]]:
    if not values:
        return []

    unique_values = sorted(set(values))
    if len(unique_values) == 1:
        only = unique_values[0]
        return [(only, only, f"${only:.0f}-${only:.0f}")]

    bin_count = max(2, min(band_count, len(unique_values)))
    edges = [_percentile(values, 100 * index / bin_count) for index in range(bin_count + 1)]
    bands = []
    for index in range(bin_count):
        lower = edges[index]
        upper = edges[index + 1]
        if upper < lower:
            lower, upper = upper, lower
        if upper == lower and index < len(edges) - 2:
            upper = edges[index + 2]
        bands.append((lower, upper, f"${lower:.0f}-${upper:.0f}"))
    return bands


def _weighted_price_band_share(
    values: list[float],
    weights: list[int],
    band_count: int,
    band_reference: list[float] | None = None,
) -> tuple[dict[str, float], dict]:
    if not values:
        return {}, {}
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        label = f"${minimum:.0f}-${maximum:.0f}"
        return {label: 1.0}, {"label": label, "share": 1.0}

    labels = _build_equal_frequency_price_bands(band_reference or values, band_count)
    bucket_weights = [0 for _ in range(len(labels))]

    for value, weight in zip(values, weights):
        matched_index = len(labels) - 1
        for index, (lower, upper, _) in enumerate(labels):
            is_last = index == len(labels) - 1
            if (lower <= value < upper) or (is_last and lower <= value <= upper):
                matched_index = index
                break
        bucket_weights[matched_index] += weight

    total_weight = sum(bucket_weights)
    price_band_share = {
        label: round(_safe_divide(weight, total_weight), 4)
        for (_, _, label), weight in zip(labels, bucket_weights)
    }
    dominant_index = max(range(len(bucket_weights)), key=bucket_weights.__getitem__)
    dominant_label = labels[dominant_index][2]
    dominant_share = round(_safe_divide(bucket_weights[dominant_index], total_weight), 4)
    return price_band_share, {"label": dominant_label, "share": dominant_share}


def _rating_bucket(value: float) -> str:
    for label, lower, upper in RATING_BUCKETS:
        if upper is None and value >= lower:
            return label
        if lower <= value < upper:
            return label
    return "unclassified"


def _lifecycle_rows(
    listing_snapshots: list[ListingSnapshotRecord],
) -> list[dict]:
    if not listing_snapshots:
        return []

    observation_end = max(_parse_date(record.captured_at) for record in listing_snapshots)
    grouped: dict[str, list[ListingSnapshotRecord]] = defaultdict(list)
    for snapshot in listing_snapshots:
        grouped[snapshot.listing_id].append(snapshot)

    lifecycles = []
    for listing_id, records in grouped.items():
        ordered = sorted(records, key=lambda item: item.captured_at)
        first_record = ordered[0]
        last_record = ordered[-1]
        first_seen = _parse_date(first_record.captured_at)
        last_seen = _parse_date(last_record.captured_at)
        event_observed = (not last_record.active_flag) or (last_seen < observation_end)
        end_date = last_seen if event_observed else observation_end
        duration_days = (end_date - first_seen).days + 1
        lifecycles.append(
            {
                "listing_id": listing_id,
                "canonical_sku": first_record.canonical_sku,
                "brand": first_record.brand,
                "first_seen": str(first_seen),
                "last_seen": str(last_seen),
                "duration_days": duration_days,
                "event_observed": event_observed,
                "first_price": first_record.sale_price or first_record.list_price,
                "latest_active_flag": last_record.active_flag,
            }
        )
    return lifecycles


def _kaplan_meier_curve(lifecycles: list[dict]) -> list[dict]:
    if not lifecycles:
        return []

    durations = sorted({row["duration_days"] for row in lifecycles})
    at_risk = len(lifecycles)
    survival = 1.0
    curve = [{"day": 0, "survival_rate": 1.0, "at_risk": at_risk, "deaths": 0, "censored": 0}]

    for duration in durations:
        deaths = sum(
            1 for row in lifecycles if row["duration_days"] == duration and row["event_observed"]
        )
        censored = sum(
            1 for row in lifecycles if row["duration_days"] == duration and not row["event_observed"]
        )
        if at_risk and deaths:
            survival *= 1 - _safe_divide(deaths, at_risk)
        curve.append(
            {
                "day": duration,
                "survival_rate": round(survival, 4),
                "at_risk": at_risk,
                "deaths": deaths,
                "censored": censored,
            }
        )
        at_risk -= deaths + censored
    return curve


def compute_sku_market_structure(
    listing_snapshots: list[ListingSnapshotRecord],
    sold_transactions: list[SoldTransactionRecord],
    assumptions: Part2Assumptions,
) -> dict:
    latest_snapshots = _latest_snapshots_by_listing(listing_snapshots)
    if not sold_transactions:
        return {
            "top_skus": [],
            "top_brands": [],
            "platform_mix": {},
            "top_sku_share": 0.0,
            "brand_hhi": 0.0,
            "brand_concentration_level": "unclassified",
        }

    sku_totals: dict[str, dict] = defaultdict(lambda: {"gmv": 0.0, "units": 0, "platform": "", "brand": ""})
    brand_totals: dict[str, float] = defaultdict(float)
    platform_totals: dict[str, float] = defaultdict(float)
    platform_units: dict[str, int] = defaultdict(int)
    proxy_rows = 0

    for record in sold_transactions:
        realized = _realized_price(record)
        gmv = realized * record.units
        snapshot = latest_snapshots.get(record.listing_id)
        brand = snapshot.brand if snapshot else record.canonical_sku
        sku_totals[record.canonical_sku]["gmv"] += gmv
        sku_totals[record.canonical_sku]["units"] += record.units
        sku_totals[record.canonical_sku]["platform"] = record.platform
        sku_totals[record.canonical_sku]["brand"] = brand
        brand_totals[brand] += gmv
        platform_totals[record.platform] += gmv
        platform_units[record.platform] += record.units
        if record.sold_id.startswith("proxy-"):
            proxy_rows += 1

    total_gmv = sum(platform_totals.values())
    total_units = sum(item["units"] for item in sku_totals.values())
    top_skus = [
        {
            "canonical_sku": sku,
            "brand": payload["brand"],
            "platform": payload["platform"],
            "gmv": round(payload["gmv"], 2),
            "units": payload["units"],
            "gmv_share": round(_safe_divide(payload["gmv"], total_gmv), 4),
            "average_realized_price": round(_safe_divide(payload["gmv"], payload["units"]), 2),
        }
        for sku, payload in sorted(sku_totals.items(), key=lambda item: item[1]["gmv"], reverse=True)[
            : assumptions.leaderboard_size
        ]
    ]
    top_brands = [
        {
            "brand": brand,
            "gmv": round(gmv, 2),
            "gmv_share": round(_safe_divide(gmv, total_gmv), 4),
        }
        for brand, gmv in sorted(brand_totals.items(), key=lambda item: item[1], reverse=True)[
            : assumptions.leaderboard_size
        ]
    ]
    platform_mix = {
        platform: round(_safe_divide(gmv, total_gmv), 4)
        for platform, gmv in sorted(platform_totals.items(), key=lambda item: item[1], reverse=True)
    }
    platform_unit_mix = {
        platform: round(_safe_divide(units, total_units), 4)
        for platform, units in sorted(platform_units.items(), key=lambda item: item[1], reverse=True)
    }

    brand_hhi = sum((_safe_divide(gmv, total_gmv) ** 2) for gmv in brand_totals.values()) * 10000
    cr4 = sum(item["gmv_share"] for item in top_brands[:4])
    top_sku_share = sum(item["gmv_share"] for item in top_skus)
    proxy_share = _safe_divide(proxy_rows, len(sold_transactions))

    return {
        "total_gmv": round(total_gmv, 2),
        "total_units": total_units,
        "platform_mix": platform_mix,
        "platform_unit_mix": platform_unit_mix,
        "top_skus": top_skus,
        "top_brands": top_brands,
        "top_sku_share": round(min(top_sku_share, 1.0), 4),
        "long_tail_share": round(max(0.0, 1 - min(top_sku_share, 1.0)), 4),
        "brand_hhi": round(brand_hhi, 2),
        "brand_concentration_level": _classify_hhi(brand_hhi),
        "brand_cr4": round(min(cr4, 1.0), 4),
        "quantity_observation_mode": "proxy_adjusted" if proxy_share >= 0.5 else "observed_transactions",
        "data_quality": {
            "sku_count": len(sku_totals),
            "brand_count": len(brand_totals),
            "platform_count": len(platform_totals),
            "proxy_transaction_share": round(proxy_share, 4),
        },
    }


def compute_transaction_price_analysis(
    listing_snapshots: list[ListingSnapshotRecord],
    sold_transactions: list[SoldTransactionRecord],
    assumptions: Part2Assumptions,
    benchmark_registry: list[ChannelBenchmarkRecord] | None = None,
    threshold_registry: list[GateThresholdRecord] | None = None,
) -> dict:
    if not sold_transactions:
        return {
            "price_distribution": {},
            "price_band_share": {},
            "sweet_spot_band": {},
            "discount_depth": {},
        }

    latest_snapshots = _latest_snapshots_by_listing(listing_snapshots)
    realized_prices = [_realized_price(record) for record in sold_transactions]
    units = [record.units for record in sold_transactions]
    distribution = _compute_distribution_summary(realized_prices)
    filtered_realized = distribution.get("filtered_values", realized_prices)
    price_band_share, sweet_spot_band = _weighted_price_band_share(
        realized_prices,
        units,
        assumptions.sweet_spot_bins,
        band_reference=filtered_realized,
    )

    seller_discount: dict[str, list[float]] = defaultdict(list)
    weighted_discount_numerator = 0.0
    weighted_units = 0
    listed_total = 0.0
    realized_total = 0.0
    for record in sold_transactions:
        snapshot = latest_snapshots.get(record.listing_id)
        if snapshot is None or snapshot.list_price <= 0:
            continue
        listed_price = snapshot.list_price
        discount_rate = max(
            0.0,
            min(0.9, _safe_divide(listed_price - record.transaction_price, listed_price)),
        )
        seller_discount[record.seller_type].append(discount_rate)
        weighted_discount_numerator += discount_rate * record.units
        weighted_units += record.units
        listed_total += listed_price * record.units
        realized_total += record.transaction_price * record.units

    discount_by_seller_type = {
        seller_type: round(median(values), 4)
        for seller_type, values in sorted(
            seller_discount.items(),
            key=lambda item: median(item[1]),
            reverse=True,
        )
    }

    platform_price: dict[str, dict[str, float]] = defaultdict(lambda: {"revenue": 0.0, "units": 0})
    for record in sold_transactions:
        realized = _realized_price(record)
        platform_price[record.platform]["revenue"] += realized * record.units
        platform_price[record.platform]["units"] += record.units

    benchmark_lookup = {row.channel: row for row in benchmark_registry or []}
    benchmark_gap_by_platform = {}
    for platform, payload in platform_price.items():
        benchmark = benchmark_lookup.get(platform)
        if benchmark is None or payload["units"] <= 0:
            continue
        observed_aov_proxy = _safe_divide(payload["revenue"], payload["units"])
        benchmark_gap_by_platform[platform] = {
            "observed_aov_proxy": round(observed_aov_proxy, 2),
            "benchmark_average_order_value": round(benchmark.benchmark_average_order_value, 2),
            "gap_ratio": round(
                _safe_divide(
                    observed_aov_proxy - benchmark.benchmark_average_order_value,
                    benchmark.benchmark_average_order_value,
                ),
                4,
            ),
        }
    sweet_spot_threshold = _threshold_lookup(
        threshold_registry,
        {"sweet_spot_share", "sweet_spot_fit"},
        0.08,
    )
    realization_floor = _threshold_lookup(
        threshold_registry,
        {"price_realization_rate", "price_realization_floor"},
        0.9,
    )
    sweet_spot_share = sweet_spot_band.get("share", 0.0)
    price_realization_rate = round(_safe_divide(realized_total, listed_total), 4)
    gate_results = {
        "sweet_spot_fit": sweet_spot_share >= sweet_spot_threshold,
        "price_realization_floor": price_realization_rate >= realization_floor,
    }

    return {
        "price_distribution": distribution.get("summary", {}),
        "outlier_analysis": {
            "method": "tukey_iqr_fences_1.5_3.0",
            "fences": distribution.get("iqr_fences", {}),
            "outliers": distribution.get("outliers", {}),
        },
        "price_band_share": price_band_share,
        "sweet_spot_band": sweet_spot_band,
        "average_realized_price": round(
            _safe_divide(sum(price * unit for price, unit in zip(realized_prices, units)), sum(units)),
            2,
        ),
        "median_realized_price": round(_percentile(realized_prices, 50), 2),
        "price_realization_rate": price_realization_rate,
        "discount_depth": {
            "weighted_average_discount_rate": round(
                _safe_divide(weighted_discount_numerator, weighted_units),
                4,
            ),
            "median_discount_rate_by_seller_type": discount_by_seller_type,
        },
        "benchmark_gap_by_platform": benchmark_gap_by_platform,
        "benchmark_coverage_ratio": round(
            _safe_divide(len(benchmark_gap_by_platform), len(platform_price)),
            4,
        ) if platform_price else 0.0,
        "gate_results": gate_results,
    }


def compute_value_gap_analysis(
    listing_snapshots: list[ListingSnapshotRecord],
    sold_transactions: list[SoldTransactionRecord],
    benchmark_registry: list[ChannelBenchmarkRecord] | None = None,
) -> dict:
    latest_snapshots = _latest_snapshots_by_listing(listing_snapshots)
    if not latest_snapshots:
        return {"matrix": [], "strong_value_clusters": [], "risk_clusters": []}

    sku_units: Counter[str] = Counter()
    sku_gmv: dict[str, float] = defaultdict(float)
    for record in sold_transactions:
        sku_units[record.canonical_sku] += record.units
        sku_gmv[record.canonical_sku] += _realized_price(record) * record.units

    snapshots = list(latest_snapshots.values())
    prices = [(item.sale_price or item.list_price) for item in snapshots]
    price_bands = _build_quantile_price_bands(prices)

    cells: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"sku_count": 0, "units": 0, "gmv": 0.0, "price_sum": 0.0, "rating_sum": 0.0}
    )

    for snapshot in snapshots:
        price = snapshot.sale_price or snapshot.list_price
        price_bucket = _match_quantile_price_band(price, price_bands)
        rating_bucket = _rating_bucket(snapshot.rating_avg)
        cell = cells[(price_bucket, rating_bucket)]
        cell["sku_count"] += 1
        cell["units"] += sku_units.get(snapshot.canonical_sku, snapshot.sold_count_window)
        fallback_gmv = (snapshot.sale_price or snapshot.list_price) * snapshot.sold_count_window
        cell["gmv"] += sku_gmv.get(snapshot.canonical_sku, fallback_gmv)
        cell["price_sum"] += price
        cell["rating_sum"] += snapshot.rating_avg

    total_skus = len(snapshots)
    total_units = sum(cell["units"] for cell in cells.values()) or 1
    total_gmv = sum(cell["gmv"] for cell in cells.values()) or 1.0
    matrix = []
    for (price_bucket, rating_bucket), payload in sorted(cells.items()):
        sku_share = _safe_divide(payload["sku_count"], total_skus)
        unit_share = _safe_divide(payload["units"], total_units)
        gmv_share = _safe_divide(payload["gmv"], total_gmv)
        matrix.append(
            {
                "price_bucket": price_bucket,
                "rating_bucket": rating_bucket,
                "sku_count": payload["sku_count"],
                "units": payload["units"],
                "gmv": round(payload["gmv"], 2),
                "sku_share": round(sku_share, 4),
                "unit_share": round(unit_share, 4),
                "gmv_share": round(gmv_share, 4),
                "average_price": round(_safe_divide(payload["price_sum"], payload["sku_count"]), 2),
                "average_rating": round(_safe_divide(payload["rating_sum"], payload["sku_count"]), 2),
                "value_gap": round(gmv_share - sku_share, 4),
                "value_density": round(_safe_divide(gmv_share, sku_share, default=0.0), 4),
            }
        )

    strong_value_clusters = [
        row
        for row in sorted(matrix, key=lambda item: item["value_gap"], reverse=True)
        if row["value_gap"] > 0 and row["rating_bucket"] in {"4_3_to_4_6", "gte_4_6"}
    ][:3]
    risk_clusters = [
        row
        for row in sorted(matrix, key=lambda item: item["value_gap"])
        if row["value_gap"] < 0 and row["price_bucket"] in {"upper_mid", "premium"}
    ][:3]

    top_cluster_gap = max((row["value_gap"] for row in strong_value_clusters), default=0.0)
    risk_cluster_penalty = abs(min((row["value_gap"] for row in risk_clusters), default=0.0))
    benchmark_channels = {row.channel for row in benchmark_registry or []}
    observed_channels = {item.platform for item in latest_snapshots.values()}
    benchmark_coverage_ratio = _safe_divide(
        len(observed_channels & benchmark_channels),
        len(observed_channels),
    ) if observed_channels else 0.0
    value_advantage_score = clip(
        min(len(strong_value_clusters), 3) / 3 * 0.35
        + clip(top_cluster_gap / 0.08, 0.0, 1.0) * 0.4
        + (1 - clip(risk_cluster_penalty / 0.08, 0.0, 1.0)) * 0.15
        + benchmark_coverage_ratio * 0.1,
        0.0,
        1.0,
    )

    return {
        "matrix": matrix,
        "strong_value_clusters": strong_value_clusters,
        "risk_clusters": risk_clusters,
        "benchmark_coverage_ratio": round(benchmark_coverage_ratio, 4),
        "value_advantage_score": round(value_advantage_score, 4),
    }


def compute_attribute_landscape(
    product_catalog: list[ProductCatalogRecord],
    sold_transactions: list[SoldTransactionRecord],
    assumptions: Part2Assumptions,
) -> dict:
    if not product_catalog:
        return {
            "top_attributes": [],
            "whitespace_opportunities": [],
            "brand_feature_coverage": [],
        }

    sku_gmv: dict[str, float] = defaultdict(float)
    for record in sold_transactions:
        sku_gmv[record.canonical_sku] += _realized_price(record) * record.units

    total_gmv = sum(sku_gmv.values()) or 1.0
    total_skus = len(product_catalog)
    attribute_skus: dict[str, set[str]] = defaultdict(set)
    attribute_gmv: dict[str, float] = defaultdict(float)
    brand_features: dict[str, Counter[str]] = defaultdict(Counter)
    brand_sku_count: Counter[str] = Counter()

    for record in product_catalog:
        tokens = _parse_attribute_tokens(record.attribute_tokens)
        brand_sku_count[record.brand] += 1
        for token in tokens:
            attribute_skus[token].add(record.canonical_sku)
            attribute_gmv[token] += sku_gmv.get(record.canonical_sku, 0.0)
            brand_features[record.brand][token] += 1

    top_attributes = []
    for token, skus in attribute_skus.items():
        sku_share = _safe_divide(len(skus), total_skus)
        gmv_share = _safe_divide(attribute_gmv[token], total_gmv)
        support_factor = min(1.0, _safe_divide(len(skus), assumptions.min_attribute_support))
        adjusted_outperformance = (gmv_share - sku_share) * support_factor
        top_attributes.append(
            {
                "attribute": token,
                "sku_count": len(skus),
                "sku_share": round(sku_share, 4),
                "gmv_share": round(gmv_share, 4),
                "outperformance": round(gmv_share - sku_share, 4),
                "adjusted_outperformance": round(adjusted_outperformance, 4),
            }
        )

    top_attributes.sort(key=lambda item: item["adjusted_outperformance"], reverse=True)
    whitespace_opportunities = [
        item
        for item in top_attributes
        if item["sku_count"] >= assumptions.min_attribute_support
        and item["adjusted_outperformance"] >= assumptions.whitespace_threshold
    ][:5]

    most_common_attributes = [item["attribute"] for item in top_attributes[:6]]
    brand_feature_coverage = []
    for brand, feature_counts in sorted(brand_features.items()):
        coverage = {
            attribute: round(_safe_divide(feature_counts.get(attribute, 0), brand_sku_count[brand]), 4)
            for attribute in most_common_attributes
        }
        brand_feature_coverage.append(
            {
                "brand": brand,
                "sku_count": brand_sku_count[brand],
                "coverage": coverage,
            }
        )

    return {
        "top_attributes": top_attributes[:10],
        "whitespace_opportunities": whitespace_opportunities,
        "brand_feature_coverage": brand_feature_coverage,
    }


def compute_review_analytics(
    reviews: list[ReviewRecord],
    assumptions: Part2Assumptions,
    voc_event_registry: list[EventLibraryRecord] | None = None,
    threshold_registry: list[GateThresholdRecord] | None = None,
    source_registry: list[EvidenceSourceRecord] | None = None,
) -> dict:
    if not reviews:
        return {
            "sentiment_mix": {},
            "top_negative_themes": [],
            "top_positive_themes": [],
            "pain_points": [],
        }

    sentiment_counts: Counter[str] = Counter()
    negative_theme_counts: Counter[str] = Counter()
    positive_theme_counts: Counter[str] = Counter()
    theme_negative_score: Counter[str] = Counter()
    rating_buckets: Counter[str] = Counter()

    for review in reviews:
        tokens = _tokenize(review.review_text)
        positive_hits = sum(1 for token in tokens if token in POSITIVE_TERMS)
        negative_hits = sum(1 for token in tokens if token in NEGATIVE_TERMS)
        rating_signal = 1 if review.rating >= 4.5 else -1 if review.rating <= 2.5 else 0
        sentiment_score = positive_hits - negative_hits + rating_signal
        if review.rating >= 4.5:
            rating_buckets["high"] += 1
        elif review.rating <= 2.5:
            rating_buckets["low"] += 1
        else:
            rating_buckets["mid"] += 1

        if sentiment_score > 0:
            sentiment = "positive"
        elif sentiment_score < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        sentiment_counts[sentiment] += 1

        text_blob = " ".join(tokens)
        for theme, keywords in THEME_KEYWORDS.items():
            matched = any(keyword in text_blob for keyword in keywords)
            if not matched:
                continue
            if sentiment == "negative":
                negative_theme_counts[theme] += 1
                theme_negative_score[theme] += abs(sentiment_score) + 1
            elif sentiment == "positive":
                positive_theme_counts[theme] += 1

    total_reviews = len(reviews)
    sentiment_mix = {
        label: round(_safe_divide(count, total_reviews), 4)
        for label, count in (
            ("positive", sentiment_counts.get("positive", 0)),
            ("neutral", sentiment_counts.get("neutral", 0)),
            ("negative", sentiment_counts.get("negative", 0)),
        )
    }
    negative_reviews = max(sentiment_counts.get("negative", 0), 1)

    top_negative_themes = [
        {
            "theme": theme,
            "count": count,
            "share_of_negative_reviews": round(_safe_divide(count, negative_reviews), 4),
        }
        for theme, count in negative_theme_counts.most_common()
        if count >= assumptions.min_theme_mentions
    ][:5]
    top_positive_themes = [
        {
            "theme": theme,
            "count": count,
            "share_of_positive_reviews": round(
                _safe_divide(count, max(sentiment_counts.get("positive", 0), 1)),
                4,
            ),
        }
        for theme, count in positive_theme_counts.most_common()
        if count >= assumptions.min_theme_mentions
    ][:5]
    pain_points = [
        {
            "theme": theme,
            "count": negative_theme_counts[theme],
            "mention_rate": round(_safe_divide(negative_theme_counts[theme], total_reviews), 4),
            "intensity": round(
                _safe_divide(theme_negative_score[theme], total_reviews),
                4,
            ),
        }
        for theme, _ in negative_theme_counts.most_common()
        if negative_theme_counts[theme] >= assumptions.min_theme_mentions
    ][:5]

    active_voc_events = [row for row in voc_event_registry or [] if row.expected_direction == "negative"]
    voc_event_hits = []
    matched_themes = set()
    for event in active_voc_events:
        hinted_theme = _event_theme_hint(event.event_name)
        theme_row = next((row for row in pain_points if row["theme"] == hinted_theme), None)
        mention_rate = theme_row["mention_rate"] if theme_row else 0.0
        intensity = theme_row["intensity"] if theme_row else 0.0
        event_risk = clip(event.severity * 0.6 + mention_rate * 0.25 + intensity * 0.15, 0.0, 1.0)
        if theme_row:
            matched_themes.add(hinted_theme)
        voc_event_hits.append(
            {
                "event_id": event.event_id,
                "event_name": event.event_name,
                "mapped_theme": hinted_theme,
                "matched_theme": theme_row is not None,
                "severity": round(event.severity, 4),
                "mention_rate": round(mention_rate, 4),
                "event_risk": round(event_risk, 4),
            }
        )
    negative_threshold = _threshold_lookup(
        threshold_registry,
        {"negative_sentiment_rate", "voc_negative_rate"},
        0.35,
    )
    negative_rate = sentiment_mix.get("negative", 0.0)
    voc_risk_score = clip(
        negative_rate * 0.45
        + min(len(active_voc_events), 3) / 3 * 0.2
        + max((row["event_risk"] for row in voc_event_hits), default=0.0) * 0.25
        + (1 - _safe_divide(len(matched_themes), len(active_voc_events) or 1)) * 0.1,
        0.0,
        1.0,
    )
    proxy_usage_flags = []
    if not source_registry:
        proxy_usage_flags.append("missing_part2_source_registry")
    if not voc_event_registry:
        proxy_usage_flags.append("missing_voc_event_registry")
    if len(reviews) < 12:
        proxy_usage_flags.append("low_review_sample_size")
    if sentiment_mix.get("negative", 0.0) == 0.0 and not pain_points:
        proxy_usage_flags.append("limited_negative_signal")

    return {
        "sentiment_mix": sentiment_mix,
        "top_negative_themes": top_negative_themes,
        "top_positive_themes": top_positive_themes,
        "pain_points": pain_points,
        "review_count": total_reviews,
        "rating_bucket_mix": {
            bucket: round(_safe_divide(count, total_reviews), 4)
            for bucket, count in sorted(rating_buckets.items())
        },
        "voc_event_hits": voc_event_hits,
        "voc_event_coverage_ratio": round(
            _safe_divide(sum(1 for row in voc_event_hits if row["matched_theme"]), len(voc_event_hits)),
            4,
        ) if voc_event_hits else 0.0,
        "source_registry_count": len(source_registry or []),
        "voc_risk_score": round(voc_risk_score, 4),
        "gate_results": {
            "voc_negative_rate": negative_rate <= negative_threshold,
        },
        "proxy_usage_flags": proxy_usage_flags,
    }


def compute_listing_dynamics(
    listing_snapshots: list[ListingSnapshotRecord],
) -> dict:
    lifecycles = _lifecycle_rows(listing_snapshots)
    if not lifecycles:
        return {
            "listing_count": 0,
            "median_lifetime_days": 0,
            "active_rate": 0.0,
            "survival_curve": [],
            "entry_exit_velocity": [],
            "price_band_exit_risk": {},
        }

    observed_durations = [row["duration_days"] for row in lifecycles if row["event_observed"]]
    duration_source = observed_durations if observed_durations else [row["duration_days"] for row in lifecycles]
    active_rate = _safe_divide(
        sum(1 for row in lifecycles if not row["event_observed"]),
        len(lifecycles),
    )
    survival_curve = _kaplan_meier_curve(lifecycles)
    first_seen_dates = [_parse_date(row["first_seen"]) for row in lifecycles]
    last_seen_dates = [_parse_date(row["last_seen"]) for row in lifecycles]
    observation_span_days = (max(last_seen_dates) - min(first_seen_dates)).days + 1 if lifecycles else 0

    entries: Counter[str] = Counter()
    exits: Counter[str] = Counter()
    for row in lifecycles:
        first_seen = _parse_date(row["first_seen"])
        entry_bucket = f"{first_seen.isocalendar().year}-W{first_seen.isocalendar().week:02d}"
        entries[entry_bucket] += 1
        if row["event_observed"]:
            exit_seen = _parse_date(row["last_seen"])
            exit_bucket = f"{exit_seen.isocalendar().year}-W{exit_seen.isocalendar().week:02d}"
            exits[exit_bucket] += 1

    price_bands = _build_quantile_price_bands([row["first_price"] for row in lifecycles])
    band_totals: Counter[str] = Counter()
    band_exits: Counter[str] = Counter()
    for row in lifecycles:
        price_band = _match_quantile_price_band(row["first_price"], price_bands)
        band_totals[price_band] += 1
        if row["event_observed"]:
            band_exits[price_band] += 1

    entry_exit_velocity = []
    for week in sorted(set(entries) | set(exits)):
        entry_exit_velocity.append(
            {
                "week": week,
                "entries": entries.get(week, 0),
                "exits": exits.get(week, 0),
                "net_change": entries.get(week, 0) - exits.get(week, 0),
            }
        )

    price_band_exit_risk = {
        band: round(_safe_divide(band_exits.get(band, 0), total), 4)
        for band, total in sorted(band_totals.items())
    }

    return {
        "listing_count": len(lifecycles),
        "median_lifetime_days": median(duration_source),
        "active_rate": round(active_rate, 4),
        "censoring_rate": round(active_rate, 4),
        "observation_span_days": observation_span_days,
        "survival_curve": survival_curve,
        "entry_exit_velocity": entry_exit_velocity,
        "price_band_exit_risk": price_band_exit_risk,
    }
