from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data_loader import generate_demo_panel  # noqa: E402
from backtest.strategy_optimizer import optimize_gate_thresholds  # noqa: E402


def run_demo(output_dir: str | Path | None = None) -> dict[str, object]:
    output_dir = Path(output_dir or ROOT / "artifacts" / "backtest_optimization")
    panel_rows = generate_demo_panel(seed=42)
    return optimize_gate_thresholds(
        panel_rows,
        output_dir=output_dir,
        simulations=400,
    )


if __name__ == "__main__":
    result = run_demo()
    print(result["best_gate_params"])
