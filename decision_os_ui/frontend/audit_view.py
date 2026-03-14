from __future__ import annotations

import pandas as pd
import streamlit as st


def render_audit_view(payload: dict) -> None:
    st.subheader("Audit Dashboard")
    if payload["recent_decisions"]:
        st.write("Recent Decisions")
        st.dataframe(pd.DataFrame(payload["recent_decisions"]), use_container_width=True)
    if payload["recent_reports"]:
        st.write("Recent Reports")
        st.dataframe(pd.DataFrame(payload["recent_reports"]), use_container_width=True)
    if payload["audit_events"]:
        st.write("Audit Events")
        st.dataframe(pd.DataFrame(payload["audit_events"]), use_container_width=True)
