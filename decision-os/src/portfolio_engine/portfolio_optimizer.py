from __future__ import annotations


def rank_opportunities(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: row.get("score", 0.0), reverse=True)
