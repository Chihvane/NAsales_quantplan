from __future__ import annotations

from pathlib import Path

from .loaders import (
    load_approval_chain,
    load_decision_nodes,
    load_evidence_sources,
    load_field_dictionary,
    load_gate_thresholds,
    load_strategy_assumptions,
    load_update_policies,
)
from .models import Part0Assumptions, Part0Dataset


DEFAULT_PART0_ASSUMPTIONS = Part0Assumptions(
    required_gate_count=5,
    required_decision_domains=6,
    required_policy_scopes=6,
    max_source_age_days=90,
    max_assumption_overdue_days=14,
    minimum_signoff_steps=3,
    required_naming_style="snake_case",
)


def build_part0_dataset_from_directory(data_dir: str | Path) -> Part0Dataset:
    data_dir = Path(data_dir)
    return Part0Dataset(
        decision_nodes=load_decision_nodes(data_dir / "decision_nodes.csv"),
        evidence_sources=load_evidence_sources(data_dir / "evidence_sources.csv"),
        assumptions_register=load_strategy_assumptions(data_dir / "assumptions_register.csv"),
        gate_thresholds=load_gate_thresholds(data_dir / "gate_thresholds.csv"),
        approval_chain=load_approval_chain(data_dir / "approval_chain.csv"),
        update_policies=load_update_policies(data_dir / "update_policies.csv"),
        field_dictionary=load_field_dictionary(data_dir / "field_dictionary.csv"),
    )
