from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionSnapshot:
    factor_score: float
    decision: str
