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


def evaluate_gate(conditions: list[dict], context: dict) -> str:
    for condition in conditions:
        left = context.get(condition["ref"])
        right = condition.get("value")
        if left is None or not compare(left, condition["operator"], right):
            return "NO_GO"
    return "GO"
