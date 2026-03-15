from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION_OS_ROOT = ROOT / "decision-os"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(DECISION_OS_ROOT) not in sys.path:
    sys.path.insert(0, str(DECISION_OS_ROOT))

from backtest.data_loader import generate_demo_panel  # noqa: E402
from backtest.stress_test import run_stress_suite  # noqa: E402
from backtest.strategy_optimizer import optimize_gate_thresholds  # noqa: E402
from backtest.walk_forward_engine import run_walk_forward_backtest  # noqa: E402
from backend.dependencies import build_market_snapshot  # noqa: E402
from quant_framework.decision_os_bridge import export_decision_os_bridge_bundle  # noqa: E402
from quant_framework.horizontal_pipeline import (  # noqa: E402
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report  # noqa: E402
from quant_framework.io_utils import write_json  # noqa: E402
from quant_framework.part0 import build_part0_quant_report  # noqa: E402
from quant_framework.part0_pipeline import (  # noqa: E402
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from quant_framework.part1 import build_part1_quant_report  # noqa: E402
from quant_framework.part2 import build_part2_quant_report  # noqa: E402
from quant_framework.part2_pipeline import (  # noqa: E402
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)
from quant_framework.part3 import build_part3_quant_report  # noqa: E402
from quant_framework.part3_pipeline import (  # noqa: E402
    DEFAULT_PART3_ASSUMPTIONS,
    build_part3_dataset_from_directory,
)
from quant_framework.part4 import build_part4_quant_report  # noqa: E402
from quant_framework.part4_pipeline import (  # noqa: E402
    DEFAULT_PART4_ASSUMPTIONS,
    build_part4_dataset_from_directory,
)
from quant_framework.part5 import build_part5_quant_report  # noqa: E402
from quant_framework.part5_pipeline import (  # noqa: E402
    DEFAULT_PART5_ASSUMPTIONS,
    build_part5_dataset_from_directory,
)
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory  # noqa: E402


def run_full_chain(output_dir: str | Path | None = None) -> dict[str, object]:
    output_dir = Path(output_dir or ROOT / "artifacts" / "full_system_run")
    reports_dir = output_dir / "reports"
    bridge_dir = output_dir / "bridge"
    backtest_dir = output_dir / "backtest"
    optimizer_dir = output_dir / "optimization"
    reports_dir.mkdir(parents=True, exist_ok=True)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    backtest_dir.mkdir(parents=True, exist_ok=True)
    optimizer_dir.mkdir(parents=True, exist_ok=True)

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

    report_paths = {
        "part0": str(write_json(reports_dir / "part0_report.json", part0_report)),
        "horizontal": str(write_json(reports_dir / "horizontal_system_report.json", horizontal_report)),
        "part1": str(write_json(reports_dir / "part1_report.json", part1_report)),
        "part2": str(write_json(reports_dir / "part2_report.json", part2_report)),
        "part3": str(write_json(reports_dir / "part3_report.json", part3_report)),
        "part4": str(write_json(reports_dir / "part4_report.json", part4_report)),
        "part5": str(write_json(reports_dir / "part5_report.json", part5_report)),
    }

    bridge_paths = export_decision_os_bridge_bundle(
        part1_report,
        part2_report,
        bridge_dir,
        part3_report=part3_report,
        part4_report=part4_report,
        part0_report=part0_report,
        horizontal_report=horizontal_report,
        part5_report=part5_report,
        tenant_id="TENANT-FULL-CHAIN",
        as_of_date="2026-03-15",
    )
    snapshot = build_market_snapshot()

    panel_rows = generate_demo_panel(seed=42)
    gate_params = snapshot.get("gate_thresholds", {})
    backtest_result = run_walk_forward_backtest(
        panel_rows,
        initial_capital=1_000_000,
        simulations=400,
        gate_params=gate_params,
    )
    stress_result = run_stress_suite(
        panel_rows,
        initial_capital=1_000_000,
        simulations=250,
        gate_params=gate_params,
    )
    optimization_result = optimize_gate_thresholds(
        panel_rows,
        output_dir=optimizer_dir,
        simulations=250,
        max_candidates=48,
        search_space={
            "min_factor_score": [0.55, 0.65],
            "max_loss_probability": [0.10, 0.15],
            "min_profit_p50": [0.0, 2.0],
            "min_governance_readiness_score": [0.6, 0.7],
            "min_control_tower_score": [0.65, 0.75],
            "min_forecast_backtest_score": [0.55],
            "min_drift_score": [0.55],
            "max_drift_risk_score": [0.45],
            "max_supply_tail_risk_score": [0.45],
            "min_supply_optimizer_feasible_ratio": [0.25],
            "min_channel_optimizer_feasible_ratio": [0.25],
            "min_channel_stress_robustness_score": [0.6],
            "min_operating_system_readiness_score": [0.5, 0.6],
            "min_data_contract_score": [0.55],
            "min_scale_control_score": [0.5],
            "max_operating_proxy_flag_count": [2.0, 4.0],
            "max_positions_per_period": [2, 3],
        },
    )

    write_json(backtest_dir / "walk_forward_result.json", backtest_result)
    write_json(backtest_dir / "stress_result.json", stress_result)

    summary = {
        "report_paths": report_paths,
        "bridge_paths": bridge_paths,
        "snapshot": {
            "source_mode": snapshot.get("source_mode"),
            "decision": snapshot.get("decision"),
            "factor_score": round(float(snapshot.get("factor_score", 0.0)), 4),
            "required_capital": round(float(snapshot.get("required_capital", 0.0)), 2),
            "gate_threshold_count": len(snapshot.get("gate_thresholds", {})),
        },
        "bridge_gate_inputs": {
            "governance_readiness_score": snapshot.get("bridge_bundle", {}).get("gate_inputs", {}).get(
                "governance_readiness_score"
            ),
            "control_tower_score": snapshot.get("bridge_bundle", {}).get("gate_inputs", {}).get(
                "control_tower_score"
            ),
            "operating_system_readiness_score": snapshot.get("bridge_bundle", {}).get("gate_inputs", {}).get(
                "operating_system_readiness_score"
            ),
            "integrated_factor_score": snapshot.get("bridge_bundle", {}).get("gate_inputs", {}).get(
                "integrated_factor_score"
            ),
        },
        "backtest_summary": backtest_result["summary"],
        "stress_summary": stress_result,
        "optimization_summary": {
            "best_gate_params": optimization_result["best_gate_params"],
            "train_score": optimization_result["train_score"],
            "test_score": optimization_result["test_score"],
            "candidate_count": optimization_result["candidate_count"],
            "test_alpha": optimization_result["test_summary"]["alpha"],
        },
    }
    summary_path = write_json(output_dir / "full_system_run_summary.json", summary)
    return {
        "summary_json": str(summary_path),
        "bridge_json": bridge_paths["bundle_json"],
        "optimizer_json": str(optimizer_dir / "strategy_optimization.json"),
    }


if __name__ == "__main__":
    result = run_full_chain()
    print(json.dumps(result, ensure_ascii=False, indent=2))
