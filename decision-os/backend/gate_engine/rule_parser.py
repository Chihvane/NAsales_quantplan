from __future__ import annotations


def compare(left: float, operator: str, right: float) -> bool:
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == "==":
        return left == right
    raise ValueError(f"Unsupported operator: {operator}")
