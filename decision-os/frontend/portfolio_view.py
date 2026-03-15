from __future__ import annotations

import pandas as pd
import streamlit as st


def render_portfolio_view(snapshot_payload: dict, summary_payload: dict) -> None:
    portfolio_rows = snapshot_payload.get("portfolio_rows", [])
    backtest_summary = summary_payload.get("summary", {}).get("backtest_summary", {})
    stress_summary = summary_payload.get("summary", {}).get("stress_summary", {})

    st.subheader("Current Portfolio Recommendation")
    if portfolio_rows:
        st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True, hide_index=True)

    st.subheader("Backtest Allocation Health")
    cols = st.columns(4)
    cols[0].metric("GO Ratio", backtest_summary.get("go_ratio", 0.0))
    cols[1].metric("Hit Rate", backtest_summary.get("decision_hit_rate", 0.0))
    cols[2].metric("Deployed Capital", backtest_summary.get("average_deployed_capital_ratio", 0.0))
    cols[3].metric("Avg Positions", backtest_summary.get("average_positions_per_period", 0.0))

    st.subheader("Stress Scenarios")
    scenarios = stress_summary.get("scenarios", [])
    if scenarios:
        scenario_rows = []
        for scenario in scenarios:
            scenario_rows.append(
                {
                    "scenario_id": scenario.get("scenario_id", ""),
                    "alpha": scenario.get("summary", {}).get("alpha", 0.0),
                    "go_ratio": scenario.get("summary", {}).get("go_ratio", 0.0),
                    "score": scenario.get("scenario_score", 0.0),
                }
            )
        frame = pd.DataFrame(scenario_rows)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.bar_chart(frame.set_index("scenario_id")[["score"]], use_container_width=True)
