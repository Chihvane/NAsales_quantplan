from __future__ import annotations


def risk_within_budget(loss_probability: float, max_loss_probability: float) -> bool:
    return loss_probability <= max_loss_probability
