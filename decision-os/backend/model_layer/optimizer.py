from __future__ import annotations


def best_candidate(candidates: list[tuple[str, float]]) -> str | None:
    return max(candidates, key=lambda item: item[1])[0] if candidates else None
