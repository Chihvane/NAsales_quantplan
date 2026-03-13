from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_part2_chart_assets  # noqa: E402
from quant_framework.cleaners import (  # noqa: E402
    combine_part2_bundles,
    normalize_amazon_part2_export,
    normalize_ebay_part2_export,
    normalize_tiktok_part2_export,
)
from quant_framework.io_utils import write_json  # noqa: E402
from quant_framework.part2 import build_part2_quant_report  # noqa: E402
from quant_framework.part2_pipeline import (  # noqa: E402
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)


EXAMPLES = ROOT / "examples"
OUTPUT_ROOT = EXAMPLES / "cleaned_part2_demo"


def main() -> None:
    amazon_dir = OUTPUT_ROOT / "amazon"
    ebay_dir = OUTPUT_ROOT / "ebay"
    tiktok_dir = OUTPUT_ROOT / "tiktok"
    combined_dir = OUTPUT_ROOT / "combined"

    amazon_summary = normalize_amazon_part2_export(
        EXAMPLES / "raw_part2_amazon_export.csv",
        amazon_dir,
        capture_date="2025-11-30",
    )
    ebay_summary = normalize_ebay_part2_export(
        EXAMPLES / "raw_part2_ebay_sold_export.csv",
        ebay_dir,
    )
    tiktok_summary = normalize_tiktok_part2_export(
        EXAMPLES / "raw_part2_tiktok_export.csv",
        tiktok_dir,
        capture_date="2025-11-30",
    )
    combined_summary = combine_part2_bundles(
        [amazon_dir, ebay_dir, tiktok_dir],
        combined_dir,
    )

    dataset = build_part2_dataset_from_directory(combined_dir)
    report = build_part2_quant_report(dataset, DEFAULT_PART2_ASSUMPTIONS)
    report_path = write_json(combined_dir / "part2_report.json", report)
    chart_paths = generate_part2_chart_assets(report, combined_dir / "charts")

    print(
        json.dumps(
            {
                "cleaning": {
                    "amazon": amazon_summary,
                    "ebay": ebay_summary,
                    "tiktok": tiktok_summary,
                    "combined": combined_summary,
                },
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
