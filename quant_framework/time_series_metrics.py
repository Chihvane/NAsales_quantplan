from __future__ import annotations

from math import log

import numpy as np

from .stats_utils import clip, safe_divide


def shannon_entropy(values: list[float], bins: int = 8) -> float:
    if len(values) < 2:
        return 0.0
    effective_bins = min(max(bins, 3), len(values))
    counts, _ = np.histogram(np.asarray(values, dtype=float), bins=effective_bins)
    probabilities = counts[counts > 0] / counts.sum()
    if len(probabilities) <= 1:
        return 0.0
    entropy = float(-np.sum(probabilities * np.log(probabilities)))
    return clip(safe_divide(entropy, log(len(probabilities)), default=0.0), 0.0, 1.0)


def approximate_entropy(values: list[float], m: int = 2, r_ratio: float = 0.2) -> float:
    x = np.asarray(values, dtype=float)
    if x.size <= m + 1:
        return 0.0
    sigma = float(np.std(x))
    tolerance = sigma * r_ratio if sigma > 0 else r_ratio

    def _phi(mm: int) -> float:
        patterns = np.array([x[index : index + mm] for index in range(x.size - mm + 1)])
        if patterns.size == 0:
            return 0.0
        counts = []
        for pattern in patterns:
            distances = np.max(np.abs(patterns - pattern), axis=1)
            counts.append(np.mean(distances <= tolerance))
        counts = np.asarray(counts, dtype=float)
        counts = counts[counts > 0]
        return float(np.mean(np.log(counts))) if counts.size else 0.0

    raw = abs(_phi(m) - _phi(m + 1))
    return clip(raw, 0.0, 1.0)


def fft_seasonality_features(
    values: list[float],
    *,
    sample_spacing: float = 1.0,
    top_k: int = 3,
) -> dict:
    if len(values) < 4:
        return {
            "observation_count": len(values),
            "dominant_period": None,
            "dominant_power_share": 0.0,
            "spectral_entropy": 0.0,
            "seasonality_confidence_score": 0.0,
            "top_periods": [],
        }

    x = np.asarray(values, dtype=float)
    centered = x - np.mean(x)
    spectrum = np.fft.rfft(centered)
    frequencies = np.fft.rfftfreq(centered.size, d=sample_spacing)
    power = np.abs(spectrum) ** 2
    positive_mask = frequencies > 0
    if not np.any(positive_mask):
        return {
            "observation_count": len(values),
            "dominant_period": None,
            "dominant_power_share": 0.0,
            "spectral_entropy": 0.0,
            "seasonality_confidence_score": 0.0,
            "top_periods": [],
        }

    positive_frequencies = frequencies[positive_mask]
    positive_power = power[positive_mask]
    total_power = float(np.sum(positive_power)) or 1.0
    ranking = np.argsort(positive_power)[::-1]
    top_periods = []
    for rank_index in ranking[:top_k]:
        frequency = float(positive_frequencies[rank_index])
        period = safe_divide(1.0, frequency, default=0.0)
        top_periods.append(
            {
                "period": round(period, 4) if period else None,
                "power_share": round(float(positive_power[rank_index] / total_power), 4),
            }
        )

    power_probabilities = positive_power / total_power
    spectral_entropy_raw = float(-np.sum(power_probabilities * np.log(power_probabilities + 1e-12)))
    spectral_entropy_max = log(len(power_probabilities)) if len(power_probabilities) > 1 else 1.0
    spectral_entropy = clip(safe_divide(spectral_entropy_raw, spectral_entropy_max, default=0.0), 0.0, 1.0)
    dominant_power_share = float(positive_power[ranking[0]] / total_power)
    seasonality_confidence_score = clip(dominant_power_share * (1 - spectral_entropy), 0.0, 1.0)

    return {
        "observation_count": len(values),
        "dominant_period": top_periods[0]["period"] if top_periods else None,
        "dominant_power_share": round(dominant_power_share, 4),
        "spectral_entropy": round(spectral_entropy, 4),
        "seasonality_confidence_score": round(seasonality_confidence_score, 4),
        "top_periods": top_periods,
    }
