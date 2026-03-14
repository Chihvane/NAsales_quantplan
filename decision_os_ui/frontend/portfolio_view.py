from __future__ import annotations

import pandas as pd
import streamlit as st


def render_portfolio_view(payload: dict) -> None:
    st.subheader("Portfolio Dashboard")
    frame = pd.DataFrame(payload["portfolio_rows"])
    st.dataframe(frame, use_container_width=True)
    st.metric("Capital Allocation Total", payload["capital_allocation_total"])
    st.metric("Average ROI Proxy", payload["average_roi_proxy"])
    st.bar_chart(frame.set_index("channel")[["allocated_capital", "roi_proxy"]])
