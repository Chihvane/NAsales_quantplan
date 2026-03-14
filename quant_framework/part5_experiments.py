from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import date
from statistics import mean

import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize, proportions_ztest

from .models import (
    ExperimentAssignmentRecord,
    ExperimentMetricRecord,
    ExperimentRecord,
    TrafficSessionRecord,
)
from .stats_utils import safe_divide


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def estimate_two_proportion_sample_size(
    baseline_rate: float,
    mde_absolute: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> dict:
    baseline_rate = max(0.0001, min(0.9999, baseline_rate))
    target_rate = max(0.0001, min(0.9999, baseline_rate + mde_absolute))
    effect_size = proportion_effectsize(baseline_rate, target_rate)
    sample_size = NormalIndPower().solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative="two-sided",
    )
    return {
        "baseline_rate": round(baseline_rate, 4),
        "target_rate": round(target_rate, 4),
        "mde_absolute": round(mde_absolute, 4),
        "alpha": alpha,
        "power": power,
        "sample_size_per_variant": int(round(sample_size)),
    }


def summarize_experiment_registry(
    experiments: list[ExperimentRecord],
    traffic_sessions: list[TrafficSessionRecord],
    min_weeks: int = 1,
) -> dict:
    if not experiments:
        return {}

    channels_with_traffic = {record.channel for record in traffic_sessions if record.channel}
    channels_with_experiments = {record.channel for record in experiments if record.channel}
    status_counts: dict[str, int] = defaultdict(int)
    mde_values = []
    durations = []
    for record in experiments:
        status_counts[record.status.lower()] += 1
        mde_values.append(record.mde)
        if record.start_date and record.end_date:
            start_date = _parse_date(record.start_date)
            end_date = _parse_date(record.end_date)
            if start_date is not None and end_date is not None:
                durations.append(max((end_date - start_date).days + 1, 1))

    total_sessions = sum(record.sessions for record in traffic_sessions)
    total_orders = sum(record.orders for record in traffic_sessions)
    baseline_conversion = safe_divide(total_orders, total_sessions)
    mde_absolute = mean(mde_values) if mde_values else 0.02
    sample_size = estimate_two_proportion_sample_size(
        baseline_conversion or 0.05,
        mde_absolute or 0.02,
    )

    days = sorted({record.date for record in traffic_sessions if record.date})
    span_days = len(days)
    velocity = safe_divide(len(experiments), max(span_days / 30, 1))
    min_duration_days = max(min_weeks * 7, 1)
    minimum_duration_pass_rate = safe_divide(
        sum(1 for duration in durations if duration >= min_duration_days),
        len(durations),
    ) if durations else 0.0

    return {
        "experiment_count": len(experiments),
        "completed_count": status_counts.get("completed", 0),
        "active_count": status_counts.get("active", 0),
        "draft_count": status_counts.get("draft", 0),
        "coverage_ratio": round(
            safe_divide(len(channels_with_experiments), max(len(channels_with_traffic), 1)),
            4,
        ),
        "test_velocity_per_30d": round(velocity, 2),
        "average_mde": round(mean(mde_values), 4) if mde_values else 0.0,
        "minimum_duration_pass_rate": round(minimum_duration_pass_rate, 4),
        "baseline_conversion_rate": round(baseline_conversion, 4),
        "sample_size_guidance": sample_size,
    }


def _choose_control_variant(variants: list[str]) -> str:
    normalized_lookup = {variant.lower(): variant for variant in variants}
    for candidate in ("control", "baseline", "a"):
        if candidate in normalized_lookup:
            return normalized_lookup[candidate]
    return sorted(variants)[0]


def _seed_from_key(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:8], "big")


def _build_grouped_variant_buckets(
    metric_rows: list[ExperimentMetricRecord],
) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {"exposures": 0, "conversions": 0, "value_total": 0.0, "date_count": 0}
    )
    for row in metric_rows:
        bucket = grouped[row.variant]
        bucket["exposures"] += row.exposures
        bucket["conversions"] += row.conversions
        bucket["value_total"] += row.value
        bucket["date_count"] += 1
    return grouped


