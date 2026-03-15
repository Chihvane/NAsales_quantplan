from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_quant_bridge_bundle_path() -> Path:
    workspace_root = Path(__file__).resolve().parents[3]
    return workspace_root / "artifacts" / "decision_os_bridge" / "integrated_market_product_bundle.json"


def load_quant_bridge_bundle(path: str | Path | None = None) -> dict[str, Any] | None:
    bundle_path = Path(path) if path else default_quant_bridge_bundle_path()
    if not bundle_path.exists():
        return None
    return json.loads(bundle_path.read_text(encoding="utf-8"))
