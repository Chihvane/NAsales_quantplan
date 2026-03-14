from __future__ import annotations


def scenario_stub(base_profit: float, shock_ratio: float) -> float:
    return round(base_profit * (1 - shock_ratio), 4)