def _estimate_prior_strength(total_exposures: int) -> float:
    if total_exposures <= 0:
        return 20.0
    return float(min(max(total_exposures ** 0.5, 20.0), 250.0))


def _prior_from_counts(conversions: int, exposures: int) -> dict:
    rate = safe_divide(conversions, exposures) if exposures > 0 else 0.05
    strength = _estimate_prior_strength(exposures)
    alpha = 1 + rate * strength
    beta = 1 + (1 - rate) * strength
    return {
        "rate": round(rate, 4),
        "strength": round(strength, 2),
        "alpha": alpha,
        "beta": beta,
    }


def _build_empirical_prior_context(
    experiments: list[ExperimentRecord],
    metrics: list[ExperimentMetricRecord],
) -> dict:
    experiment_lookup = {record.experiment_id: record for record in experiments}
    metric_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"conversions": 0, "exposures": 0})
    channel_metric_totals: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"conversions": 0, "exposures": 0}
    )
    for row in metrics:
        experiment = experiment_lookup.get(row.experiment_id)
        if experiment is None or row.metric_name != experiment.primary_metric:
            continue
        metric_bucket = metric_totals[row.metric_name]
        metric_bucket["conversions"] += row.conversions
        metric_bucket["exposures"] += row.exposures
        channel_bucket = channel_metric_totals[(experiment.channel, row.metric_name)]
        channel_bucket["conversions"] += row.conversions
        channel_bucket["exposures"] += row.exposures

    metric_priors = {
        metric_name: _prior_from_counts(values["conversions"], values["exposures"])
        for metric_name, values in metric_totals.items()
    }
    channel_metric_priors = {
        key: _prior_from_counts(values["conversions"], values["exposures"])
        for key, values in channel_metric_totals.items()
    }
    return {
        "metric": metric_priors,
        "channel_metric": channel_metric_priors,
    }


def _resolve_hierarchical_prior(
    channel: str,
    metric_name: str,
    prior_context: dict,
) -> dict:
    metric_prior = prior_context.get("metric", {}).get(metric_name)
    channel_metric_prior = prior_context.get("channel_metric", {}).get((channel, metric_name))
    if channel_metric_prior and metric_prior:
        total_strength = channel_metric_prior["strength"] + metric_prior["strength"]
        channel_weight = min(
            max(channel_metric_prior["strength"] / max(total_strength, 1.0), 0.35),
            0.8,
        )
        rate = channel_metric_prior["rate"] * channel_weight + metric_prior["rate"] * (1 - channel_weight)
        strength = min(channel_metric_prior["strength"] * 0.65 + metric_prior["strength"] * 0.35, 250.0)
        return {
            "level": "channel_metric_blend",
            "alpha": 1 + rate * strength,
            "beta": 1 + (1 - rate) * strength,
            "rate": round(rate, 4),
            "strength": round(strength, 2),
        }
    if channel_metric_prior:
        return {"level": "channel_metric", **channel_metric_prior}
    if metric_prior:
        return {"level": "metric_global", **metric_prior}
    fallback = _prior_from_counts(0, 0)
    return {"level": "fallback", **fallback}


