from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.ph_ugreen_case import run_ph_ugreen_case


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Philippines UGREEN livestream case through Part4/Part5.")
    parser.add_argument("excel_path", help="Path to the Philippines UGREEN Excel export.")
    parser.add_argument(
        "--output-dir",
        default=str(Path("artifacts") / "ph_ugreen_case"),
        help="Directory for generated case artifacts.",
    )
    args = parser.parse_args()

    result = run_ph_ugreen_case(args.excel_path, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
