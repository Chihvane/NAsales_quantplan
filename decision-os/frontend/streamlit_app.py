from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

try:
    from frontend.audit_view import render_audit_view
    from frontend.executive import render_executive_view
    from frontend.model_view import render_model_view
    from frontend.portfolio_view import render_portfolio_view
    from frontend.reports_view import render_reports_view
except ModuleNotFoundError:
    from audit_view import render_audit_view
    from executive import render_executive_view
    from model_view import render_model_view
    from portfolio_view import render_portfolio_view
    from reports_view import render_reports_view


WORKSPACE_ROOT = ROOT.parent
FULL_SYSTEM_ROOT = WORKSPACE_ROOT / "artifacts" / "full_system_run"
FULL_SYSTEM_SUMMARY_PATH = FULL_SYSTEM_ROOT / "full_system_run_summary.json"
BRIDGE_BUNDLE_PATH = WORKSPACE_ROOT / "artifacts" / "decision_os_bridge" / "integrated_market_product_bundle.json"

DEFAULT_API_BASE = os.environ.get("DECISION_OS_API_BASE", "")


def _inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg-1: #f7f0df;
          --bg-2: #d9ead3;
          --ink: #18211b;
          --accent: #1f6f50;
          --accent-2: #a44323;
          --panel: rgba(255,255,255,0.72);
          --border: rgba(24,33,27,0.10);
        }
        .stApp {
          background:
            radial-gradient(circle at top left, rgba(164,67,35,0.10), transparent 28%),
            radial-gradient(circle at top right, rgba(31,111,80,0.18), transparent 24%),
            linear-gradient(180deg, var(--bg-1) 0%, #eef3e4 50%, var(--bg-2) 100%);
          color: var(--ink);
        }
        html, body, [class*="css"]  {
          font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
        }
        .hero-card {
          padding: 1rem 1.1rem;
          border-radius: 18px;
          background: var(--panel);
          border: 1px solid var(--border);
          backdrop-filter: blur(10px);
          box-shadow: 0 10px 30px rgba(24,33,27,0.08);
        }
        .hero-kicker {
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--accent-2);
          font-size: 0.75rem;
          font-weight: 700;
        }
        .hero-title {
          font-size: 2rem;
          line-height: 1.05;
          margin: 0.25rem 0 0.35rem 0;
          font-weight: 800;
        }
        .hero-sub {
          color: rgba(24,33,27,0.72);
          font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _request_json(api_base: str, method: str, path: str) -> dict[str, Any]:
    response = requests.request(method, f"{api_base}{path}", timeout=180)
    response.raise_for_status()
    return response.json()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_report_overview(label: str, report_path: str) -> dict[str, Any]:
    report = _read_json(Path(report_path))
    overview = report.get("overview", {})
    confidence_band = report.get("confidence_band", {})
    validation_summary = report.get("validation", {}).get("summary", {})
    return {
        "label": label,
        "report_id": report.get("metadata", {}).get("report_id", ""),
        "path": report_path,
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
        if report_path:
            rows.append(_extract_report_overview(label, report_path))
    return rows


def _build_local_snapshot(summary: dict[str, Any], bridge_bundle: dict[str, Any]) -> dict[str, Any]:
    gate_inputs = bridge_bundle.get("gate_inputs", {})
    field_data = bridge_bundle.get("field_data_proxy", {})
    signal_cards = {
        "governance_readiness_score": gate_inputs.get("governance_readiness_score", 0.0),
        "control_tower_score": gate_inputs.get("control_tower_score", 0.0),
        "operating_system_readiness_score": gate_inputs.get("operating_system_readiness_score", 0.0),
        "integrated_factor_score": gate_inputs.get("integrated_factor_score", 0.0),
        "signal_regime": gate_inputs.get("signal_regime", ""),
    }
    portfolio_rows = []
    for signal in (
        bridge_bundle.get("part4_channel_signals", {}),
        bridge_bundle.get("part5_operating_signals", {}),
    ):
        if signal:
            for key, value in signal.items():
                if isinstance(value, (int, float, str)):
                    portfolio_rows.append({"channel": key, "score": value, "allocated_capital": ""})
            break
    return {
        "source_mode": summary.get("snapshot", {}).get("source_mode", "local_artifacts"),
        "decision": summary.get("snapshot", {}).get("decision", "UNKNOWN"),
        "factor_score": summary.get("snapshot", {}).get("factor_score", gate_inputs.get("integrated_factor_score", 0.0)),
        "required_capital": summary.get("snapshot", {}).get("required_capital", 0.0),
        "field_data": field_data,
        "model_outputs": {
            "profit_p10": gate_inputs.get("channel_margin_rate_var_95", 0.0),
            "profit_p50": gate_inputs.get("channel_risk_adjusted_profit", 0.0),
            "profit_p90": gate_inputs.get("localized_market_selection_score", 0.0),
            "loss_probability": gate_inputs.get("channel_loss_probability_weighted", 0.0),
        },
        "capital_state": {
            "required_capital": summary.get("snapshot", {}).get("required_capital", 0.0),
            "mode": "artifact_proxy",
        },
        "risk_state": {
            "drift_risk_score": gate_inputs.get("drift_risk_score", 0.0),
            "supply_tail_risk_score": gate_inputs.get("supply_tail_risk_score", 0.0),
            "channel_tail_shortfall_severity": gate_inputs.get("channel_tail_shortfall_severity", 0.0),
        },
        "candidate_features": {**field_data, **gate_inputs},
        "gate_thresholds": summary.get("backtest_summary", {}).get("gate_params", {}),
        "portfolio_rows": portfolio_rows,
        "bridge_meta": {
            "tenant_id": bridge_bundle.get("tenant_id", ""),
            "as_of_date": bridge_bundle.get("as_of_date", ""),
            "report_refs": bridge_bundle.get("report_refs", {}),
            "factor_panel_count": len(bridge_bundle.get("factor_panel", [])),
        },
        "signal_cards": signal_cards,
    }


def _load_local_state(*, refresh_summary: bool = False, run_full_chain: bool = False) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary = _read_json(FULL_SYSTEM_SUMMARY_PATH)
    bridge_bundle = _read_json(BRIDGE_BUNDLE_PATH)
    reports_overview = _build_reports_overview(summary)
    payload = {
        "status": "loaded" if not run_full_chain else "artifact_fallback",
        "artifacts": {
            "summary_json": str(FULL_SYSTEM_SUMMARY_PATH),
            "bridge_json": str(BRIDGE_BUNDLE_PATH),
            "optimizer_json": str(FULL_SYSTEM_ROOT / "optimization" / "strategy_optimization.json"),
        },
        "summary": summary,
        "reports_overview": reports_overview,
    }
    snapshot = _build_local_snapshot(summary, bridge_bundle)
    audit = {
        "logs": [
            {
                "timestamp": "artifact-fallback",
                "module": "frontend.local_fallback",
                "action": "load_artifacts",
                "entity_id": "FULL-SYSTEM-RUN",
                "user": "system",
                "version": "local-artifact",
                "status": "ok",
            }
        ]
    }
    return payload, snapshot, audit


def _load_app_state(api_base: str, *, refresh_summary: bool = False) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    api_base = api_base.strip()
    if not api_base:
        return _load_local_state(refresh_summary=refresh_summary)
    try:
        summary = _request_json(api_base, "GET", f"/system/summary?refresh={'true' if refresh_summary else 'false'}")
        snapshot = _request_json(api_base, "GET", "/system/snapshot")
        audit = _request_json(api_base, "GET", "/audit/logs")
        return summary, snapshot, audit
    except requests.RequestException:
        return _load_local_state(refresh_summary=refresh_summary)


def _run_pipeline_state(api_base: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    api_base = api_base.strip()
    if not api_base:
        summary, snapshot, audit = _load_local_state(run_full_chain=True)
        return summary, snapshot, audit, "local"
    try:
        summary = _request_json(api_base, "POST", "/system/run-full-chain")
        snapshot = _request_json(api_base, "GET", "/system/snapshot")
        audit = _request_json(api_base, "GET", "/audit/logs")
        return summary, snapshot, audit, "api"
    except requests.RequestException:
        summary, snapshot, audit = _load_local_state(run_full_chain=True)
        return summary, snapshot, audit, "local"


def _mode_badge(mode: str) -> None:
    st.caption("Mode: API" if mode == "api" else "Mode: Local Fallback")


def main() -> None:
    st.set_page_config(page_title="Decision OS App", layout="wide", initial_sidebar_state="expanded")
    _inject_theme()

    st.markdown(
        """
        <div class="hero-card">
          <div class="hero-kicker">Enterprise Decision OS</div>
          <div class="hero-title">Quant Strategy Control Room</div>
          <div class="hero-sub">
            从 Part0–Part5、横向治理、Bridge、Gate、Backtest 到 Stress Test 的完整交互入口。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Control")
        api_base = st.text_input("API Base", value=DEFAULT_API_BASE)
        page = st.radio(
            "Workspace",
            ["Overview", "Reports", "Backtest", "Gate & Capital", "Audit"],
        )
        run_pipeline = st.button("Run Full Chain", type="primary", width="stretch")
        refresh_summary = st.button("Refresh State", width="stretch")

    if run_pipeline:
        with st.spinner("Running full system chain..."):
            summary, snapshot, audit, mode = _run_pipeline_state(api_base)
    else:
        with st.spinner("Loading system state..."):
            summary, snapshot, audit = _load_app_state(api_base, refresh_summary=refresh_summary)
            mode = "api" if api_base.strip() else "local"

    _mode_badge(mode)

    top = st.columns(5)
    top[0].metric("Source", snapshot.get("source_mode", ""))
    top[1].metric("Gate", snapshot.get("decision", ""))
    top[2].metric("Factor", round(float(snapshot.get("factor_score", 0.0)), 4))
    top[3].metric("Required Capital", round(float(snapshot.get("required_capital", 0.0)), 2))
    top[4].metric("Bridge Factors", snapshot.get("bridge_meta", {}).get("factor_panel_count", 0))

    if page == "Overview":
        render_executive_view(summary, snapshot)
    elif page == "Reports":
        render_reports_view(summary)
    elif page == "Backtest":
        render_portfolio_view(snapshot, summary)
        st.divider()
        render_model_view(snapshot, summary)
    elif page == "Gate & Capital":
        left, right = st.columns([1.2, 1.0])
        with left:
            st.subheader("Candidate Features")
            st.dataframe(
                [{"feature": key, "value": value} for key, value in snapshot.get("candidate_features", {}).items()],
                width="stretch",
                hide_index=True,
            )
        with right:
            st.subheader("Gate Thresholds")
            st.dataframe(
                [{"threshold": key, "value": value} for key, value in snapshot.get("gate_thresholds", {}).items()],
                width="stretch",
                hide_index=True,
            )
            st.subheader("Capital State")
            st.json(snapshot.get("capital_state", {}))
            st.subheader("Risk State")
            st.json(snapshot.get("risk_state", {}))
    else:
        render_audit_view(audit, summary, snapshot)


if __name__ == "__main__":
    main()
