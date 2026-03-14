from __future__ import annotations


def flatten(values: list[list]) -> list:
    return [item for row in values for item in row]
