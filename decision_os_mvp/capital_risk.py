from __future__ import annotations


class CapitalState:
    def __init__(self, total: float, allocated: float) -> None:
        self.total = total
        self.allocated = allocated

    @property
    def free(self) -> float:
        return self.total - self.allocated


class RiskBudget:
    def __init__(self, max_loss_probability: float, max_drawdown: float) -> None:
        self.max_loss_probability = max_loss_probability
        self.max_drawdown = max_drawdown
