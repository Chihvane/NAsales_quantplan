from __future__ import annotations

import pandas as pd
import streamlit as st


def render_portfolio_view(payload: dict) -> None:
    st.dataframe(pd.DataFrame(payload["rows"]), use_container_width=True)
