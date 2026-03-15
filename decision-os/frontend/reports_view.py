from __future__ import annotations

import pandas as pd
import streamlit as st


def render_reports_view(payload: dict) -> None:
    reports = payload.get("reports_overview", [])
    if not reports:
        st.warning("No reports available yet.")
        return

    st.subheader("Part Reports")
    summary_rows = []
    for report in reports:
        summary_rows.append(
            {
                "Part": report.get("label", ""),
                "Decision": report.get("decision_signal", ""),
                "Score": report.get("decision_score", 0.0),
                "Confidence": report.get("confidence_label", ""),
                "Factor Count": report.get("factor_snapshot_count", 0),
                "Validation Pass": report.get("validation", {}).get("pass_count", 0),
            }
        )
    st.dataframe(pd.DataFrame(summary_rows), width="stretch", hide_index=True)

    for report in reports:
        with st.expander(f"{report.get('label', '')} · {report.get('decision_signal', '')}", expanded=False):
            headline_metrics = report.get("headline_metrics", [])
            if headline_metrics:
                cols = st.columns(min(4, len(headline_metrics)))
                for idx, metric in enumerate(headline_metrics[:4]):
                    cols[idx].metric(metric.get("label", metric.get("key", "")), metric.get("value", 0.0))
            st.caption(report.get("path", ""))
            proxy_flags = report.get("proxy_usage_flags", [])
            if proxy_flags:
                st.write("Proxy Flags")
                st.write(", ".join(proxy_flags))