def _bayesian_rate_comparison(
    control_conversions: int,
    control_exposures: int,
    treatment_conversions: int,
    treatment_exposures: int,
    seed_key: str,
    draws: int = 4000,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
) -> dict:
    control_alpha = prior_alpha + max(control_conversions, 0)
    control_beta = prior_beta + max(control_exposures - control_conversions, 0)
    treatment_alpha = prior_alpha + max(treatment_conversions, 0)
    treatment_beta = prior_beta + max(treatment_exposures - treatment_conversions, 0)

    rng = np.random.default_rng(_seed_from_key(seed_key))
    control_draws = rng.beta(control_alpha, control_beta, draws)
    treatment_draws = rng.beta(treatment_alpha, treatment_beta, draws)
    absolute_uplift_draws = treatment_draws - control_draws
    relative_uplift_draws = absolute_uplift_draws / np.maximum(control_draws, 1e-6)

    posterior_probability = float(np.mean(treatment_draws > control_draws))
    ci_low = float(np.quantile(absolute_uplift_draws, 0.025))
    ci_high = float(np.quantile(absolute_uplift_draws, 0.975))
    rel_ci_low = float(np.quantile(relative_uplift_draws, 0.025))
    rel_ci_high = float(np.quantile(relative_uplift_draws, 0.975))

    if posterior_probability >= 0.95 and ci_low > 0:
        decision = "win"
    elif posterior_probability <= 0.05 and ci_high < 0:
        decision = "loss"
    else:
        decision = "inconclusive"

    return {
        "posterior_probability_treatment_best": round(posterior_probability, 4),
        "posterior_expected_control_rate": round(float(np.mean(control_draws)), 4),
        "posterior_expected_treatment_rate": round(float(np.mean(treatment_draws)), 4),
        "posterior_expected_absolute_uplift": round(float(np.mean(absolute_uplift_draws)), 4),
        "posterior_expected_relative_uplift": round(float(np.mean(relative_uplift_draws)), 4),
        "posterior_ci_low": round(ci_low, 4),
        "posterior_ci_high": round(ci_high, 4),
        "posterior_relative_ci_low": round(rel_ci_low, 4),
        "posterior_relative_ci_high": round(rel_ci_high, 4),
        "bayesian_status": decision,
    }


def _build_slice_readouts(
    experiment: ExperimentRecord,
    metric_rows: list[ExperimentMetricRecord],
    assignment_count: int,
    prior_context: dict,
    stop_rule_context: dict | None = None,
) -> list[dict]:
    parsed_rows = []
    for row in metric_rows:
        parsed_rows.append((_parse_date(row.date), row))
    dated_rows = [(parsed_date, row) for parsed_date, row in parsed_rows if parsed_date is not None]
    unique_dates = sorted({parsed_date for parsed_date, _ in dated_rows})
    if len(unique_dates) < 2:
        return []

    midpoint = len(unique_dates) // 2
    first_half_dates = set(unique_dates[:midpoint])
    second_half_dates = set(unique_dates[midpoint:])
    slices = [
        ("early_window", [row for parsed_date, row in dated_rows if parsed_date in first_half_dates]),
        ("late_window", [row for parsed_date, row in dated_rows if parsed_date in second_half_dates]),
    ]
    slice_readouts = []
    for slice_name, rows in slices:
        if not rows:
            continue
        readout = _build_readout_row(
            experiment,
            rows,
            assignment_count=assignment_count,
            slice_name=slice_name,
            include_slices=False,
            prior_context=prior_context,
            stop_rule_context=stop_rule_context,
        )
        if readout is not None:
            slice_readouts.append(readout)
    return slice_readouts


def _runtime_days(experiment: ExperimentRecord, metric_rows: list[ExperimentMetricRecord]) -> int:
    start_date = _parse_date(experiment.start_date)
    end_date = _parse_date(experiment.end_date)
    if start_date is not None and end_date is not None:
        return max((end_date - start_date).days + 1, 1)
    parsed_dates = sorted(
        parsed_date
        for parsed_date in (_parse_date(row.date) for row in metric_rows)
        if parsed_date is not None
    )
    if len(parsed_dates) >= 2:
        return max((parsed_dates[-1] - parsed_dates[0]).days + 1, 1)
    return 0


