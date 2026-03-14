from __future__ import annotations


def can_allocate(required_capital: float, free_capital: float) -> bool:
    return required_capital <= free_capital
