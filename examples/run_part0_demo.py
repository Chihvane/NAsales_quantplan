from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_part0_chart_assets  # noqa: E402
from quant_framework.io_utils import write_json  # noqa: E402
from quant_framework.part0 import build_part0_quant_report  # noqa: E402
from quant_framework.part0_pipeline import (  # noqa: E402
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)

DATA_DIR = ROOT / "examples" / "part0_demo"
OUTPUT_DIR = ROOT / "examples" / "output_part0"


def main() -> None:
    dataset = build_part0_dataset_from_directory(DATA_DIR)
    report = build_part0_quant_report(dataset, DEFAULT_PART0_ASSUMPTIONS)
    report_path = write_json(OUTPUT_DIR / "part0_report.json", report)
    chart_paths = generate_part0_chart_assets(report, OUTPUT_DIR / "charts")
    print(
        json.dumps(
            {
                "report_json": str(report_path),
                "charts": chart_paths,
                "validation": report["validation"]["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
