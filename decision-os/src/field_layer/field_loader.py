from __future__ import annotations

from pathlib import Path
import json


def load_json_field_records(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else [payload]
