from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st


def render_model_view(payload: dict) -> None:
    st.subheader("Model Dashboard")
    st.write(
        {
            "P10": payload["profit_p10"],
            "P50": payload["profit_p50"],
            "P90": payload["profit_p90"],
            "Loss Probability": payload["loss_probability"],
        }
    )
    distribution = pd.DataFrame({"profit": payload["profit_distribution"]})
    chart = (
        alt.Chart(distribution)
        .mark_bar()
        .encode(alt.X("profit:Q", bin=alt.Bin(maxbins=40)), y="count()")
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)
    st.bar_chart(pd.DataFrame({"weight": payload["factor_weights"]}))
