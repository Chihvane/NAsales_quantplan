from __future__ import annotations

import streamlit as st


def render_executive_view(payload: dict) -> None:
    st.subheader("Executive Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Market Factor", payload["market_factor"])
    col2.metric("Gate Status", payload["gate_status"])
    col3.metric("Capital Utilization", payload["capital_utilization_rate"])
    st.metric("Risk Budget Utilization", payload["risk_budget_utilization"])
    st.metric("Expected Profit P50", payload["expected_profit_p50"])
