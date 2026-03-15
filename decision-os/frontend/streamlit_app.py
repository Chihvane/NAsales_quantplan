from __future__ import annotations

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


DEFAULT_API_BASE = os.environ.get("DECISION_OS_API_BASE", "http://localhost:8000")


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


def _load_local_state(*, refresh_summary: bool = False, run_full_chain: bool = False) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from backend.audit.audit_logger import sample_audit_log
    from backend.services.system_flow import (
        build_system_snapshot_payload,
        load_or_run_full_chain_payload,
        run_full_chain_payload,
    )

    if run_full_chain:
        summary = run_full_chain_payload()
    else:
        summary = load_or_run_full_chain_payload(refresh=refresh_summary)
    snapshot = build_system_snapshot_payload()
    audit = {"logs": sample_audit_log()}
    return summary, snapshot, audit


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
