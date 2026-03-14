from __future__ import annotations

from collections import defaultdict
from datetime import date


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def reconstruct_state(panel_rows: list[dict[str, str | float]], as_of_date: str) -> list[dict[str, str | float]]:
    target = _parse_date(as_of_date)
    history_by_entity: dict[str, list[dict[str, str | float]]] = defaultdict(list)
    for row in panel_rows:
        row_date = _parse_date(str(row["as_of_date"]))
        if row_date <= target:
            history_by_entity[str(row["entity_id"])].append(row)

    reconstructed: list[dict[str, str | float]] = []
    for entity_rows in history_by_entity.values():
        entity_rows.sort(key=lambda item: str(item["as_of_date"]))
        latest = dict(entity_rows[-1])
        trailing_returns = [float(item["forward_return_rate"]) for item in entity_rows[-3:]]
        latest["observed_return_mean_3m"] = round(sum(trailing_returns) / len(trailing_returns), 4)
        reconstructed.append(latest)

    reconstructed.sort(key=lambda item: str(item["entity_id"]))
    return reconstructed
