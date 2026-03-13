import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.backtest import run_backtest_demo  # noqa: E402


def main() -> None:
    examples_dir = Path(__file__).resolve().parent
    output_dir = examples_dir / "output" / "backtest_demo"
    payload = run_backtest_demo(output_dir, seed=42)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
