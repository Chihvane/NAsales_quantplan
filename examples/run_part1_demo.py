import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory  # noqa: E402
from quant_framework.part1 import build_part1_quant_report  # noqa: E402


def main() -> None:
    examples_dir = Path(__file__).resolve().parent
    dataset = build_dataset_from_directory(examples_dir)
    report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
