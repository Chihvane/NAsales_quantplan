from __future__ import annotations

import requests
import streamlit as st

from frontend.audit_view import render_audit_view
from frontend.executive import render_executive_view
from frontend.model_view import render_model_view
from frontend.portfolio_view import render_portfolio_view


API_BASE = "http://localhost:8000"


def _get(path: str) -> dict:
    response = requests.get(f"{API_BASE}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="Decision OS", layout="wide")
    st.title("Decision OS v3.0")
    view = st.sidebar.selectbox("View", ["Executive", "Model", "Portfolio", "Audit"])
    if view == "Executive":
        render_executive_view(_get("/gate/status"), _get("/capital/status"))
    elif view == "Model":
        render_model_view(_get("/model/simulation"))
    elif view == "Portfolio":
        render_portfolio_view(_get("/portfolio/summary"))
    else:
        render_audit_view(_get("/audit/logs"))


if __name__ == "__main__":
    main()