def _build_stop_rule_decision(
    experiment: ExperimentRecord,
    sample_target_per_variant: int,
    min_runtime_days: int,
    runtime_days: int,
    control_exposures: int,
    treatment_exposures: int,
    hierarchical_summary: dict,
    temporal_consistency_score: float,
    thresholds: dict,
) -> dict:
    min_variant_exposures = min(control_exposures, treatment_exposures)
    sample_ratio = safe_divide(min_variant_exposures, max(sample_target_per_variant, 1))
    effect_floor = max(experiment.mde * thresholds["effect_floor_share_of_mde"], 0.002)
    hierarchical_abs_uplift = hierarchical_summary.get("posterior_expected_absolute_uplift", 0.0)
    hierarchical_prob = hierarchical_summary.get("posterior_probability_treatment_best", 0.5)
    ci_low = hierarchical_summary.get("posterior_ci_low", 0.0)
    ci_high = hierarchical_summary.get("posterior_ci_high", 0.0)
    runtime_pass = runtime_days >= min_runtime_days
    sample_pass = sample_ratio >= 1.0

    if runtime_pass and sample_ratio >= 1.0 and hierarchical_prob >= thresholds["ship_threshold"] and ci_low > 0 and temporal_consistency_score >= 0.6:
        decision = "ship_winner"
        reason = "后验胜率、样本量与时间切片一致性同时满足上线阈值。"
    elif runtime_pass and sample_ratio >= 0.8 and hierarchical_prob <= thresholds["loss_threshold"] and ci_high < 0:
        decision = "stop_for_loss"
        reason = "后验结果稳定偏负，继续投流或扩量的收益较低。"
    elif runtime_pass and sample_ratio >= 1.2 and thresholds["futility_lower"] <= hierarchical_prob <= thresholds["futility_upper"] and abs(hierarchical_abs_uplift) < effect_floor:
        decision = "stop_for_futility"
        reason = "已达到足够样本，但 uplift 仍落在无效区间内。"
    elif not runtime_pass or sample_ratio < 0.6:
        decision = "continue_collecting"
        reason = "运行时长或样本量不足，继续收集数据。"
    elif hierarchical_prob >= 0.9 and temporal_consistency_score >= 0.6:
        decision = "prepare_rollout"
        reason = "方向明确但尚未完全满足放量阈值，可准备扩量方案。"
    elif hierarchical_prob <= 0.1:
        decision = "watch_for_loss"
        reason = "负向概率较高，建议重点监控 guardrail 指标。"
    else:
        decision = "continue_collecting"
        reason = "当前证据不足以触发自动止损或放量。"

    confidence = min(
        1.0,
        sample_ratio * 0.45
        + min(runtime_days / max(min_runtime_days, 1), 1.0) * 0.2
        + abs(hierarchical_prob - 0.5) * 1.2 * 0.25
        + temporal_consistency_score * 0.1,
    )
    return {
        "auto_stop_decision": decision,
        "auto_stop_reason": reason,
        "sample_target_per_variant": int(sample_target_per_variant),
        "sample_ratio_to_target": round(sample_ratio, 4),
        "runtime_days": runtime_days,
        "minimum_runtime_days": min_runtime_days,
        "runtime_gate_pass": runtime_pass,
        "sample_gate_pass": sample_pass,
        "effect_floor_absolute": round(effect_floor, 4),
        "auto_stop_confidence": round(confidence, 4),
    }


