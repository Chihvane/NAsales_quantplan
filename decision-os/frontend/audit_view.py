from __future__ import annotations

import pandas as pd
import streamlit as st


def render_audit_view(audit_payload: dict, summary_payload: dict, snapshot_payload: dict) -> None:
    st.subheader("Bridge Metadata")
    bridge_meta = snapshot_payload.get("bridge_meta", {})
    st.json(bridge_meta)

    st.subheader("Artifacts")
    st.json(summary_payload.get("artifacts", {}))

    st.subheader("Audit Log")
    logs = audit_payload.get("logs", [])
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)

    reports = summary_payload.get("reports_overview", [])
    if reports:
        st.subheader("Validation Status")
        validation_rows = []
        for report in reports:
            validation = report.get("validation", {})
            validation_rows.append(
                {
                    "Part": report.get("label", ""),
                    "Decision": report.get("decision_signal", ""),
                    "Pass": validation.get("pass_count", 0),
                    "Review": validation.get("review_count", 0),
                    "Fail": validation.get("fail_count", 0),
                }
            )
        st.dataframe(pd.DataFrame(validation_rows), use_container_width=True, hide_index=True)
