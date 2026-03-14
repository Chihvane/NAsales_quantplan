from __future__ import annotations


def run_stub_monte_carlo(expected_return: float, simulations: int = 1000) -> dict:
    return {
        "simulations": simulations,
        "profit_p50": expected_return,
        "loss_probability": 0.1 if expected_return > 0 else 0.5,
    }
