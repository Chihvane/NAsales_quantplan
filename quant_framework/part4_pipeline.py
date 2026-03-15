from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_b2b_accounts,
    load_channel_benchmarks,
    load_channel_rate_cards,
    load_customer_cohorts,
    load_evidence_sources,
    load_experiment_registry,
    load_gate_thresholds,
    load_inventory_positions,
    load_landed_cost_scenarios,
    load_listing_snapshots,
    load_marketing_spend,
    load_part4_optimizer_registry,
    load_part4_stress_registry,
    load_product_catalog,
    load_returns_claims,
    load_sold_transactions,
    load_traffic_sessions,
)
from .models import Part4Assumptions, Part4Dataset


DEFAULT_PART4_ASSUMPTIONS = Part4Assumptions(
    target_payback_months=6.0,
    max_loss_probability=0.25,
    min_contribution_margin_rate=0.08,
    target_repeat_rate=0.18,
    target_inventory_days=45.0,
    risk_penalty_lambda=0.4,
    minimum_experiment_days=7,
)


def build_part4_dataset_from_directory(data_dir: str | Path) -> Part4Dataset:
    data_dir = Path(data_dir)
    return Part4Dataset(
        listing_snapshots=load_listing_snapshots(data_dir / "listing_snapshots.csv"),
        sold_transactions=load_sold_transactions(data_dir / "sold_transactions.csv"),
        product_catalog=load_product_catalog(data_dir / "product_catalog.csv"),
        landed_cost_scenarios=load_landed_cost_scenarios(data_dir / "landed_cost_scenarios.csv"),
        channel_rate_cards=load_channel_rate_cards(data_dir / "channel_rate_cards.csv"),
        marketing_spend=load_marketing_spend(data_dir / "marketing_spend.csv"),
        traffic_sessions=load_traffic_sessions(data_dir / "traffic_sessions.csv"),
        returns_claims=load_returns_claims(data_dir / "returns_claims.csv"),
        customer_cohorts=load_customer_cohorts(data_dir / "customer_cohorts.csv"),
        inventory_positions=load_inventory_positions(data_dir / "inventory_positions.csv"),
        experiment_registry=load_experiment_registry(data_dir / "experiment_registry.csv"),
        b2b_accounts=load_b2b_accounts(data_dir / "b2b_accounts.csv"),
        part4_source_registry=(
            load_evidence_sources(data_dir / "part4_source_registry.csv")
            if (data_dir / "part4_source_registry.csv").exists()
            else []
        ),
        part4_threshold_registry=(
            load_gate_thresholds(data_dir / "part4_threshold_registry.csv")
            if (data_dir / "part4_threshold_registry.csv").exists()
            else []
        ),
        part4_benchmark_registry=(
            load_channel_benchmarks(data_dir / "part4_benchmark_registry.csv")
            if (data_dir / "part4_benchmark_registry.csv").exists()
            else []
        ),
        part4_optimizer_registry=(
            load_part4_optimizer_registry(data_dir / "part4_optimizer_registry.csv")
            if (data_dir / "part4_optimizer_registry.csv").exists()
            else []
        ),
        part4_stress_registry=(
            load_part4_stress_registry(data_dir / "part4_stress_registry.csv")
            if (data_dir / "part4_stress_registry.csv").exists()
            else []
        ),
    )
