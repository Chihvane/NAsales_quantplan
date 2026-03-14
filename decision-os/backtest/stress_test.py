from __future__ import annotations

from copy import deepcopy

from backtest.walk_forward_engine import run_walk_forward_backtest


DEFAULT_STRESS_SCENARIOS: dict[str, dict[str, float]] = {
    "freight_up_40": {
        "landed_cost_multiplier": 1.40,
    },
    "cpc_up_50": {
        "platform_fee_multiplier": 1.50,
    },
    "demand_drop_20": {
        "tam_multiplier": 0.80,
        "cagr_shift": -0.03,
        "expected_price_multiplier": 0.94,
        "volatility_multiplier": 1.15,
        "forward_return_shift": -0.04,
        "benchmark_return_shift": -0.02,
    },
    "return_rate_shock": {
        "expected_price_multiplier": 0.96,
        "volatility_multiplier": 1.20,
        "forward_return_shift": -0.06,
    },
    "capital_cut_30": {
        "capital_multiplier": 0.70,
    },
}


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def apply_stress_scenario(
    panel_rows: list[dict[str, str | float]],
    scenario_config: dict[str, float],
) -> list[dict[str, str | float]]:
    stressed_rows = deepcopy(panel_rows)
    for row in stressed_rows:
        if "tam_multiplier" in scenario_config:
            row["TAM"] = round(float(row["TAM"]) * scenario_config["tam_multiplier"], 2)
        if "cagr_shift" in scenario_config:
            row["CAGR"] = round(_clip(float(row["CAGR"]) + scenario_config["cagr_shift"], 0.0, 1.0), 6)
        if "volatility_multiplier" in scenario_config:
            row["volatility"] = round(
                _clip(float(row["volatility"]) * scenario_config["volatility_multiplier"], 0.01, 1.0),
                6,
            )
        if "landed_cost_multiplier" in scenario_config:
            row["landed_cost"] = round(float(row["landed_cost"]) * scenario_config["landed_cost_multiplier"], 2)
        if "expected_price_multiplier" in scenario_config:
            row["expected_price"] = round(float(row["expected_price"]) * scenario_config["expected_price_multiplier"], 2)
        if "platform_fee_multiplier" in scenario_config:
            row["platform_fee"] = round(float(row["platform_fee"]) * scenario_config["platform_fee_multiplier"], 2)
        if "forward_return_shift" in scenario_config:
            row["forward_return_rate"] = round(
                _clip(float(row["forward_return_rate"]) + scenario_config["forward_return_shift"], -0.99, 2.0),
                6,
            )
        if "benchmark_return_shift" in scenario_config:
            row["benchmark_return_rate"] = round(
                _clip(float(row["benchmark_return_rate"]) + scenario_config["benchmark_return_shift"], -0.99, 2.0),
                6,
            )
    return stressed_rows


def _scenario_score(summary: dict[str, float | int | list[float]]) -> float:
    alpha = float(summary.get("alpha", 0.0))
    drawdown = abs(float(summary.get("strategy_max_drawdown", 0.0)))
    hit_rate = float(summary.get("decision_hit_rate", 0.0))
    selectivity = 1.0 - min(abs(float(summary.get("go_ratio", 0.0)) - 0.55) / 0.55, 1.0)

    alpha_score = 1.0 if alpha >= 0 else max(0.0, 1.0 + alpha)
    drawdown_score = max(0.0, 1.0 - drawdown / 0.35)
    return round(
        alpha_score * 0.4 + drawdown_score * 0.3 + hit_rate * 0.2 + selectivity * 0.1,
        6,
    )


def run_stress_suite(
    panel_rows: list[dict[str, str | float]],
    *,
    gate_params: dict[str, float] | None = None,
    initial_capital: float = 1_000_000,
    max_loss_probability: float = 0.30,
    max_drawdown: float = 0.20,
    simulations: int = 1200,
    seed: int = 42,
    scenario_library: dict[str, dict[str, float]] | None = None,
) -> dict[str, object]:
    scenario_library = scenario_library or DEFAULT_STRESS_SCENARIOS
    scenario_rows: list[dict[str, object]] = []

    for scenario_index, (scenario_id, scenario_config) in enumerate(scenario_library.items()):
        stressed_panel = apply_stress_scenario(panel_rows, scenario_config)
        stressed_capital = initial_capital * scenario_config.get("capital_multiplier", 1.0)
        result = run_walk_forward_backtest(
            stressed_panel,
            initial_capital=stressed_capital,
            max_loss_probability=max_loss_probability,
            max_drawdown=max_drawdown,
            simulations=simulations,
            seed=seed + (scenario_index + 1) * 500,
            gate_params=gate_params,
        )
        summary = result["summary"]
        scenario_rows.append(
            {
                "scenario_id": scenario_id,
                "capital_multiplier": scenario_config.get("capital_multiplier", 1.0),
                "summary": summary,
                "scenario_score": _scenario_score(summary),
            }
        )

    robustness_score = (
        round(sum(float(row["scenario_score"]) for row in scenario_rows) / len(scenario_rows), 6)
        if scenario_rows
        else 0.0
    )
    return {
        "scenario_count": len(scenario_rows),
        "robustness_score": robustness_score,
        "scenarios": scenario_rows,
    }
