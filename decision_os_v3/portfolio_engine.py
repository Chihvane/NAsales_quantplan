from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Iterable

from .models import (
    CapitalPoolStateV3,
    PortfolioAllocationV3,
    PortfolioOpportunityV3,
    RiskBudgetStateV3,
)


def _objective_score(opportunity: PortfolioOpportunityV3) -> float:
    capital_efficiency = opportunity.expected_return / max(opportunity.required_capital, 1.0)
    risk_penalty = (
        opportunity.expected_loss_probability * 0.4
        + opportunity.expected_drawdown * 0.3
        + opportunity.channel_dependency * 0.2
    )
    return round(capital_efficiency + opportunity.priority_score - risk_penalty, 6)


def allocate_portfolio_v3(
    opportunities: Iterable[PortfolioOpportunityV3],
    capital_pool: CapitalPoolStateV3,
    risk_budget: RiskBudgetStateV3,
) -> dict:
    ordered = sorted(opportunities, key=_objective_score, reverse=True)
    remaining_capital = capital_pool.free_capital
    channel_allocations: dict[str, float] = defaultdict(float)
    rows: list[PortfolioAllocationV3] = []
    portfolio_id = ordered[0].portfolio_id if ordered else ""

    for opportunity in ordered:
        objective_score = _objective_score(opportunity)

        reject_reason = ""
        if opportunity.expected_loss_probability > risk_budget.max_loss_probability:
            reject_reason = "loss_probability_limit"
        elif opportunity.expected_drawdown > risk_budget.max_drawdown:
            reject_reason = "drawdown_limit"
        elif opportunity.channel_dependency > risk_budget.max_channel_dependency:
            reject_reason = "channel_dependency_input_limit"
        else:
            next_channel_capital = channel_allocations[opportunity.channel] + opportunity.required_capital
            if capital_pool.free_capital > 0 and next_channel_capital / capital_pool.free_capital > risk_budget.max_channel_dependency:
                reject_reason = "channel_dependency_limit"
            elif opportunity.required_capital > remaining_capital:
                reject_reason = "insufficient_capital"

        if reject_reason:
            rows.append(
                PortfolioAllocationV3(
                    portfolio_id=opportunity.portfolio_id,
                    opportunity_id=opportunity.opportunity_id,
                    channel=opportunity.channel,
                    allocated_capital=0.0,
                    expected_return=opportunity.expected_return,
                    expected_drawdown=opportunity.expected_drawdown,
                    objective_score=objective_score,
                    accepted=False,
                    reject_reason=reject_reason,
                )
            )
            continue

        remaining_capital -= opportunity.required_capital
        channel_allocations[opportunity.channel] += opportunity.required_capital
        rows.append(
            PortfolioAllocationV3(
                portfolio_id=opportunity.portfolio_id,
                opportunity_id=opportunity.opportunity_id,
                channel=opportunity.channel,
                allocated_capital=opportunity.required_capital,
                expected_return=opportunity.expected_return,
                expected_drawdown=opportunity.expected_drawdown,
                objective_score=objective_score,
                accepted=True,
            )
        )

    accepted_rows = [row for row in rows if row.accepted]
    allocated_capital = sum(row.allocated_capital for row in accepted_rows)
    expected_profit_proxy = sum(row.allocated_capital * row.expected_return for row in accepted_rows)
    return {
        "portfolio_id": portfolio_id,
        "accepted_count": len(accepted_rows),
        "rejected_count": len(rows) - len(accepted_rows),
        "allocated_capital": round(allocated_capital, 2),
        "remaining_capital": round(remaining_capital, 2),
        "capital_utilization_rate": round(allocated_capital / max(capital_pool.free_capital, 1.0), 4),
        "expected_profit_proxy": round(expected_profit_proxy, 2),
        "channel_allocation_share": {
            channel: round(value / capital_pool.free_capital, 4) if capital_pool.free_capital > 0 else 0.0
            for channel, value in sorted(channel_allocations.items())
        },
        "rows": [asdict(row) for row in rows],
    }
