from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_horizontal_system_chart_assets  # noqa: E402
from quant_framework.horizontal_pipeline import (  # noqa: E402
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report  # noqa: E402
from quant_framework.io_utils import write_json  # noqa: E402

DATA_DIR = ROOT / "examples" / "horizontal_system_demo"
OUTPUT_DIR = ROOT / "examples" / "output_horizontal_system"


def main() -> None:
    dataset = build_horizontal_system_dataset_from_directory(DATA_DIR)
    report = build_horizontal_system_report(dataset, DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS)
    report_path = write_json(OUTPUT_DIR / "horizontal_system_report.json", report)
    chart_paths = generate_horizontal_system_chart_assets(report, OUTPUT_DIR / "charts")
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