def _build_readout_row(
    experiment: ExperimentRecord,
    metric_rows: list[ExperimentMetricRecord],
    assignment_count: int = 0,
    slice_name: str | None = None,
    include_slices: bool = True,
    prior_context: dict | None = None,
    stop_rule_context: dict | None = None,
) -> dict | None:
    primary_rows = [
        row for row in metric_rows if row.metric_name == experiment.primary_metric
    ]
    if not primary_rows:
        return None

    grouped = _build_grouped_variant_buckets(primary_rows)

    variants = list(grouped.keys())
    if len(variants) < 2:
        return None

    control_variant = _choose_control_variant(variants)
    treatment_variants = [variant for variant in variants if variant != control_variant]
    control = grouped[control_variant]
    treatment = {"exposures": 0, "conversions": 0, "value_total": 0.0}
    for variant in treatment_variants:
        bucket = grouped[variant]
        treatment["exposures"] += bucket["exposures"]
        treatment["conversions"] += bucket["conversions"]
        treatment["value_total"] += bucket["value_total"]

    if control["exposures"] <= 0 or treatment["exposures"] <= 0:
        return None

    control_rate = safe_divide(control["conversions"], control["exposures"])
    treatment_rate = safe_divide(treatment["conversions"], treatment["exposures"])
    relative_uplift = safe_divide(
        treatment_rate - control_rate,
        control_rate if control_rate > 0 else 1.0,
    )
    absolute_uplift = treatment_rate - control_rate

    statistic, p_value = proportions_ztest(
        [treatment["conversions"], control["conversions"]],
        [treatment["exposures"], control["exposures"]],
    )
    pooled_rate = safe_divide(
        treatment["conversions"] + control["conversions"],
        treatment["exposures"] + control["exposures"],
    )
    standard_error = (
        pooled_rate
        * (1 - pooled_rate)
        * (1 / max(treatment["exposures"], 1) + 1 / max(control["exposures"], 1))
    ) ** 0.5
    ci_low = absolute_uplift - 1.96 * standard_error
    ci_high = absolute_uplift + 1.96 * standard_error

    if p_value < 0.05 and absolute_uplift > 0:
        frequentist_status = "win"
    elif p_value < 0.05 and absolute_uplift < 0:
        frequentist_status = "loss"
    else:
        frequentist_status = "inconclusive"

    bayesian_summary = _bayesian_rate_comparison(
        control["conversions"],
        control["exposures"],
        treatment["conversions"],
        treatment["exposures"],
        seed_key=f"{experiment.experiment_id}:{slice_name or 'full'}:{experiment.primary_metric}",
    )
    resolved_prior = _resolve_hierarchical_prior(
        experiment.channel,
        experiment.primary_metric,
        prior_context or {},
    )
    hierarchical_summary = _bayesian_rate_comparison(
        control["conversions"],
        control["exposures"],
        treatment["conversions"],
        treatment["exposures"],
        seed_key=f"{experiment.experiment_id}:{slice_name or 'full'}:{experiment.primary_metric}:hierarchical",
        prior_alpha=resolved_prior["alpha"],
        prior_beta=resolved_prior["beta"],
    )

    if frequentist_status == bayesian_summary["bayesian_status"] == hierarchical_summary["bayesian_status"]:
        result = frequentist_status
    else:
        result = "inconclusive"

    slice_readouts = []
    if include_slices:
        slice_readouts = _build_slice_readouts(
            experiment,
            primary_rows,
            assignment_count,
            prior_context or {},
            stop_rule_context,
        )

    directional_slices = [
        row for row in slice_readouts if row.get("absolute_uplift") is not None
    ]
    direction_matches = [
        1
        for row in directional_slices
        if (row["absolute_uplift"] >= 0 and absolute_uplift >= 0)
        or (row["absolute_uplift"] < 0 and absolute_uplift < 0)
    ]
    temporal_consistency_score = (
        safe_divide(len(direction_matches), len(directional_slices))
        if directional_slices
        else 0.5
    )
    runtime_days = _runtime_days(experiment, primary_rows)
    sample_target = estimate_two_proportion_sample_size(
        max(control_rate, 0.0001),
        max(experiment.mde, 0.005),
    )["sample_size_per_variant"]
    stop_summary = _build_stop_rule_decision(
        experiment=experiment,
        sample_target_per_variant=sample_target,
        min_runtime_days=(stop_rule_context or {}).get("minimum_runtime_days", 7),
        runtime_days=runtime_days,
        control_exposures=int(control["exposures"]),
        treatment_exposures=int(treatment["exposures"]),
        hierarchical_summary=hierarchical_summary,
        temporal_consistency_score=temporal_consistency_score,
        thresholds={
            "ship_threshold": (stop_rule_context or {}).get("ship_threshold", 0.97),
            "loss_threshold": (stop_rule_context or {}).get("loss_threshold", 0.05),
            "futility_lower": (stop_rule_context or {}).get("futility_lower", 0.35),
            "futility_upper": (stop_rule_context or {}).get("futility_upper", 0.65),
            "effect_floor_share_of_mde": (stop_rule_context or {}).get("effect_floor_share_of_mde", 0.5),
        },
    )

    payload = {
        "experiment_id": experiment.experiment_id,
        "channel": experiment.channel,
        "primary_metric": experiment.primary_metric,
        "control_variant": control_variant,
        "treatment_variants": treatment_variants,
        "control_exposures": int(control["exposures"]),
        "treatment_exposures": int(treatment["exposures"]),
        "control_rate": round(control_rate, 4),
        "treatment_rate": round(treatment_rate, 4),
        "absolute_uplift": round(absolute_uplift, 4),
        "relative_uplift": round(relative_uplift, 4),
        "p_value": round(float(p_value), 4),
        "z_stat": round(float(statistic), 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "frequentist_status": frequentist_status,
        "readout_status": result,
        "slice_name": slice_name or "full_window",
        "assignment_count": assignment_count,
        "temporal_consistency_score": round(temporal_consistency_score, 4),
        "slice_readouts": slice_readouts,
    }
    payload.update(bayesian_summary)
    payload.update(
        {
            "hierarchical_prior_level": resolved_prior["level"],
            "hierarchical_prior_rate": resolved_prior["rate"],
            "hierarchical_prior_strength": resolved_prior["strength"],
            "hierarchical_probability_treatment_best": hierarchical_summary["posterior_probability_treatment_best"],
            "hierarchical_expected_control_rate": hierarchical_summary["posterior_expected_control_rate"],
            "hierarchical_expected_treatment_rate": hierarchical_summary["posterior_expected_treatment_rate"],
            "hierarchical_expected_absolute_uplift": hierarchical_summary["posterior_expected_absolute_uplift"],
            "hierarchical_expected_relative_uplift": hierarchical_summary["posterior_expected_relative_uplift"],
            "hierarchical_ci_low": hierarchical_summary["posterior_ci_low"],
            "hierarchical_ci_high": hierarchical_summary["posterior_ci_high"],
            "hierarchical_relative_ci_low": hierarchical_summary["posterior_relative_ci_low"],
            "hierarchical_relative_ci_high": hierarchical_summary["posterior_relative_ci_high"],
            "hierarchical_status": hierarchical_summary["bayesian_status"],
        }
    )
    payload.update(stop_summary)
    return payload


def summarize_experiment_readouts(
    experiments: list[ExperimentRecord],
    assignments: list[ExperimentAssignmentRecord],
    metrics: list[ExperimentMetricRecord],
    min_runtime_days: int = 7,
    stop_thresholds: dict | None = None,
) -> dict:
    if not experiments:
        return {}

    experiment_lookup = {record.experiment_id: record for record in experiments}
    prior_context = _build_empirical_prior_context(experiments, metrics)
    metrics_by_experiment: dict[str, list[ExperimentMetricRecord]] = defaultdict(list)
    for row in metrics:
        metrics_by_experiment[row.experiment_id].append(row)

    assignments_by_experiment: dict[str, int] = defaultdict(int)
    for row in assignments:
        assignments_by_experiment[row.experiment_id] += 1

    readout_rows = []
    experiments_without_readouts = []
    for experiment in experiments:
        readout = _build_readout_row(
            experiment,
            metrics_by_experiment.get(experiment.experiment_id, []),
            assignment_count=assignments_by_experiment.get(experiment.experiment_id, 0),
            prior_context=prior_context,
            stop_rule_context={
                "minimum_runtime_days": min_runtime_days,
                **(stop_thresholds or {}),
            },
        )
        if readout is not None:
            readout_rows.append(readout)
        else:
            experiments_without_readouts.append(
                {
                    "experiment_id": experiment.experiment_id,
                    "channel": experiment.channel,
                    "status": experiment.status,
                    "reason": "缺少 primary metric 读数或无法形成 control/treatment 对比。",
                }
            )

    readout_count = len(readout_rows)
    completed_experiments = [record for record in experiments if record.status.lower() == "completed"]
    win_count = sum(1 for row in readout_rows if row["readout_status"] == "win")
    loss_count = sum(1 for row in readout_rows if row["readout_status"] == "loss")
    inconclusive_count = sum(1 for row in readout_rows if row["readout_status"] == "inconclusive")
    bayesian_win_count = sum(1 for row in readout_rows if row["bayesian_status"] == "win")
    bayesian_loss_count = sum(1 for row in readout_rows if row["bayesian_status"] == "loss")
    hierarchical_win_count = sum(1 for row in readout_rows if row["hierarchical_status"] == "win")
    hierarchical_loss_count = sum(1 for row in readout_rows if row["hierarchical_status"] == "loss")
    experiments_with_assignments = {row.experiment_id for row in assignments if row.experiment_id in experiment_lookup}
    auto_stop_counts: dict[str, int] = defaultdict(int)
    for row in readout_rows:
        auto_stop_counts[row["auto_stop_decision"]] += 1

    hierarchical_prior_levels: dict[str, int] = defaultdict(int)
    for row in readout_rows:
        hierarchical_prior_levels[row.get("hierarchical_prior_level", "unknown")] += 1

    return {
        "readout_count": readout_count,
        "readout_coverage_ratio": round(
            safe_divide(readout_count, max(len(completed_experiments), 1)),
            4,
        ),
        "assignment_coverage_ratio": round(
            safe_divide(len(experiments_with_assignments), max(len(experiments), 1)),
            4,
        ),
        "win_count": win_count,
        "loss_count": loss_count,
        "inconclusive_count": inconclusive_count,
        "bayesian_win_count": bayesian_win_count,
        "bayesian_loss_count": bayesian_loss_count,
        "hierarchical_win_count": hierarchical_win_count,
        "hierarchical_loss_count": hierarchical_loss_count,
        "winning_experiment_share": round(safe_divide(win_count, max(readout_count, 1)), 4),
        "average_posterior_win_probability": round(
            mean(row["posterior_probability_treatment_best"] for row in readout_rows),
            4,
        ) if readout_rows else 0.0,
        "average_hierarchical_win_probability": round(
            mean(row["hierarchical_probability_treatment_best"] for row in readout_rows),
            4,
        ) if readout_rows else 0.0,
        "average_relative_uplift": round(
            mean(row["relative_uplift"] for row in readout_rows),
            4,
        ) if readout_rows else 0.0,
        "average_hierarchical_relative_uplift": round(
            mean(row["hierarchical_expected_relative_uplift"] for row in readout_rows),
            4,
        ) if readout_rows else 0.0,
        "temporal_consistency_score": round(
            mean(
                row.get("temporal_consistency_score", 0.0)
                for row in readout_rows
                if row.get("slice_name") == "full_window"
            ),
            4,
        ) if readout_rows else 0.0,
        "auto_stop_summary": {
            "ship_winner_count": auto_stop_counts.get("ship_winner", 0),
            "stop_for_loss_count": auto_stop_counts.get("stop_for_loss", 0),
            "stop_for_futility_count": auto_stop_counts.get("stop_for_futility", 0),
            "prepare_rollout_count": auto_stop_counts.get("prepare_rollout", 0),
            "watch_for_loss_count": auto_stop_counts.get("watch_for_loss", 0),
            "continue_collecting_count": auto_stop_counts.get("continue_collecting", 0),
        },
        "auto_stop_enabled": True,
        "hierarchical_prior_mix": dict(hierarchical_prior_levels),
        "experiments_without_readouts": experiments_without_readouts,
        "experiment_readouts": sorted(
            readout_rows,
            key=lambda row: (
                row["readout_status"],
                row["hierarchical_probability_treatment_best"],
                row["posterior_probability_treatment_best"],
                row["relative_uplift"],
            ),
            reverse=True,
        ),
    }
