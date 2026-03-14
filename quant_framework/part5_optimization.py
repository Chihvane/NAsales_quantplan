from __future__ import annotations

try:
    import cvxpy as cp
except Exception:  # pragma: no cover - fallback for missing solver environments
    cp = None

from .models import Part5Assumptions
from .stats_utils import safe_divide


def recommend_budget_allocation(
    channel_rows: list[dict],
    assumptions: Part5Assumptions,
) -> dict:
    eligible_rows = [row for row in channel_rows if row.get("revenue", 0.0) > 0]
    if not eligible_rows:
        return {"allocation": {}, "method": "unavailable"}

    scores = [
        max(
            row.get("contribution_margin_rate", 0.0) * 0.45
            + row.get("repeat_rate", 0.0) * 0.2
            + (1 - row.get("return_rate", 0.0)) * 0.2
            + (1 - min(row.get("payback_period_months", 12.0) / 12.0, 1.0)) * 0.15,
            0.0001,
        )
        for row in eligible_rows
    ]
    total_spend = sum(row.get("acquisition_cost_total", 0.0) for row in eligible_rows)
    current_shares = [
        safe_divide(row.get("acquisition_cost_total", 0.0), total_spend, default=1 / len(eligible_rows))
        for row in eligible_rows
    ]

    if cp is not None:
        variable = cp.Variable(len(eligible_rows), nonneg=True)
        min_share = min(0.02, 1 / len(eligible_rows))
        constraints = [
            cp.sum(variable) == 1,
            variable >= min_share,
            variable <= assumptions.budget_allocation_max_share,
        ]
        objective = cp.Maximize(scores @ variable - 0.05 * cp.sum_squares(variable - current_shares))
        problem = cp.Problem(objective, constraints)
        try:
            problem.solve(solver=cp.SCS, verbose=False)
            if variable.value is not None:
                allocation = {
                    row["channel"]: round(float(share), 4)
                    for row, share in zip(eligible_rows, variable.value.tolist())
                }
                return {"allocation": allocation, "method": "cvxpy_scs"}
        except Exception:
            pass

    total_score = sum(scores)
    allocation = {
        row["channel"]: round(score / total_score, 4)
        for row, score in zip(eligible_rows, scores)
    }
    return {"allocation": allocation, "method": "heuristic"}
