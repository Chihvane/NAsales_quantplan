from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.backtest import run_full_backtest_suite  # noqa: E402

OUTPUT_DIR = ROOT / "examples" / "output_backtest_suite"


def main() -> None:
    payload = run_full_backtest_suite(OUTPUT_DIR, seed=42)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
