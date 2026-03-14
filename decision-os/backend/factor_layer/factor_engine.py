from __future__ import annotations

from backend.factor_layer.normalization import bounded_score


def compute_market_factor(data: dict[str, float]) -> float:
    tam_score = bounded_score(data["TAM"] / 200_000_000)
    growth_score = bounded_score(data["CAGR"] / 0.20)
    competition_score = bounded_score(1 - (data["HHI"] / 5000))
    stability_score = bounded_score(1 - data["volatility"])
    return (
        tam_score * 0.25
        + growth_score * 0.25
        + competition_score * 0.25
        + stability_score * 0.25
    )
