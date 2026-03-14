from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data_loader import generate_demo_panel, write_panel_csv  # noqa: E402
from backtest.report_generator import write_csv, write_curve_svg, write_json, write_markdown_report  # noqa: E402
from backtest.walk_forward_engine import run_walk_forward_backtest  # noqa: E402


def run_demo(output_dir: str | Path | None = None) -> dict:
    output_dir = Path(output_dir or ROOT / "artifacts" / "backtest_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    panel_rows = generate_demo_panel(seed=42)
    panel_path = write_panel_csv(output_dir / "decision_os_backtest_panel.csv", panel_rows)
    result = run_walk_forward_backtest(panel_rows)

    summary_path = write_json(output_dir / "backtest_summary.json", result["summary"])
    period_path = write_csv(output_dir / "period_records.csv", result["period_records"])
    decisions_path = write_csv(output_dir / "decision_accuracy.csv", result["decisions"])
    alpha_rows = [
        {
            "strategy_cumulative_return": result["summary"]["strategy_cumulative_return"],
            "benchmark_cumulative_return": result["summary"]["benchmark_cumulative_return"],
            "alpha": result["summary"]["alpha"],
            "strategy_max_drawdown": result["summary"]["strategy_max_drawdown"],
            "benchmark_max_drawdown": result["summary"]["benchmark_max_drawdown"],
        }
    ]
    alpha_path = write_csv(output_dir / "alpha_table.csv", alpha_rows)
    performance_curve = write_curve_svg(
        output_dir / "performance_curve.svg",
        result["summary"]["strategy_curve"],
        result["summary"]["benchmark_curve"],
        "Decision OS Backtest Cumulative Return",
    )
    drawdown_curve = write_curve_svg(
        output_dir / "drawdown_curve.svg",
        [1 + value for value in result["summary"]["strategy_drawdown_curve"]],
        [1 + value for value in result["summary"]["benchmark_drawdown_curve"]],
        "Decision OS Backtest Drawdown Curve",
    )
    report_path = write_markdown_report(
        output_dir / "backtest_report.md",
        result["summary"],
        {
            "panel": str(panel_path),
            "summary": str(summary_path),
            "period_records": str(period_path),
            "decision_accuracy": str(decisions_path),
            "alpha_table": str(alpha_path),
            "performance_curve": str(performance_curve),
            "drawdown_curve": str(drawdown_curve),
        },
    )
    return {
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "summary": result["summary"],
    }


if __name__ == "__main__":
    demo_result = run_demo()
    print(demo_result["summary_path"])
    print(demo_result["report_path"])
