import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.charts import generate_part1_chart_assets  # noqa: E402
from quant_framework.io_utils import write_json  # noqa: E402
from quant_framework.part1 import build_part1_quant_report  # noqa: E402
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory  # noqa: E402


def main() -> None:
    examples_dir = Path(__file__).resolve().parent
    output_dir = examples_dir / "output"
    charts_dir = output_dir / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = build_dataset_from_directory(examples_dir)
    report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)
    report_path = write_json(output_dir / "part1_report.json", report)
    chart_paths = generate_part1_chart_assets(report, charts_dir)
    print(
        json.dumps(
            {
                "report_json": str(report_path),
                "charts": chart_paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
