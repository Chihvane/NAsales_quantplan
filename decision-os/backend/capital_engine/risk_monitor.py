from __future__ import annotations


def build_risk_state(max_loss_probability: float, max_drawdown: float) -> dict[str, float]:
    return {
        "max_loss_probability": max_loss_probability,
        "max_drawdown": max_drawdown,
    }
