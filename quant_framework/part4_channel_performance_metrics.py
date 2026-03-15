from __future__ import annotations

from .models import ChannelBenchmarkRecord, EvidenceSourceRecord, GateThresholdRecord
from .stats_utils import clip, safe_divide


def _threshold_value(
    threshold_registry: list[GateThresholdRecord],
    metric_names: set[str],
    default_value: float,
) -> float:
    for row in threshold_registry:
        if row.metric_name in metric_names:
            return row.threshold_value
    return default_value


def compute_part4_channel_performance_metrics(
    channel_rows: list[dict],
    benchmark_registry: list[ChannelBenchmarkRecord],
    threshold_registry: list[GateThresholdRecord],
    source_registry: list[EvidenceSourceRecord] | None = None,
) -> dict:
    if not channel_rows:
        return {}

    benchmark_lookup = {row.channel: row for row in benchmark_registry}
    margin_floor = _threshold_value(
        threshold_registry,
        {"contribution_margin_rate", "margin_gate", "min_contribution_margin_rate"},
        0.08,
    )
    inventory_days_limit = _threshold_value(
        threshold_registry,
        {"inventory_days", "max_inventory_days"},
        45.0,
    )
    max_execution_friction = _threshold_value(
        threshold_registry,
        {"execution_friction_score", "max_execution_friction"},
        0.55,
    )
    grade_scores = {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.4}
    source_registry = source_registry or []
    expected_topics = {"traffic_sessions", "marketing_spend", "channel_rate_cards", "sold_transactions", "returns_claims"}
    observed_topics = {row.topic for row in source_registry if row.topic}
    source_coverage_ratio = safe_divide(len(observed_topics & expected_topics), len(expected_topics))
    freshness_score = 1 - min(
        safe_divide(sum(max(row.freshness_days, 0) for row in source_registry), max(len(source_registry), 1), default=999.0) / 30.0,
        1.0,
    ) if source_registry else 0.0
    source_confidence_score = safe_divide(
        sum(grade_scores.get(row.confidence_grade.upper(), 0.5) for row in source_registry),
        max(len(source_registry), 1),
    ) if source_registry else 0.0
    source_health_score = clip(
        source_coverage_ratio * 0.45
        + freshness_score * 0.25
        + source_confidence_score * 0.3,
        0.0,
        1.0,
    )
    performance_rows = []
    execution_friction_flags = set()
    for row in channel_rows:
        benchmark = benchmark_lookup.get(row["channel"])
        if benchmark is None:
            benchmark_gap = {}
            benchmark_fit_score = 0.45
            cac_gap = 0.0
        else:
            conversion_gap = safe_divide(
                row["conversion_rate"] - benchmark.benchmark_conversion_rate,
                benchmark.benchmark_conversion_rate,
            )
            aov_gap = safe_divide(
                row["aov"] - benchmark.benchmark_average_order_value,
                benchmark.benchmark_average_order_value,
            )
            roi_gap = safe_divide(
                row["roi"] - benchmark.benchmark_roas,
                max(abs(benchmark.benchmark_roas), 0.01),
            )
            cac_gap = safe_divide(
                benchmark.benchmark_cac - row["cac"],
                max(benchmark.benchmark_cac, 0.01),
            ) if benchmark.benchmark_cac else 0.0
            benchmark_fit_score = clip(
                (conversion_gap + 1) / 2 * 0.3
                + (aov_gap + 1) / 2 * 0.2
                + (roi_gap + 1) / 2 * 0.3
                + (cac_gap + 1) / 2 * 0.2,
                0.0,
                1.0,
            )
            benchmark_gap = {
                "conversion_gap_ratio": round(conversion_gap, 4),
                "aov_gap_ratio": round(aov_gap, 4),
                "roi_gap_ratio": round(roi_gap, 4),
                "cac_gap_ratio": round(cac_gap, 4),
            }

        turnover_penalty_score = clip(
            safe_divide(max(row.get("inventory_days", 0.0) - inventory_days_limit, 0.0), max(inventory_days_limit, 1.0)),
            0.0,
            1.0,
        )
        cac_slippage_ratio = round(max(-cac_gap, 0.0), 4) if benchmark is not None else 0.0
        fee_burden_rate = safe_divide(
            row.get("channel_fees_total", 0.0)
            + row.get("payment_cost_total", 0.0)
            + row.get("fulfillment_cost_total", 0.0)
            + row.get("storage_cost_total", 0.0),
            max(row.get("revenue", 0.0), 1.0),
        )
        fee_jump_risk_score = clip(safe_divide(max(row.get("fee_version_count", 0) - 1, 0), 2.0), 0.0, 1.0)
        policy_jump_risk_score = clip(
            max(fee_jump_risk_score, row.get("dispute_rate", 0.0) * 4.0),
            0.0,
            1.0,
        )
        execution_friction_score = clip(
            turnover_penalty_score * 0.25
            + cac_slippage_ratio * 0.25
            + clip(fee_burden_rate / 0.35, 0.0, 1.0) * 0.2
            + policy_jump_risk_score * 0.15
            + clip(row.get("return_rate", 0.0) / 0.12, 0.0, 1.0) * 0.15,
            0.0,
            1.0,
        )
        friction_flags = []
        if turnover_penalty_score >= 0.2:
            friction_flags.append("inventory_turnover_penalty")
        if cac_slippage_ratio >= 0.15:
            friction_flags.append("cac_slippage")
        if fee_jump_risk_score >= 0.35:
            friction_flags.append("fee_jump_risk")
        if policy_jump_risk_score >= 0.4:
            friction_flags.append("policy_jump_risk")
        if execution_friction_score >= max_execution_friction:
            friction_flags.append("execution_friction_high")
        execution_friction_flags.update(friction_flags)
        gate_results = {
            "margin_gate": row["contribution_margin_rate"] >= margin_floor,
            "benchmark_fit_gate": benchmark_fit_score >= 0.5,
            "execution_friction_gate": execution_friction_score <= max_execution_friction,
        }
        performance_rows.append(
            {
                "channel": row["channel"],
                "channel_family": row["channel_family"],
                "benchmark_gap": benchmark_gap,
                "benchmark_fit_score": round(benchmark_fit_score, 4),
                "risk_adjusted_profit": round(row.get("contribution_profit", 0.0) * (1 - execution_friction_score), 2),
                "turnover_penalty_score": round(turnover_penalty_score, 4),
                "cac_slippage_ratio": round(cac_slippage_ratio, 4),
                "fee_burden_rate": round(fee_burden_rate, 4),
                "fee_jump_risk_score": round(fee_jump_risk_score, 4),
                "policy_jump_risk_score": round(policy_jump_risk_score, 4),
                "execution_friction_score": round(execution_friction_score, 4),
                "execution_friction_flags": friction_flags,
                "gate_results": gate_results,
            }
        )

    coverage_ratio = round(
        safe_divide(
            sum(1 for row in performance_rows if row["benchmark_gap"]),
            len(performance_rows),
        ),
        4,
    )
    return {
        "channel_rows": performance_rows,
        "benchmark_coverage_ratio": coverage_ratio,
        "threshold_coverage_ratio": round(
            safe_divide(
                sum(
                    1
                    for row in threshold_registry
                    if row.metric_name
                    in {
                        "contribution_margin_rate",
                        "margin_gate",
                        "min_contribution_margin_rate",
                        "execution_friction_score",
                        "max_execution_friction",
                        "inventory_days",
                        "max_inventory_days",
                    }
                ),
                3,
            ),
            4,
        ),
        "threshold_registry_count": len(threshold_registry),
        "benchmark_registry_count": len(benchmark_registry),
        "source_registry_count": len(source_registry),
        "source_health": {
            "coverage_ratio": round(source_coverage_ratio, 4),
            "freshness_score": round(freshness_score, 4),
            "confidence_score": round(source_confidence_score, 4),
            "health_score": round(source_health_score, 4),
        },
        "average_benchmark_fit_score": round(
            sum(row["benchmark_fit_score"] for row in performance_rows) / len(performance_rows),
            4,
        ),
        "average_execution_friction_score": round(
            sum(row["execution_friction_score"] for row in performance_rows) / len(performance_rows),
            4,
        ),
        "average_turnover_penalty_score": round(
            sum(row["turnover_penalty_score"] for row in performance_rows) / len(performance_rows),
            4,
        ),
        "average_cac_slippage_ratio": round(
            sum(row["cac_slippage_ratio"] for row in performance_rows) / len(performance_rows),
            4,
        ),
        "execution_friction_flags": sorted(execution_friction_flags),
        "channel_gate_records": [
            {
                "channel": row["channel"],
                "gate_results": row["gate_results"],
                "execution_friction_flags": row["execution_friction_flags"],
            }
            for row in performance_rows
        ],
    }
