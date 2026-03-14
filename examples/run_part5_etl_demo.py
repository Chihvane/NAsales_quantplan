from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.part5_etl import run_part5_etl_skeleton  # noqa: E402

SOURCE_DIR = ROOT / "examples" / "part5_demo"
OUTPUT_DIR = ROOT / "examples" / "output_part5_etl"


def main() -> None:
    payload = run_part5_etl_skeleton(
        SOURCE_DIR,
        OUTPUT_DIR,
        batch_id="part5-demo-batch",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
