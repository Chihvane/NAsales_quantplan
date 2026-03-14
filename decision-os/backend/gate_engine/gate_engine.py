from __future__ import annotations

from backend.gate_engine.rule_parser import compare


def evaluate_market_gate(
    factor_score: float,
    model_outputs: dict[str, float],
    capital_state: dict[str, float],
    risk_state: dict[str, float],
    required_capital: float,
    candidate_features: dict[str, float] | None = None,
    thresholds: dict[str, float] | None = None,
) -> str:
    candidate_features = candidate_features or {}
    thresholds = thresholds or {}
    min_profit_p50 = thresholds.get("min_profit_p50", 0.0)
    min_factor_score = thresholds.get("min_factor_score", 0.5)
    max_loss_probability = thresholds.get(
        "max_loss_probability",
        risk_state["max_loss_probability"],
    )
    min_profit_p10 = thresholds.get("min_profit_p10")
    min_margin_p50_ratio = thresholds.get("min_margin_p50_ratio")
    max_volatility = thresholds.get("max_volatility")
    max_hhi = thresholds.get("max_hhi")
    max_required_capital_ratio = thresholds.get("max_required_capital_ratio")

    total_capital = float(
        capital_state.get(
            "total_capital",
            capital_state.get("free_capital", required_capital),
        )
    )

    if not compare(model_outputs["profit_p50"], ">=", min_profit_p50):
        return "NO_GO_PROFIT"
    if min_profit_p10 is not None and not compare(model_outputs.get("profit_p10", 0.0), ">=", min_profit_p10):
        return "NO_GO_PROFIT_TAIL"
    if min_margin_p50_ratio is not None and not compare(
        model_outputs.get("margin_p50_ratio", 0.0),
        ">=",
        min_margin_p50_ratio,
    ):
        return "NO_GO_MARGIN"
    if not compare(model_outputs["loss_probability"], "<=", max_loss_probability):
        return "NO_GO_RISK"
    if not compare(factor_score, ">=", min_factor_score):
        return "NO_GO_FACTOR"
    if max_volatility is not None and "volatility" in candidate_features:
        if not compare(float(candidate_features["volatility"]), "<=", max_volatility):
            return "NO_GO_VOLATILITY"
    if max_hhi is not None and "hhi" in candidate_features:
        if not compare(float(candidate_features["hhi"]), "<=", max_hhi):
            return "NO_GO_CONCENTRATION"
    if max_required_capital_ratio is not None and total_capital > 0:
        required_capital_ratio = required_capital / total_capital
        if not compare(required_capital_ratio, "<=", max_required_capital_ratio):
            return "NO_GO_CAPITAL_SHARE"
    if not compare(required_capital, "<=", capital_state["free_capital"]):
        return "NO_GO_CAPITAL"
    return "GO"
