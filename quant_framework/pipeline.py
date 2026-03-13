from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_channels,
    load_customer_segments,
    load_listings,
    load_region_demand,
    load_search_trends,
    load_transactions,
)
from .models import MarketSizeAssumptions, Part1Dataset


DEFAULT_ASSUMPTIONS = MarketSizeAssumptions(
    tam=95000000.0,
    online_penetration=0.48,
    importable_share=0.58,
    target_capture_share=0.03,
    sample_coverage=0.28,
)


def build_dataset_from_directory(data_dir: str | Path) -> Part1Dataset:
    data_dir = Path(data_dir)
    return Part1Dataset(
        search_trends=load_search_trends(data_dir / "search_trends.csv"),
        region_demand=load_region_demand(data_dir / "region_demand.csv"),
        customer_segments=load_customer_segments(data_dir / "customer_segments.csv"),
        listings=load_listings(data_dir / "listings.csv"),
        transactions=load_transactions(data_dir / "transactions.csv"),
        channels=load_channels(data_dir / "channels.csv"),
    )
