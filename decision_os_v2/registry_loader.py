from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def load_registry_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must load as a mapping.")
        return payload
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "YAML registry loading requires PyYAML. Install `PyYAML` to load Decision OS registry files."
            ) from exc
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must load as a mapping.")
        return payload
    raise ValueError(f"Unsupported registry suffix: {path.suffix}")


def ensure_mapping(payload: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    return dict(payload)
