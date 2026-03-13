from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_part2_chart_assets
from quant_framework.io_utils import write_json
from quant_framework.part2 import build_part2_quant_report
from quant_framework.part2_pipeline import (
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)

DATA_DIR = ROOT / "examples" / "part2_demo"
OUTPUT_DIR = ROOT / "examples" / "output_part2"


def main() -> None:
    dataset = build_part2_dataset_from_directory(DATA_DIR)
    report = build_part2_quant_report(dataset, DEFAULT_PART2_ASSUMPTIONS)
    write_json(OUTPUT_DIR / "part2_report.json", report)
    chart_paths = generate_part2_chart_assets(report, OUTPUT_DIR / "charts")
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
