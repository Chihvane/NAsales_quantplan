from __future__ import annotations

import pandas as pd
import streamlit as st


def render_model_view(snapshot_payload: dict, summary_payload: dict) -> None:
    model_outputs = snapshot_payload.get("model_outputs", {})
    signal_cards = snapshot_payload.get("signal_cards", {})
    st.subheader("Simulation")
    cols = st.columns(5)
    cols[0].metric("P10", round(float(model_outputs.get("profit_p10", 0.0)), 2))
    cols[1].metric("P50", round(float(model_outputs.get("profit_p50", 0.0)), 2))
    cols[2].metric("P90", round(float(model_outputs.get("profit_p90", 0.0)), 2))
    cols[3].metric("Loss Prob", round(float(model_outputs.get("loss_probability", 0.0)), 4))
    cols[4].metric("Signal Regime", signal_cards.get("signal_regime", ""))

    profits = model_outputs.get("profits", [])
    if profits:
        st.subheader("Profit Distribution")
        st.bar_chart(pd.DataFrame({"profit": profits}))

    st.subheader("Factor Inputs")
    field_data = snapshot_payload.get("field_data", {})
    if field_data:
        st.dataframe(pd.DataFrame([field_data]), use_container_width=True, hide_index=True)

    st.subheader("Optimization")
    optimization = summary_payload.get("summary", {}).get("optimization_summary", {})
    if optimization:
        st.json(optimization)
