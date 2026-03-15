from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_compliance_requirements,
    load_logistics_quotes,
    load_evidence_sources,
    load_gate_thresholds,
    load_part3_optimizer_registry,
    load_part3_scenario_registry,
    load_rfq_quotes,
    load_shipment_events,
    load_suppliers,
    load_tariff_tax,
)
from .models import Part3Assumptions, Part3Dataset


DEFAULT_PART3_ASSUMPTIONS = Part3Assumptions(
    target_market="US",
    target_sell_price=699.0,
    target_order_units=500,
    channel_fee_rate=0.15,
    marketing_fee_rate=0.08,
    return_rate=0.04,
    return_cost_per_unit=24.0,
    working_capital_rate=0.02,
)


def build_part3_dataset_from_directory(data_dir: str | Path) -> Part3Dataset:
    data_dir = Path(data_dir)
    return Part3Dataset(
        suppliers=load_suppliers(data_dir / "suppliers.csv"),
        rfq_quotes=load_rfq_quotes(data_dir / "rfq_quotes.csv"),
        compliance_requirements=load_compliance_requirements(data_dir / "compliance_requirements.csv"),
        logistics_quotes=load_logistics_quotes(data_dir / "logistics_quotes.csv"),
        tariff_tax=load_tariff_tax(data_dir / "tariff_tax.csv"),
        shipment_events=load_shipment_events(data_dir / "shipment_events.csv"),
        part3_source_registry=(
            load_evidence_sources(data_dir / "part3_source_registry.csv")
            if (data_dir / "part3_source_registry.csv").exists()
            else []
        ),
        part3_threshold_registry=(
            load_gate_thresholds(data_dir / "part3_threshold_registry.csv")
            if (data_dir / "part3_threshold_registry.csv").exists()
            else []
        ),
        part3_scenario_registry=(
            load_part3_scenario_registry(data_dir / "part3_scenario_registry.csv")
            if (data_dir / "part3_scenario_registry.csv").exists()
            else []
        ),
        part3_optimizer_registry=(
            load_part3_optimizer_registry(data_dir / "part3_optimizer_registry.csv")
            if (data_dir / "part3_optimizer_registry.csv").exists()
            else []
        ),
    )
