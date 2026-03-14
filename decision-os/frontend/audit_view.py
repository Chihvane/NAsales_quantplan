from __future__ import annotations

import pandas as pd
import streamlit as st


def render_audit_view(payload: dict) -> None:
    st.dataframe(pd.DataFrame(payload["logs"]), use_container_width=True)
