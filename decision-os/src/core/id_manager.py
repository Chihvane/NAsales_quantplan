from __future__ import annotations


class IdManager:
    """Generate deterministic layer-prefixed identifiers."""

    @staticmethod
    def build(prefix: str, number: int, width: int = 4) -> str:
        return f"{prefix}-{number:0{width}d}"
