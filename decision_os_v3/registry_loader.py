from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_registry_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif suffix in {".yaml", ".yml"}:
        import yaml  # type: ignore

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported registry suffix: {path.suffix}")
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load as a mapping.")
    return payload
