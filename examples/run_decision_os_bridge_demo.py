from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from quant_framework.decision_os_bridge import export_decision_os_bridge_bundle
from quant_framework.horizontal_pipeline import (
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report
from quant_framework.part0 import build_part0_quant_report
from quant_framework.part0_pipeline import (
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from quant_framework.part1 import build_part1_quant_report
from quant_framework.part2 import build_part2_quant_report
from quant_framework.part2_pipeline import DEFAULT_PART2_ASSUMPTIONS, build_part2_dataset_from_directory
from quant_framework.part3 import build_part3_quant_report
from quant_framework.part3_pipeline import DEFAULT_PART3_ASSUMPTIONS, build_part3_dataset_from_directory
from quant_framework.part4 import build_part4_quant_report
from quant_framework.part4_pipeline import DEFAULT_PART4_ASSUMPTIONS, build_part4_dataset_from_directory
from quant_framework.part5 import build_part5_quant_report
from quant_framework.part5_pipeline import DEFAULT_PART5_ASSUMPTIONS, build_part5_dataset_from_directory
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory


def run_demo(output_dir: str | Path | None = None) -> dict[str, str]:
    part0_report = build_part0_quant_report(
        build_part0_dataset_from_directory(ROOT / "examples" / "part0_demo"),
        DEFAULT_PART0_ASSUMPTIONS,
    )
    horizontal_report = build_horizontal_system_report(
        build_horizontal_system_dataset_from_directory(ROOT / "examples" / "horizontal_system_demo"),
        DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    )
    part1_report = build_part1_quant_report(
        build_dataset_from_directory(ROOT / "examples"),
        DEFAULT_ASSUMPTIONS,
    )
    part2_report = build_part2_quant_report(
        build_part2_dataset_from_directory(ROOT / "examples" / "part2_demo"),
        DEFAULT_PART2_ASSUMPTIONS,
    )
    part3_report = build_part3_quant_report(
        build_part3_dataset_from_directory(ROOT / "examples" / "part3_demo"),
        DEFAULT_PART3_ASSUMPTIONS,
    )
    part4_report = build_part4_quant_report(
        build_part4_dataset_from_directory(ROOT / "examples" / "part4_demo"),
        DEFAULT_PART4_ASSUMPTIONS,
    )
    part5_report = build_part5_quant_report(
        build_part5_dataset_from_directory(ROOT / "examples" / "part5_demo"),
        DEFAULT_PART5_ASSUMPTIONS,
    )
    output_dir = Path(output_dir or ROOT / "artifacts" / "decision_os_bridge")
    result = export_decision_os_bridge_bundle(
        part1_report,
        part2_report,
        output_dir,
        part3_report=part3_report,
        part4_report=part4_report,
        part0_report=part0_report,
        horizontal_report=horizontal_report,
        part5_report=part5_report,
        tenant_id="TENANT-DEMO",
        as_of_date="2026-03-15",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    run_demo()
