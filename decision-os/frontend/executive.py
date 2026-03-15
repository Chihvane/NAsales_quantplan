from __future__ import annotations

import pandas as pd
import streamlit as st


def render_executive_view(summary_payload: dict, snapshot_payload: dict) -> None:
    summary = summary_payload.get("summary", {})
    snapshot = snapshot_payload
    bridge_inputs = summary.get("bridge_gate_inputs", {})

    hero = st.columns(4)
    hero[0].metric("Current Gate", snapshot.get("decision", ""))
    hero[1].metric("Integrated Factor", round(float(snapshot.get("factor_score", 0.0)), 4))
    hero[2].metric("Backtest Alpha", round(float(summary.get("backtest_summary", {}).get("alpha", 0.0)), 4))
    hero[3].metric("Stress Robustness", round(float(summary.get("stress_summary", {}).get("robustness_score", 0.0)), 4))

    st.subheader("Control Signals")
    control_cols = st.columns(4)
    control_cols[0].metric("Governance", bridge_inputs.get("governance_readiness_score", 0.0))
    control_cols[1].metric("Control Tower", bridge_inputs.get("control_tower_score", 0.0))
    control_cols[2].metric("Operating System", bridge_inputs.get("operating_system_readiness_score", 0.0))
    control_cols[3].metric("Required Capital", round(float(snapshot.get("required_capital", 0.0)), 2))

    st.subheader("Curves")
    backtest_summary = summary.get("backtest_summary", {})
    curves = pd.DataFrame(
        {
            "strategy": backtest_summary.get("strategy_curve", []),
            "benchmark": backtest_summary.get("benchmark_curve", []),
        }
    )
    if not curves.empty:
        st.line_chart(curves, use_container_width=True)

    drawdowns = pd.DataFrame(
        {
            "strategy_drawdown": backtest_summary.get("strategy_drawdown_curve", []),
            "benchmark_drawdown": backtest_summary.get("benchmark_drawdown_curve", []),
        }
    )
    if not drawdowns.empty:
        st.line_chart(drawdowns, use_container_width=True)
