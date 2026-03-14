from __future__ import annotations


def normalize_version(version: str) -> tuple[int, ...]:
    parts = [part for part in version.split(".") if part]
    return tuple(int(part) for part in parts)
