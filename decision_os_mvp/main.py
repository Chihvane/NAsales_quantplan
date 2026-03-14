from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decision_os_mvp.capital_risk import CapitalState, RiskBudget
from decision_os_mvp.gate_engine import GateEngine
from decision_os_mvp.models import compute_market_factor, monte_carlo_profit_simulation
from decision_os_mvp.sample_data import generate_sample_market_data


def run_decision_flow() -> dict[str, float | str]:
    data = generate_sample_market_data()
    factor_score = compute_market_factor(data)
    model_outputs = monte_carlo_profit_simulation(data)

    capital_state = CapitalState(total=2_000_000, allocated=1_200_000)
    risk_budget = RiskBudget(max_loss_probability=0.3, max_drawdown=0.2)
    required_capital = 500_000

    gate = GateEngine()
    decision = gate.evaluate(
        factor_score=factor_score,
        model_outputs=model_outputs,
        capital_state=capital_state,
        risk_budget=risk_budget,
        required_capital=required_capital,
    )

    result = {
        "market_factor": round(factor_score, 3),
        "profit_p10": round(model_outputs["profit_p10"], 2),
        "profit_p50": round(model_outputs["profit_p50"], 2),
        "profit_p90": round(model_outputs["profit_p90"], 2),
        "loss_probability": round(model_outputs["loss_probability"], 3),
        "free_capital": capital_state.free,
        "decision": decision,
    }

    print("=== Decision OS v3.0 ===")
    print("Market Factor:", result["market_factor"])
    print("Profit P10:", result["profit_p10"])
    print("Profit P50:", result["profit_p50"])
    print("Profit P90:", result["profit_p90"])
    print("Loss Probability:", result["loss_probability"])
    print("Free Capital:", result["free_capital"])
    print("Decision:", result["decision"])
    return result


if __name__ == "__main__":
    run_decision_flow()
