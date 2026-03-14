from __future__ import annotations

import streamlit as st


def render_executive_view(gate_payload: dict, capital_payload: dict) -> None:
    st.metric("Gate Status", gate_payload["decision"])
    st.metric("Factor Score", gate_payload["factor_score"])
    st.metric("Loss Probability", gate_payload["loss_probability"])
    st.json(capital_payload)
