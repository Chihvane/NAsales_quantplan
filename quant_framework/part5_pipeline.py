from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_b2b_accounts,
    load_cash_flow_snapshots,
    load_channel_rate_cards,
    load_customer_cohorts,
    load_experiment_assignments,
    load_experiment_metrics,
    load_experiment_registry,
    load_inventory_positions,
    load_kpi_daily_snapshots,
    load_landed_cost_scenarios,
    load_listing_snapshots,
    load_marketing_spend,
    load_policy_change_log,
    load_pricing_actions,
    load_product_catalog,
    load_reorder_plan,
    load_returns_claims,
    load_sold_transactions,
    load_traffic_sessions,
)
from .models import Part5Assumptions, Part5Dataset


DEFAULT_PART5_ASSUMPTIONS = Part5Assumptions(
    target_health_score=0.65,
    min_contribution_margin_rate=0.08,
    max_refund_rate=0.1,
    max_dispute_rate=0.03,
    target_inventory_days=45.0,
    target_repeat_rate=0.18,
    min_experiment_weeks=1,
    max_budget_burn_ratio=0.4,
    budget_allocation_max_share=0.55,
    experiment_ship_threshold=0.97,
    experiment_loss_threshold=0.05,
    experiment_futility_lower=0.35,
    experiment_futility_upper=0.65,
    experiment_effect_floor_share_of_mde=0.5,
)


def build_part5_dataset_from_directory(data_dir: str | Path) -> Part5Dataset:
    data_dir = Path(data_dir)
    return Part5Dataset(
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
        experiment_assignments=load_experiment_assignments(data_dir / "experiment_assignments.csv")
        if (data_dir / "experiment_assignments.csv").exists()
        else [],
        experiment_metrics=load_experiment_metrics(data_dir / "experiment_metrics.csv")
        if (data_dir / "experiment_metrics.csv").exists()
        else [],
        b2b_accounts=load_b2b_accounts(data_dir / "b2b_accounts.csv"),
        kpi_daily_snapshots=load_kpi_daily_snapshots(data_dir / "kpi_daily_snapshots.csv"),
        pricing_actions=load_pricing_actions(data_dir / "pricing_actions.csv"),
        reorder_plan=load_reorder_plan(data_dir / "reorder_plan.csv"),
        policy_change_log=load_policy_change_log(data_dir / "policy_change_log.csv"),
        cash_flow_snapshots=load_cash_flow_snapshots(data_dir / "cash_flow_snapshots.csv"),
    )
