from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import CapitalPoolState, OpportunitySpec, PortfolioAllocationRow, RiskBudgetState


def _objective_score(opportunity: OpportunitySpec) -> float:
    capital_efficiency = opportunity.expected_return / max(opportunity.required_capital, 1.0)
    risk_penalty = opportunity.expected_loss_probability * 0.4 + opportunity.expected_drawdown * 0.3
    return round(capital_efficiency + opportunity.priority_score - risk_penalty, 6)


def allocate_portfolio(
    opportunities: Iterable[OpportunitySpec],
    capital_pool: CapitalPoolState,
    risk_budget: RiskBudgetState,
) -> dict:
    ordered = sorted(opportunities, key=_objective_score, reverse=True)
    remaining_capital = capital_pool.free_capital
    channel_allocations: dict[str, float] = defaultdict(float)
    rows: list[PortfolioAllocationRow] = []

    for opportunity in ordered:
        objective_score = _objective_score(opportunity)
        if opportunity.expected_loss_probability > risk_budget.max_loss_probability:
            rows.append(
                PortfolioAllocationRow(
                    opportunity_id=opportunity.opportunity_id,
                    channel=opportunity.channel,
                    allocated_capital=0.0,
                    expected_return=opportunity.expected_return,
                    objective_score=objective_score,
                    accepted=False,
                    reject_reason="loss_probability_limit",
                )
            )
            continue
        if opportunity.expected_drawdown > risk_budget.max_drawdown:
            rows.append(
                PortfolioAllocationRow(
                    opportunity_id=opportunity.opportunity_id,
                    channel=opportunity.channel,
                    allocated_capital=0.0,
                    expected_return=opportunity.expected_return,
                    objective_score=objective_score,
                    accepted=False,
                    reject_reason="drawdown_limit",
                )
            )
            continue
        next_channel_capital = channel_allocations[opportunity.channel] + opportunity.required_capital
        if capital_pool.free_capital > 0 and next_channel_capital / capital_pool.free_capital > risk_budget.max_channel_dependency:
            rows.append(
                PortfolioAllocationRow(
                    opportunity_id=opportunity.opportunity_id,
                    channel=opportunity.channel,
                    allocated_capital=0.0,
                    expected_return=opportunity.expected_return,
                    objective_score=objective_score,
                    accepted=False,
                    reject_reason="channel_dependency_limit",
                )
            )
            continue
        if opportunity.required_capital > remaining_capital:
            rows.append(
                PortfolioAllocationRow(
                    opportunity_id=opportunity.opportunity_id,
                    channel=opportunity.channel,
                    allocated_capital=0.0,
                    expected_return=opportunity.expected_return,
                    objective_score=objective_score,
                    accepted=False,
                    reject_reason="insufficient_capital",
                )
            )
            continue

        remaining_capital -= opportunity.required_capital
        channel_allocations[opportunity.channel] += opportunity.required_capital
        rows.append(
            PortfolioAllocationRow(
                opportunity_id=opportunity.opportunity_id,
                channel=opportunity.channel,
                allocated_capital=opportunity.required_capital,
                expected_return=opportunity.expected_return,
                objective_score=objective_score,
                accepted=True,
            )
        )

    accepted_rows = [row for row in rows if row.accepted]
    return {
        "accepted_count": len(accepted_rows),
        "rejected_count": len(rows) - len(accepted_rows),
        "allocated_capital": round(sum(row.allocated_capital for row in accepted_rows), 2),
        "remaining_capital": round(remaining_capital, 2),
        "channel_allocation_share": {
            channel: round(value / capital_pool.free_capital, 4) if capital_pool.free_capital > 0 else 0.0
            for channel, value in sorted(channel_allocations.items())
        },
        "rows": [row.__dict__ for row in rows],
    }
