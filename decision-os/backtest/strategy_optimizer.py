from __future__ import annotations

from itertools import product
from pathlib import Path

from backtest.report_generator import write_json
from backtest.stress_test import run_stress_suite
from backtest.walk_forward_engine import run_walk_forward_backtest
from backend.oss_integrations.mlflow_adapter import log_tracking_payload
from backend.oss_integrations.optuna_adapter import get_optuna_status


def _band_score(value: float, lower: float, upper: float) -> float:
    if lower <= value <= upper:
        return 1.0
    if value < lower:
        return max(0.0, 1.0 - ((lower - value) / max(lower, 1e-9)))
    return max(0.0, 1.0 - ((value - upper) / max(1.0 - upper, 1e-9)))


def _composite_score(summary: dict[str, float | int | list[float]], stress_summary: dict[str, object] | None = None) -> float:
    alpha = float(summary.get("alpha", 0.0))
    hit_rate = float(summary.get("decision_hit_rate", 0.0))
    rejection_precision = float(summary.get("rejection_precision", 0.0))
    go_ratio = float(summary.get("go_ratio", 0.0))
    drawdown = abs(float(summary.get("strategy_max_drawdown", 0.0)))
    deployed_capital_ratio = float(summary.get("average_deployed_capital_ratio", 0.0))
    stress_robustness = float(stress_summary.get("robustness_score", 0.5)) if stress_summary else 0.5

    selectivity_score = _band_score(go_ratio, 0.30, 0.70)
    deployed_capital_score = _band_score(deployed_capital_ratio, 0.35, 0.85)
    composite = (
        alpha * 1.1
        + hit_rate * 0.35
        + rejection_precision * 0.35
        + selectivity_score * 0.25
        + deployed_capital_score * 0.20
        + stress_robustness * 0.30
        - drawdown * 0.75
    )
    return round(composite, 6)


def optimize_gate_thresholds(
    panel_rows: list[dict[str, str | float]],
    *,
    output_dir: str | Path,
    search_space: dict[str, list[float]] | None = None,
    optimization_metric: str = "composite_score",
    train_ratio: float = 0.7,
    initial_capital: float = 1_000_000,
    simulations: int = 800,
    seed: int = 42,
    enable_stress_test: bool = True,
) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    search_space = search_space or {
        "min_factor_score": [0.55, 0.65],
        "max_loss_probability": [0.10, 0.15],
        "min_profit_p50": [0.0, 2.0, 4.0],
        "min_margin_p50_ratio": [0.18, 0.22],
        "max_volatility": [0.20, 0.24],
        "max_positions_per_period": [2, 3],
    }

    ordered_dates = sorted({str(row["as_of_date"]) for row in panel_rows})
    split_index = max(1, int(len(ordered_dates) * train_ratio))
    train_dates = set(ordered_dates[:split_index])
    test_dates = set(ordered_dates[split_index:])
    train_rows = [row for row in panel_rows if str(row["as_of_date"]) in train_dates]
    test_rows = [row for row in panel_rows if str(row["as_of_date"]) in test_dates]

    keys = list(search_space.keys())
    best_candidate: dict[str, object] | None = None
    candidate_rows: list[dict[str, object]] = []

    for values in product(*(search_space[key] for key in keys)):
        gate_params = dict(zip(keys, values))
        train_result = run_walk_forward_backtest(
            train_rows,
            initial_capital=initial_capital,
            simulations=simulations,
            seed=seed,
            gate_params=gate_params,
        )
        train_stress_summary = (
            run_stress_suite(
                train_rows,
                gate_params=gate_params,
                initial_capital=initial_capital,
                simulations=max(300, simulations // 2),
                seed=seed + 3000,
            )
            if enable_stress_test
            else None
        )
        if optimization_metric == "composite_score":
            score = _composite_score(train_result["summary"], train_stress_summary)
        else:
            score = float(train_result["summary"].get(optimization_metric, 0.0))
        candidate_payload = {
            "gate_params": gate_params,
            "train_summary": train_result["summary"],
            "train_stress_summary": train_stress_summary,
            "train_score": score,
        }
        candidate_rows.append(candidate_payload)
        if best_candidate is None or score > float(best_candidate["train_score"]):
            best_candidate = candidate_payload

    if best_candidate is None:
        raise ValueError("No optimization candidates were generated")

    test_result = run_walk_forward_backtest(
        test_rows,
        initial_capital=initial_capital,
        simulations=simulations,
        seed=seed + 1000,
        gate_params=best_candidate["gate_params"],
    )
    test_stress_summary = (
        run_stress_suite(
            test_rows,
            gate_params=best_candidate["gate_params"],
            initial_capital=initial_capital,
            simulations=max(300, simulations // 2),
            seed=seed + 5000,
        )
        if enable_stress_test
        else None
    )
    test_score = (
        _composite_score(test_result["summary"], test_stress_summary)
        if optimization_metric == "composite_score"
        else float(test_result["summary"].get(optimization_metric, 0.0))
    )
    payload = {
        "optimizer": "optuna" if get_optuna_status()["available"] else "grid_search_fallback",
        "optimization_metric": optimization_metric,
        "search_space": search_space,
        "best_gate_params": best_candidate["gate_params"],
        "train_summary": best_candidate["train_summary"],
        "train_stress_summary": best_candidate["train_stress_summary"],
        "train_score": best_candidate["train_score"],
        "test_summary": test_result["summary"],
        "test_stress_summary": test_stress_summary,
        "test_score": test_score,
        "candidate_count": len(candidate_rows),
    }

    write_json(output_dir / "strategy_optimization.json", payload)
    write_json(output_dir / "strategy_optimization_candidates.json", {"candidates": candidate_rows})
    log_tracking_payload(
        output_dir / "strategy_optimization_mlflow.json",
        run_name="decision_os_backtest_optimization",
        params=best_candidate["gate_params"],
        metrics={
            "train_alpha": best_candidate["train_summary"]["alpha"],
            "test_alpha": test_result["summary"]["alpha"],
            "train_composite_score": best_candidate["train_score"],
            "test_composite_score": test_score,
            "train_hit_rate": best_candidate["train_summary"]["decision_hit_rate"],
            "test_hit_rate": test_result["summary"]["decision_hit_rate"],
        },
    )
    return payload
