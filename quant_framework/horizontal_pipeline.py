from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_audit_events,
    load_data_dictionary_fields,
    load_decision_rules,
    load_decision_triggers,
    load_evidence_lineage,
    load_master_data_entities,
)
from .models import HorizontalSystemAssumptions, HorizontalSystemDataset


DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS = HorizontalSystemAssumptions(
    required_entity_types=5,
    required_rule_scenarios=5,
    required_entity_type_names=("sku", "channel", "calendar", "price_metric", "supplier"),
    required_rule_scenario_names=("market_entry", "pilot_scale", "sku_exit", "channel_exit", "ad_pause"),
    required_field_groups=("product", "channel", "time", "price"),
    min_dictionary_approval_ratio=0.9,
    min_reproducibility_ratio=0.85,
    min_trigger_resolution_ratio=0.8,
    max_traceback_minutes=30,
)


def build_horizontal_system_dataset_from_directory(data_dir: str | Path) -> HorizontalSystemDataset:
    data_dir = Path(data_dir)
    return HorizontalSystemDataset(
        master_data_entities=load_master_data_entities(data_dir / "master_data_entities.csv"),
        data_dictionary_fields=load_data_dictionary_fields(data_dir / "data_dictionary_fields.csv"),
        evidence_lineage=load_evidence_lineage(data_dir / "evidence_lineage.csv"),
        audit_events=load_audit_events(data_dir / "audit_events.csv"),
        decision_rules=load_decision_rules(data_dir / "decision_rules.csv"),
        decision_triggers=load_decision_triggers(data_dir / "decision_triggers.csv"),
    )
