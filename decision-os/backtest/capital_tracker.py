from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CapitalTracker:
    total_capital: float
    currency: str = "USD"
    allocated_capital: float = 0.0
    history: list[dict[str, float]] = field(default_factory=list)

    @property
    def free_capital(self) -> float:
        return self.total_capital - self.allocated_capital

    def reset_period(self) -> None:
        self.allocated_capital = 0.0

    def can_allocate(self, required_capital: float) -> bool:
        return required_capital <= self.free_capital

    def allocate(self, required_capital: float) -> bool:
        if not self.can_allocate(required_capital):
            return False
        self.allocated_capital += required_capital
        return True

    def close_period(self, period: str, realized_profit: float) -> dict[str, float | str]:
        starting_capital = self.total_capital
        self.total_capital += realized_profit
        record = {
            "period": period,
            "starting_capital": round(starting_capital, 2),
            "ending_capital": round(self.total_capital, 2),
            "period_profit": round(realized_profit, 2),
        }
        self.history.append(record)
        self.reset_period()
        return record
