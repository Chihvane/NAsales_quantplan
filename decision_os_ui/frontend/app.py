from __future__ import annotations

import requests
import streamlit as st

from decision_os_ui.frontend.audit_view import render_audit_view
from decision_os_ui.frontend.executive import render_executive_view
from decision_os_ui.frontend.model_view import render_model_view
from decision_os_ui.frontend.portfolio_view import render_portfolio_view


API_BASE = "http://localhost:8000"


def _get(path: str) -> dict:
    response = requests.get(f"{API_BASE}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="Decision OS v3.0 Dashboard", layout="wide")
    st.title("Decision OS v3.0 Dashboard")

    view = st.sidebar.selectbox(
        "View",
        ["Executive Dashboard", "Model Dashboard", "Portfolio Dashboard", "Audit Dashboard"],
    )

    if st.sidebar.button("Generate Report"):
        report_response = requests.post(f"{API_BASE}/report/generate", timeout=20)
        report_response.raise_for_status()
        st.sidebar.success(f"Report generated: {report_response.json()['paths']['pdf_path']}")

    if view == "Executive Dashboard":
        render_executive_view(_get("/dashboard/executive"))
    elif view == "Model Dashboard":
        render_model_view(_get("/dashboard/model"))
    elif view == "Portfolio Dashboard":
        render_portfolio_view(_get("/dashboard/portfolio"))
    else:
        render_audit_view(_get("/dashboard/audit"))


if __name__ == "__main__":
    main()
