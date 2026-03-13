from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.backtest import (  # noqa: E402
    build_part2_backtest_panel_from_directory,
    load_part2_backtest_panel,
    run_part2_competition_backtest,
    write_backtest_curve_svg,
    write_backtest_monthly_csv,
)
from quant_framework.charts import generate_part2_chart_assets  # noqa: E402
from quant_framework.cleaners import normalize_amazon_part2_export  # noqa: E402
from quant_framework.io_utils import write_json  # noqa: E402
from quant_framework.part2 import build_part2_quant_report  # noqa: E402
from quant_framework.part2_pipeline import (  # noqa: E402
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)


RAW_CSV = ROOT / "external_inputs" / "github_amazon_products.csv"
OUTPUT_DIR = ROOT / "external_inputs" / "github_amazon_part2_demo"


def main() -> None:
    clean_summary = normalize_amazon_part2_export(
        RAW_CSV,
        OUTPUT_DIR / "bundle",
    )

    dataset = build_part2_dataset_from_directory(OUTPUT_DIR / "bundle")
    report = build_part2_quant_report(dataset, DEFAULT_PART2_ASSUMPTIONS)
    report_path = write_json(OUTPUT_DIR / "report.json", report)
    chart_paths = generate_part2_chart_assets(report, OUTPUT_DIR / "charts")

    panel_path = build_part2_backtest_panel_from_directory(
        OUTPUT_DIR / "bundle",
        OUTPUT_DIR / "github_part2_panel.csv",
        category_depth=1,
        min_categories_per_month=3,
    )
    panel_rows = load_part2_backtest_panel(panel_path)
    backtest_result = run_part2_competition_backtest(panel_rows, lookback=2, top_n=2)
    backtest_json = write_json(OUTPUT_DIR / "part2_backtest_summary.json", backtest_result)
    backtest_curve = write_backtest_curve_svg(backtest_result, OUTPUT_DIR / "part2_backtest_curve.svg")
    backtest_monthly_csv = write_backtest_monthly_csv(
        backtest_result,
        OUTPUT_DIR / "part2_backtest_monthly_returns.csv",
    )

    print(
        json.dumps(
            {
                "cleaning": clean_summary,
                "report_json": str(report_path),
                "charts": chart_paths,
                "panel_csv": str(panel_path),
                "panel_rows": len(panel_rows),
                "backtest_json": str(backtest_json),
                "backtest_curve": str(backtest_curve),
                "backtest_monthly_csv": str(backtest_monthly_csv),
                "backtest_summary": backtest_result["summary"],
                "validation": report["validation"]["summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
