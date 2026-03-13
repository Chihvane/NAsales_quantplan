from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_listing_snapshots,
    load_product_catalog,
    load_reviews,
    load_sold_transactions,
)
from .models import Part2Assumptions, Part2Dataset


DEFAULT_PART2_ASSUMPTIONS = Part2Assumptions(
    leaderboard_size=5,
    sweet_spot_bins=6,
    whitespace_threshold=0.05,
    min_theme_mentions=1,
    min_attribute_support=2,
)


def build_part2_dataset_from_directory(data_dir: str | Path) -> Part2Dataset:
    data_dir = Path(data_dir)
    return Part2Dataset(
        listing_snapshots=load_listing_snapshots(data_dir / "listing_snapshots.csv"),
        sold_transactions=load_sold_transactions(data_dir / "sold_transactions.csv"),
        product_catalog=load_product_catalog(data_dir / "product_catalog.csv"),
        reviews=load_reviews(data_dir / "reviews.csv"),
    )
