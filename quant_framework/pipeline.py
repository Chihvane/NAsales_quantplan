from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_channel_benchmarks,
    load_channels,
    load_consumer_habit_vectors,
    load_customer_segments,
    load_event_library,
    load_evidence_sources,
    load_gate_thresholds,
    load_listings,
    load_market_destination_registry,
    load_market_size_inputs,
    load_region_demand,
    load_region_weight_profiles,
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
        market_size_inputs=(
            load_market_size_inputs(data_dir / "market_size_inputs.csv")
            if (data_dir / "market_size_inputs.csv").exists()
            else []
        ),
        channel_benchmarks=(
            load_channel_benchmarks(data_dir / "channel_benchmarks.csv")
            if (data_dir / "channel_benchmarks.csv").exists()
            else []
        ),
        event_library=(
            load_event_library(data_dir / "event_library.csv")
            if (data_dir / "event_library.csv").exists()
            else []
        ),
        source_registry=(
            load_evidence_sources(data_dir / "source_registry.csv")
            if (data_dir / "source_registry.csv").exists()
            else []
        ),
        part1_threshold_registry=(
            load_gate_thresholds(data_dir / "part1_threshold_registry.csv")
            if (data_dir / "part1_threshold_registry.csv").exists()
            else []
        ),
        market_destination_registry=(
            load_market_destination_registry(data_dir / "market_destination_registry.csv")
            if (data_dir / "market_destination_registry.csv").exists()
            else []
        ),
        consumer_habit_vectors=(
            load_consumer_habit_vectors(data_dir / "consumer_habit_vectors.csv")
            if (data_dir / "consumer_habit_vectors.csv").exists()
            else []
        ),
        region_weight_profiles=(
            load_region_weight_profiles(data_dir / "region_weight_profiles.csv")
            if (data_dir / "region_weight_profiles.csv").exists()
            else []
        ),
    )
