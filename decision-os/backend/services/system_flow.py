from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from backend.dependencies import build_market_snapshot


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS_ROOT = WORKSPACE_ROOT / "artifacts" / "full_system_run"
SUMMARY_PATH = ARTIFACTS_ROOT / "full_system_run_summary.json"

if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from examples.run_full_system_chain import run_full_chain  # noqa: E402


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_report_overview(label: str, report_path: str) -> dict[str, Any]:
    path = Path(report_path)
    report = _read_json(path)
    overview = report.get("overview", {})
    confidence_band = report.get("confidence_band", {})
    validation_summary = report.get("validation", {}).get("summary", {})
    return {
        "label": label,
        "report_id": report.get("metadata", {}).get("report_id", ""),
        "path": str(path),
        "decision_signal": overview.get("decision_signal", ""),
        "decision_score": overview.get("decision_score", 0.0),
        "headline_metrics": overview.get("headline_metrics", []),
        "confidence_label": confidence_band.get("label", ""),
        "confidence_score": confidence_band.get("score", 0.0),
        "factor_snapshot_count": len(report.get("factor_snapshots", {})),
        "proxy_usage_flags": report.get("proxy_usage_flags", []),
        "validation": validation_summary,
    }


def _build_reports_overview(summary: dict[str, Any]) -> list[dict[str, Any]]:
    label_map = {
        "part0": "Part 0",
        "horizontal": "Horizontal",
        "part1": "Part 1",
        "part2": "Part 2",
        "part3": "Part 3",
        "part4": "Part 4",
        "part5": "Part 5",
    }
    report_paths = summary.get("report_paths", {})
    rows: list[dict[str, Any]] = []
    for key, label in label_map.items():
        report_path = report_paths.get(key)
        if not report_path:
            continue
        rows.append(_extract_report_overview(label, report_path))
    return rows


def run_full_chain_payload() -> dict[str, Any]:
    result = run_full_chain()
    summary = _read_json(Path(result["summary_json"]))
    return {
        "status": "completed",
        "artifacts": result,
        "summary": summary,
        "reports_overview": _build_reports_overview(summary),
    }


def load_or_run_full_chain_payload(*, refresh: bool = False) -> dict[str, Any]:
    if refresh or not SUMMARY_PATH.exists():
        return run_full_chain_payload()
    summary = _read_json(SUMMARY_PATH)
    return {
        "status": "loaded",
        "artifacts": {
            "summary_json": str(SUMMARY_PATH),
            "bridge_json": summary.get("bridge_paths", {}).get("bundle_json", ""),
            "optimizer_json": str(ARTIFACTS_ROOT / "optimization" / "strategy_optimization.json"),
        },
        "summary": summary,
        "reports_overview": _build_reports_overview(summary),
    }


def build_system_snapshot_payload() -> dict[str, Any]:
    snapshot = build_market_snapshot()
    bridge_bundle = snapshot.get("bridge_bundle", {}) or {}
    gate_inputs = bridge_bundle.get("gate_inputs", {})
    return {
        "source_mode": snapshot.get("source_mode", ""),
        "decision": snapshot.get("decision", ""),
        "factor_score": snapshot.get("factor_score", 0.0),
        "required_capital": snapshot.get("required_capital", 0.0),
        "field_data": snapshot.get("field_data", {}),
        "model_outputs": snapshot.get("model_outputs", {}),
        "capital_state": snapshot.get("capital_state", {}),
        "risk_state": snapshot.get("risk_state", {}),
        "candidate_features": snapshot.get("candidate_features", {}),
        "gate_thresholds": snapshot.get("gate_thresholds", {}),
        "portfolio_rows": snapshot.get("portfolio_rows", []),
        "bridge_meta": {
            "tenant_id": bridge_bundle.get("tenant_id", ""),
            "as_of_date": bridge_bundle.get("as_of_date", ""),
            "report_refs": bridge_bundle.get("report_refs", {}),
            "factor_panel_count": len(bridge_bundle.get("factor_panel", [])),
        },
        "signal_cards": {
            "governance_readiness_score": gate_inputs.get("governance_readiness_score", 0.0),
            "control_tower_score": gate_inputs.get("control_tower_score", 0.0),
            "operating_system_readiness_score": gate_inputs.get("operating_system_readiness_score", 0.0),
            "integrated_factor_score": gate_inputs.get("integrated_factor_score", 0.0),
            "signal_regime": gate_inputs.get("signal_regime", ""),
        },
    }

