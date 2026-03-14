from __future__ import annotations

from collections import defaultdict


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, dict]] = defaultdict(dict)

    def register(self, group: str, item_id: str, payload: dict) -> None:
        self._items[group][item_id] = payload

    def get(self, group: str, item_id: str) -> dict | None:
        return self._items.get(group, {}).get(item_id)
