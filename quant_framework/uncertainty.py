from __future__ import annotations

from random import Random
from statistics import mean, median

from .metrics import compute_bottom_up_market_size, compute_transaction_metrics
from .models import (
    ListingRecord,
    ListingSnapshotRecord,
    MarketSizeAssumptions,
    Part2Assumptions,
    Part2Dataset,
    Part4Assumptions,
    Part4Dataset,
    Part3Assumptions,
    Part3Dataset,
    ReviewRecord,
    SoldTransactionRecord,
    TransactionRecord,
)
from .part2_metrics import (
    _lifecycle_rows,
    _realized_price,
    compute_review_analytics,
    compute_sku_market_structure,
)
from .part3_metrics import compute_landed_cost_metrics
from .part3_simulation import run_landed_cost_monte_carlo
from .part4_metrics import compute_channel_pnl_rows
from .part4_simulation import run_part4_roi_monte_carlo
from .stats_utils import percentile as _percentile


def _bootstrap_values(
    values: list[float],
    statistic: str = "mean",
    iterations: int = 500,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not values:
        return {}

    rng = Random(seed)
    sample_size = len(values)
    stats = []
    for _ in range(iterations):
        sample = [values[rng.randrange(sample_size)] for _ in range(sample_size)]
        stats.append(mean(sample) if statistic == "mean" else median(sample))

    point_estimate = mean(values) if statistic == "mean" else median(values)
    return {
        "statistic": statistic,
        "point_estimate": round(point_estimate, 4),
        "ci_lower": round(_percentile(stats, alpha / 2 * 100), 4),
        "ci_upper": round(_percentile(stats, (1 - alpha / 2) * 100), 4),
        "iterations": iterations,
        "alpha": alpha,
    }


def _resample_records(records: list, rng: Random) -> list:
    if not records:
        return []
    sample_size = len(records)
    return [records[rng.randrange(sample_size)] for _ in range(sample_size)]


def bootstrap_market_size_ci(
    listings: list[ListingRecord],
    sample_coverage: float,
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not listings:
        return {}

    rng = Random(seed)
    annual_sizes = []
    weighted_prices = []
    for _ in range(iterations):
        sample = _resample_records(listings, rng)
        result = compute_bottom_up_market_size(sample, sample_coverage)
        annual_sizes.append(result["estimated_annual_market_size"])
        weighted_prices.append(result["weighted_average_list_price"])

    return {
        "annual_market_size": {
            "point_estimate": round(compute_bottom_up_market_size(listings, sample_coverage)["estimated_annual_market_size"], 2),
            "ci_lower": round(_percentile(annual_sizes, alpha / 2 * 100), 2),
            "ci_upper": round(_percentile(annual_sizes, (1 - alpha / 2) * 100), 2),
            "iterations": iterations,
            "alpha": alpha,
        },
        "weighted_average_list_price": {
            "point_estimate": round(compute_bottom_up_market_size(listings, sample_coverage)["weighted_average_list_price"], 2),
            "ci_lower": round(_percentile(weighted_prices, alpha / 2 * 100), 2),
            "ci_upper": round(_percentile(weighted_prices, (1 - alpha / 2) * 100), 2),
            "iterations": iterations,
            "alpha": alpha,
        },
    }


def bootstrap_transaction_ci(
    transactions: list[TransactionRecord],
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not transactions:
        return {}

    rng = Random(seed)
    actual_prices = []
    discount_rates = []
    elasticities = []
    base_metrics = compute_transaction_metrics(transactions)

    for _ in range(iterations):
        sample = _resample_records(transactions, rng)
        sample_metrics = compute_transaction_metrics(sample)
        actual_prices.append(sample_metrics.get("average_actual_price", 0.0))
        discount_rates.append(sample_metrics.get("average_discount_rate", 0.0))
        elasticity = sample_metrics.get("average_price_elasticity")
        if elasticity is not None:
            elasticities.append(elasticity)

    return {
        "average_actual_price": {
            "point_estimate": round(base_metrics.get("average_actual_price", 0.0), 2),
            "ci_lower": round(_percentile(actual_prices, alpha / 2 * 100), 2),
            "ci_upper": round(_percentile(actual_prices, (1 - alpha / 2) * 100), 2),
            "iterations": iterations,
            "alpha": alpha,
        },
        "average_discount_rate": {
            "point_estimate": round(base_metrics.get("average_discount_rate", 0.0), 4),
            "ci_lower": round(_percentile(discount_rates, alpha / 2 * 100), 4),
            "ci_upper": round(_percentile(discount_rates, (1 - alpha / 2) * 100), 4),
            "iterations": iterations,
            "alpha": alpha,
        },
        "average_price_elasticity": {
            "point_estimate": round(base_metrics.get("average_price_elasticity", 0.0), 4),
            "ci_lower": round(_percentile(elasticities, alpha / 2 * 100), 4),
            "ci_upper": round(_percentile(elasticities, (1 - alpha / 2) * 100), 4),
            "iterations": iterations,
            "alpha": alpha,
        },
    }


def build_part1_uncertainty_snapshot(
    listings: list[ListingRecord],
    transactions: list[TransactionRecord],
    assumptions: MarketSizeAssumptions,
) -> dict:
    return {
        "market_size": bootstrap_market_size_ci(
            listings,
            assumptions.sample_coverage,
        ),
        "transactions": bootstrap_transaction_ci(transactions),
        "listed_price_median": _bootstrap_values(
            [record.list_price for record in listings],
            statistic="median",
        ),
    }


def bootstrap_part2_market_share_ci(
    listing_snapshots: list[ListingSnapshotRecord],
    sold_transactions: list[SoldTransactionRecord],
    assumptions: Part2Assumptions,
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not sold_transactions:
        return {}

    rng = Random(seed)
    share_samples = []
    for _ in range(iterations):
        sample = _resample_records(sold_transactions, rng)
        metrics = compute_sku_market_structure(listing_snapshots, sample, assumptions)
        share_samples.append(metrics.get("top_sku_share", 0.0))

    base = compute_sku_market_structure(listing_snapshots, sold_transactions, assumptions)
    return {
        "top_sku_share": {
            "point_estimate": round(base.get("top_sku_share", 0.0), 4),
            "ci_lower": round(_percentile(share_samples, alpha / 2 * 100), 4),
            "ci_upper": round(_percentile(share_samples, (1 - alpha / 2) * 100), 4),
            "iterations": iterations,
            "alpha": alpha,
        }
    }


def bootstrap_part2_price_ci(
    sold_transactions: list[SoldTransactionRecord],
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    realized_prices = [_realized_price(record) for record in sold_transactions]
    return {
        "median_realized_price": _bootstrap_values(
            realized_prices,
            statistic="median",
            iterations=iterations,
            alpha=alpha,
            seed=seed,
        ),
    }


def bootstrap_part2_review_ci(
    reviews: list[ReviewRecord],
    assumptions: Part2Assumptions,
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not reviews:
        return {}

    rng = Random(seed)
    negativity = []
    for _ in range(iterations):
        sample = _resample_records(reviews, rng)
        analytics = compute_review_analytics(sample, assumptions)
        negativity.append(analytics.get("sentiment_mix", {}).get("negative", 0.0))

    base = compute_review_analytics(reviews, assumptions)
    return {
        "negative_review_rate": {
            "point_estimate": round(base.get("sentiment_mix", {}).get("negative", 0.0), 4),
            "ci_lower": round(_percentile(negativity, alpha / 2 * 100), 4),
            "ci_upper": round(_percentile(negativity, (1 - alpha / 2) * 100), 4),
            "iterations": iterations,
            "alpha": alpha,
        }
    }


def bootstrap_part2_lifetime_ci(
    listing_snapshots: list[ListingSnapshotRecord],
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    lifecycles = _lifecycle_rows(listing_snapshots)
    durations = [row["duration_days"] for row in lifecycles]
    return {
        "median_lifetime_days": _bootstrap_values(
            durations,
            statistic="median",
            iterations=iterations,
            alpha=alpha,
            seed=seed,
        ),
    }


def build_part2_uncertainty_snapshot(
    dataset: Part2Dataset,
    assumptions: Part2Assumptions,
) -> dict:
    return {
        "market_structure": bootstrap_part2_market_share_ci(
            dataset.listing_snapshots,
            dataset.sold_transactions,
            assumptions,
        ),
        "price": bootstrap_part2_price_ci(dataset.sold_transactions),
        "reviews": bootstrap_part2_review_ci(dataset.reviews, assumptions),
        "listing_dynamics": bootstrap_part2_lifetime_ci(dataset.listing_snapshots),
    }


def build_part3_uncertainty_snapshot(
    dataset: Part3Dataset,
    assumptions: Part3Assumptions,
    iterations: int = 400,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    if not dataset.rfq_quotes:
        return {}

    rng = Random(seed)
    landed_costs = []
    net_margins = []
    margin_rates = []

    for _ in range(iterations):
        sample_quotes = _resample_records(dataset.rfq_quotes, rng)
        sample_routes = _resample_records(dataset.logistics_quotes, rng)
        metrics = compute_landed_cost_metrics(
            sample_quotes,
            sample_routes,
            dataset.compliance_requirements,
            dataset.tariff_tax,
            assumptions,
            dataset.suppliers,
        )
        best = metrics.get("best_scenario", {})
        if best:
            landed_costs.append(best.get("landed_cost", 0.0))
            net_margins.append(best.get("net_margin", 0.0))
            margin_rates.append(best.get("net_margin_rate", 0.0))

    base = compute_landed_cost_metrics(
        dataset.rfq_quotes,
        dataset.logistics_quotes,
        dataset.compliance_requirements,
        dataset.tariff_tax,
        assumptions,
        dataset.suppliers,
    )
    best = base.get("best_scenario", {})
    route_volatility = 0.2
    for route in dataset.logistics_quotes:
        if route.route_id == best.get("route_id"):
            route_volatility = route.volatility_score
            break
    monte_carlo = run_landed_cost_monte_carlo(
        best,
        assumptions,
        route_volatility_score=route_volatility,
        iterations=max(iterations * 3, 1200),
        seed=seed,
    )
    return {
        "best_landed_cost": {
            "point_estimate": round(best.get("landed_cost", 0.0), 2),
            "ci_lower": round(_percentile(landed_costs, alpha / 2 * 100), 2),
            "ci_upper": round(_percentile(landed_costs, (1 - alpha / 2) * 100), 2),
            "iterations": iterations,
            "alpha": alpha,
        },
        "best_net_margin": {
            "point_estimate": round(best.get("net_margin", 0.0), 2),
            "ci_lower": round(_percentile(net_margins, alpha / 2 * 100), 2),
            "ci_upper": round(_percentile(net_margins, (1 - alpha / 2) * 100), 2),
            "iterations": iterations,
            "alpha": alpha,
        },
        "best_net_margin_rate": {
            "point_estimate": round(best.get("net_margin_rate", 0.0), 4),
            "ci_lower": round(_percentile(margin_rates, alpha / 2 * 100), 4),
            "ci_upper": round(_percentile(margin_rates, (1 - alpha / 2) * 100), 4),
            "iterations": iterations,
            "alpha": alpha,
        },
        "monte_carlo": monte_carlo,
    }


def build_part4_uncertainty_snapshot(
    dataset: Part4Dataset,
    assumptions: Part4Assumptions,
    iterations: int = 1200,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    channel_rows = compute_channel_pnl_rows(dataset, assumptions)
    if not channel_rows:
        return {}

    monte_carlo = run_part4_roi_monte_carlo(
        channel_rows,
        assumptions,
        iterations=iterations,
        seed=seed,
    )
    margin_rates = [row.get("contribution_margin_rate", 0.0) for row in channel_rows]
    payback_periods = [row.get("payback_period_months", 0.0) for row in channel_rows if row.get("payback_period_months", 0.0) > 0]
    repeat_rates = [row.get("repeat_rate", 0.0) for row in channel_rows]
    return {
        "channel_margin_rate": _bootstrap_values(
            margin_rates,
            statistic="mean",
            iterations=max(iterations // 3, 400),
            alpha=alpha,
            seed=seed,
        ),
        "channel_payback_period": _bootstrap_values(
            payback_periods,
            statistic="median",
            iterations=max(iterations // 3, 400),
            alpha=alpha,
            seed=seed,
        )
        if payback_periods
        else {},
        "channel_repeat_rate": _bootstrap_values(
            repeat_rates,
            statistic="mean",
            iterations=max(iterations // 3, 400),
            alpha=alpha,
            seed=seed,
        ),
        "roi_monte_carlo": monte_carlo,
    }
