from __future__ import annotations


def compute_capital_state(total: float, allocated: float) -> dict[str, float]:
    return {
        "total_capital": total,
        "allocated_capital": allocated,
        "free_capital": total - allocated,
    }
