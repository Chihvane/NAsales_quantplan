from __future__ import annotations

import argparse
import json
from pathlib import Path

from .charts import (
    generate_horizontal_system_chart_assets,
    generate_part0_chart_assets,
    generate_part1_chart_assets,
    generate_part2_chart_assets,
    generate_part3_chart_assets,
    generate_part4_chart_assets,
    generate_part5_chart_assets,
)
from .backtest import (
    build_part2_backtest_panel_from_directory,
    load_backtest_panel,
    load_part2_backtest_panel,
    load_part3_backtest_panel,
    load_part4_backtest_panel,
    load_part5_backtest_panel,
    run_part2_backtest_demo,
    run_part2_competition_backtest,
    run_part3_backtest_demo,
    run_part3_supply_backtest,
    run_part4_backtest_demo,
    run_part4_channel_backtest,
    run_part5_backtest_demo,
    run_part5_operating_backtest,
    run_backtest_demo,
    run_full_backtest_suite,
    run_market_opportunity_backtest,
    write_backtest_curve_svg,
    write_backtest_monthly_csv,
)
from .cleaners import (
    combine_part2_bundles,
    normalize_amazon_listings_export,
    normalize_amazon_part2_export,
    normalize_ebay_transactions_export,
    normalize_ebay_part2_export,
    normalize_part3_compliance_export,
    normalize_part3_logistics_export,
    normalize_part3_rfq_export,
    normalize_part3_shipment_export,
    normalize_part3_suppliers_export,
    normalize_part3_tariff_export,
    normalize_tiktok_part2_export,
    normalize_tiktok_listings_export,
    normalize_tiktok_channels_export,
)
from .io_utils import write_json
from .models import HorizontalSystemAssumptions, MarketSizeAssumptions, Part0Assumptions, Part2Assumptions, Part3Assumptions, Part4Assumptions, Part5Assumptions
from .horizontal_pipeline import (
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from .horizontal_system import build_horizontal_system_report
from .part0 import build_part0_quant_report
from .part0_pipeline import (
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from .part1 import build_part1_quant_report
from .part2 import build_part2_quant_report
from .part3 import build_part3_quant_report
from .part4 import build_part4_quant_report
from .part5 import build_part5_quant_report
from .part5_etl import run_part5_etl_skeleton
from .part2_pipeline import (
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)
from .part3_pipeline import (
    DEFAULT_PART3_ASSUMPTIONS,
    build_part3_dataset_from_directory,
)
from .part4_pipeline import (
    DEFAULT_PART4_ASSUMPTIONS,
    build_part4_dataset_from_directory,
)
from .part5_pipeline import (
    DEFAULT_PART5_ASSUMPTIONS,
    build_part5_dataset_from_directory,
)
from .pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory
from .reporting import build_cli_summary


def _part0_assumptions_from_args(args: argparse.Namespace) -> Part0Assumptions:
    return Part0Assumptions(
        required_gate_count=args.required_gate_count,
        required_decision_domains=args.required_decision_domains,
        required_policy_scopes=args.required_policy_scopes,
        required_strategic_metric_families=args.required_strategic_metric_families,
        max_source_age_days=args.max_source_age_days,
        max_assumption_overdue_days=args.max_assumption_overdue_days,
        minimum_signoff_steps=args.minimum_signoff_steps,
        required_naming_style=args.required_naming_style,
    )


def _horizontal_system_assumptions_from_args(args: argparse.Namespace) -> HorizontalSystemAssumptions:
    return HorizontalSystemAssumptions(
        required_entity_types=args.required_entity_types,
        required_rule_scenarios=args.required_rule_scenarios,
        min_dictionary_approval_ratio=args.min_dictionary_approval_ratio,
        min_reproducibility_ratio=args.min_reproducibility_ratio,
        min_trigger_resolution_ratio=args.min_trigger_resolution_ratio,
        max_traceback_minutes=args.max_traceback_minutes,
    )


def _add_part0_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--required-gate-count", type=int, default=DEFAULT_PART0_ASSUMPTIONS.required_gate_count)
    parser.add_argument("--required-decision-domains", type=int, default=DEFAULT_PART0_ASSUMPTIONS.required_decision_domains)
    parser.add_argument("--required-policy-scopes", type=int, default=DEFAULT_PART0_ASSUMPTIONS.required_policy_scopes)
    parser.add_argument("--required-strategic-metric-families", type=int, default=DEFAULT_PART0_ASSUMPTIONS.required_strategic_metric_families)
    parser.add_argument("--max-source-age-days", type=int, default=DEFAULT_PART0_ASSUMPTIONS.max_source_age_days)
    parser.add_argument("--max-assumption-overdue-days", type=int, default=DEFAULT_PART0_ASSUMPTIONS.max_assumption_overdue_days)
    parser.add_argument("--minimum-signoff-steps", type=int, default=DEFAULT_PART0_ASSUMPTIONS.minimum_signoff_steps)
    parser.add_argument("--required-naming-style", default=DEFAULT_PART0_ASSUMPTIONS.required_naming_style)


def _add_horizontal_system_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--required-entity-types", type=int, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.required_entity_types)
    parser.add_argument("--required-rule-scenarios", type=int, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.required_rule_scenarios)
    parser.add_argument("--min-dictionary-approval-ratio", type=float, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.min_dictionary_approval_ratio)
    parser.add_argument("--min-reproducibility-ratio", type=float, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.min_reproducibility_ratio)
    parser.add_argument("--min-trigger-resolution-ratio", type=float, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.min_trigger_resolution_ratio)
    parser.add_argument("--max-traceback-minutes", type=int, default=DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS.max_traceback_minutes)


def _assumptions_from_args(args: argparse.Namespace) -> MarketSizeAssumptions:
    return MarketSizeAssumptions(
        tam=args.tam,
        online_penetration=args.online_penetration,
        importable_share=args.importable_share,
        target_capture_share=args.target_capture_share,
        sample_coverage=args.sample_coverage,
    )


def _add_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tam", type=float, default=DEFAULT_ASSUMPTIONS.tam)
    parser.add_argument(
        "--online-penetration",
        type=float,
        default=DEFAULT_ASSUMPTIONS.online_penetration,
    )
    parser.add_argument(
        "--importable-share",
        type=float,
        default=DEFAULT_ASSUMPTIONS.importable_share,
    )
    parser.add_argument(
        "--target-capture-share",
        type=float,
        default=DEFAULT_ASSUMPTIONS.target_capture_share,
    )
    parser.add_argument(
        "--sample-coverage",
        type=float,
        default=DEFAULT_ASSUMPTIONS.sample_coverage,
    )


def _part2_assumptions_from_args(args: argparse.Namespace) -> Part2Assumptions:
    return Part2Assumptions(
        leaderboard_size=args.leaderboard_size,
        sweet_spot_bins=args.sweet_spot_bins,
        whitespace_threshold=args.whitespace_threshold,
        min_theme_mentions=args.min_theme_mentions,
        min_attribute_support=args.min_attribute_support,
    )


def _add_part2_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--leaderboard-size",
        type=int,
        default=DEFAULT_PART2_ASSUMPTIONS.leaderboard_size,
    )
    parser.add_argument(
        "--sweet-spot-bins",
        type=int,
        default=DEFAULT_PART2_ASSUMPTIONS.sweet_spot_bins,
    )
    parser.add_argument(
        "--whitespace-threshold",
        type=float,
        default=DEFAULT_PART2_ASSUMPTIONS.whitespace_threshold,
    )
    parser.add_argument(
        "--min-theme-mentions",
        type=int,
        default=DEFAULT_PART2_ASSUMPTIONS.min_theme_mentions,
    )
    parser.add_argument(
        "--min-attribute-support",
        type=int,
        default=DEFAULT_PART2_ASSUMPTIONS.min_attribute_support,
    )


def _part3_assumptions_from_args(args: argparse.Namespace) -> Part3Assumptions:
    return Part3Assumptions(
        target_market=args.target_market,
        target_sell_price=args.target_sell_price,
        target_order_units=args.target_order_units,
        channel_fee_rate=args.channel_fee_rate,
        marketing_fee_rate=args.marketing_fee_rate,
        return_rate=args.return_rate,
        return_cost_per_unit=args.return_cost_per_unit,
        working_capital_rate=args.working_capital_rate,
    )


def _add_part3_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target-market", default=DEFAULT_PART3_ASSUMPTIONS.target_market)
    parser.add_argument(
        "--target-sell-price",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.target_sell_price,
    )
    parser.add_argument(
        "--target-order-units",
        type=int,
        default=DEFAULT_PART3_ASSUMPTIONS.target_order_units,
    )
    parser.add_argument(
        "--channel-fee-rate",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.channel_fee_rate,
    )
    parser.add_argument(
        "--marketing-fee-rate",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.marketing_fee_rate,
    )
    parser.add_argument(
        "--return-rate",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.return_rate,
    )
    parser.add_argument(
        "--return-cost-per-unit",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.return_cost_per_unit,
    )
    parser.add_argument(
        "--working-capital-rate",
        type=float,
        default=DEFAULT_PART3_ASSUMPTIONS.working_capital_rate,
    )


def _part4_assumptions_from_args(args: argparse.Namespace) -> Part4Assumptions:
    return Part4Assumptions(
        target_payback_months=args.target_payback_months,
        max_loss_probability=args.max_loss_probability,
        min_contribution_margin_rate=args.min_contribution_margin_rate,
        target_repeat_rate=args.target_repeat_rate,
        target_inventory_days=args.target_inventory_days,
        risk_penalty_lambda=args.risk_penalty_lambda,
        minimum_experiment_days=args.minimum_experiment_days,
    )


def _add_part4_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target-payback-months",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.target_payback_months,
    )
    parser.add_argument(
        "--max-loss-probability",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.max_loss_probability,
    )
    parser.add_argument(
        "--min-contribution-margin-rate",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.min_contribution_margin_rate,
    )
    parser.add_argument(
        "--target-repeat-rate",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.target_repeat_rate,
    )
    parser.add_argument(
        "--target-inventory-days",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.target_inventory_days,
    )
    parser.add_argument(
        "--risk-penalty-lambda",
        type=float,
        default=DEFAULT_PART4_ASSUMPTIONS.risk_penalty_lambda,
    )
    parser.add_argument(
        "--minimum-experiment-days",
        type=int,
        default=DEFAULT_PART4_ASSUMPTIONS.minimum_experiment_days,
    )


def _part5_assumptions_from_args(args: argparse.Namespace) -> Part5Assumptions:
    return Part5Assumptions(
        target_health_score=args.target_health_score,
        min_contribution_margin_rate=args.min_contribution_margin_rate,
        max_refund_rate=args.max_refund_rate,
        max_dispute_rate=args.max_dispute_rate,
        target_inventory_days=args.target_inventory_days,
        target_repeat_rate=args.target_repeat_rate,
        min_experiment_weeks=args.min_experiment_weeks,
        max_budget_burn_ratio=args.max_budget_burn_ratio,
        budget_allocation_max_share=args.budget_allocation_max_share,
        experiment_ship_threshold=args.experiment_ship_threshold,
        experiment_loss_threshold=args.experiment_loss_threshold,
        experiment_futility_lower=args.experiment_futility_lower,
        experiment_futility_upper=args.experiment_futility_upper,
        experiment_effect_floor_share_of_mde=args.experiment_effect_floor_share_of_mde,
    )


def _add_part5_assumption_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target-health-score",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.target_health_score,
    )
    parser.add_argument(
        "--min-contribution-margin-rate",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.min_contribution_margin_rate,
    )
    parser.add_argument(
        "--max-refund-rate",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.max_refund_rate,
    )
    parser.add_argument(
        "--max-dispute-rate",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.max_dispute_rate,
    )
    parser.add_argument(
        "--target-inventory-days",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.target_inventory_days,
    )
    parser.add_argument(
        "--target-repeat-rate",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.target_repeat_rate,
    )
    parser.add_argument(
        "--min-experiment-weeks",
        type=int,
        default=DEFAULT_PART5_ASSUMPTIONS.min_experiment_weeks,
    )
    parser.add_argument(
        "--max-budget-burn-ratio",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.max_budget_burn_ratio,
    )
    parser.add_argument(
        "--budget-allocation-max-share",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.budget_allocation_max_share,
    )
    parser.add_argument(
        "--experiment-ship-threshold",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.experiment_ship_threshold,
    )
    parser.add_argument(
        "--experiment-loss-threshold",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.experiment_loss_threshold,
    )
    parser.add_argument(
        "--experiment-futility-lower",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.experiment_futility_lower,
    )
    parser.add_argument(
        "--experiment-futility-upper",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.experiment_futility_upper,
    )
    parser.add_argument(
        "--experiment-effect-floor-share-of-mde",
        type=float,
        default=DEFAULT_PART5_ASSUMPTIONS.experiment_effect_floor_share_of_mde,
    )


def _handle_report(args: argparse.Namespace) -> int:
    dataset = build_dataset_from_directory(args.data_dir)
    assumptions = _assumptions_from_args(args)
    report = build_part1_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part0_report(args: argparse.Namespace) -> int:
    dataset = build_part0_dataset_from_directory(args.data_dir)
    assumptions = _part0_assumptions_from_args(args)
    report = build_part0_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part0_charts(args: argparse.Namespace) -> int:
    dataset = build_part0_dataset_from_directory(args.data_dir)
    assumptions = _part0_assumptions_from_args(args)
    report = build_part0_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part0_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_horizontal_system_report(args: argparse.Namespace) -> int:
    dataset = build_horizontal_system_dataset_from_directory(args.data_dir)
    assumptions = _horizontal_system_assumptions_from_args(args)
    report = build_horizontal_system_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_horizontal_system_charts(args: argparse.Namespace) -> int:
    dataset = build_horizontal_system_dataset_from_directory(args.data_dir)
    assumptions = _horizontal_system_assumptions_from_args(args)
    report = build_horizontal_system_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_horizontal_system_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_charts(args: argparse.Namespace) -> int:
    dataset = build_dataset_from_directory(args.data_dir)
    assumptions = _assumptions_from_args(args)
    report = build_part1_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part1_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_part2_report(args: argparse.Namespace) -> int:
    dataset = build_part2_dataset_from_directory(args.data_dir)
    assumptions = _part2_assumptions_from_args(args)
    report = build_part2_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part2_charts(args: argparse.Namespace) -> int:
    dataset = build_part2_dataset_from_directory(args.data_dir)
    assumptions = _part2_assumptions_from_args(args)
    report = build_part2_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part2_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_part3_report(args: argparse.Namespace) -> int:
    dataset = build_part3_dataset_from_directory(args.data_dir)
    assumptions = _part3_assumptions_from_args(args)
    report = build_part3_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part3_charts(args: argparse.Namespace) -> int:
    dataset = build_part3_dataset_from_directory(args.data_dir)
    assumptions = _part3_assumptions_from_args(args)
    report = build_part3_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part3_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_part4_report(args: argparse.Namespace) -> int:
    dataset = build_part4_dataset_from_directory(args.data_dir)
    assumptions = _part4_assumptions_from_args(args)
    report = build_part4_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part4_charts(args: argparse.Namespace) -> int:
    dataset = build_part4_dataset_from_directory(args.data_dir)
    assumptions = _part4_assumptions_from_args(args)
    report = build_part4_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part4_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_part5_report(args: argparse.Namespace) -> int:
    dataset = build_part5_dataset_from_directory(args.data_dir)
    assumptions = _part5_assumptions_from_args(args)
    report = build_part5_quant_report(dataset, assumptions)
    summary = build_cli_summary(report)
    if args.output_json:
        report_path = write_json(args.output_json, report)
        summary["report_json"] = str(report_path)
    if args.print_report or not args.output_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_part5_charts(args: argparse.Namespace) -> int:
    dataset = build_part5_dataset_from_directory(args.data_dir)
    assumptions = _part5_assumptions_from_args(args)
    report = build_part5_quant_report(dataset, assumptions)
    if args.report_json:
        write_json(args.report_json, report)
    chart_paths = generate_part5_chart_assets(report, args.output_dir)
    print(json.dumps(chart_paths, ensure_ascii=False, indent=2))
    return 0


def _handle_part5_etl(args: argparse.Namespace) -> int:
    payload = run_part5_etl_skeleton(
        args.source_dir,
        args.output_dir,
        batch_id=args.batch_id,
        connector=args.connector,
        max_retries=args.max_retries,
        previous_manifest=args.previous_manifest,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_clean(args: argparse.Namespace) -> int:
    cleaners = {
        "amazon": normalize_amazon_listings_export,
        "ebay": normalize_ebay_transactions_export,
        "tiktok": normalize_tiktok_channels_export,
        "tiktok-listings": normalize_tiktok_listings_export,
    }
    summary = cleaners[args.platform](args.input_csv, args.output_csv)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_clean_part2(args: argparse.Namespace) -> int:
    if args.platform == "combine":
        if not args.bundle_dirs:
            raise SystemExit("--bundle-dirs is required when --platform combine")
        summary = combine_part2_bundles(args.bundle_dirs, args.output_dir)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not args.input_csv:
        raise SystemExit("--input-csv is required for platform-specific Part 2 cleaning")
    cleaners = {
        "amazon": normalize_amazon_part2_export,
        "ebay": normalize_ebay_part2_export,
        "tiktok": normalize_tiktok_part2_export,
    }
    if args.platform in {"amazon", "tiktok"}:
        summary = cleaners[args.platform](
            args.input_csv,
            args.output_dir,
            capture_date=args.capture_date,
        )
    else:
        summary = cleaners[args.platform](args.input_csv, args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_clean_part3(args: argparse.Namespace) -> int:
    cleaners = {
        "suppliers": normalize_part3_suppliers_export,
        "rfq": normalize_part3_rfq_export,
        "compliance": normalize_part3_compliance_export,
        "logistics": normalize_part3_logistics_export,
        "tariff": normalize_part3_tariff_export,
        "shipment": normalize_part3_shipment_export,
    }
    summary = cleaners[args.table](args.input_csv, args.output_csv)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest(args: argparse.Namespace) -> int:
    panel_rows = load_backtest_panel(args.panel_csv)
    result = run_market_opportunity_backtest(
        panel_rows,
        lookback=args.lookback,
        top_n=args.top_n,
    )
    payload = {
        "summary": result["summary"],
    }
    if args.output_json:
        summary_path = write_json(args.output_json, result)
        payload["summary_json"] = str(summary_path)
    if args.output_svg:
        svg_path = write_backtest_curve_svg(result, args.output_svg)
        payload["curve_svg"] = str(svg_path)
    if args.output_monthly_csv:
        monthly_csv = write_backtest_monthly_csv(result, args.output_monthly_csv)
        payload["monthly_csv"] = str(monthly_csv)
    if args.print_report or not args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part2(args: argparse.Namespace) -> int:
    panel_rows = load_part2_backtest_panel(args.panel_csv)
    result = run_part2_competition_backtest(
        panel_rows,
        lookback=args.lookback,
        top_n=args.top_n,
    )
    payload = {
        "summary": result["summary"],
    }
    if args.output_json:
        summary_path = write_json(args.output_json, result)
        payload["summary_json"] = str(summary_path)
    if args.output_svg:
        svg_path = write_backtest_curve_svg(result, args.output_svg)
        payload["curve_svg"] = str(svg_path)
    if args.output_monthly_csv:
        monthly_csv = write_backtest_monthly_csv(result, args.output_monthly_csv)
        payload["monthly_csv"] = str(monthly_csv)
    if args.print_report or not args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_build_part2_panel(args: argparse.Namespace) -> int:
    panel_path = build_part2_backtest_panel_from_directory(
        args.data_dir,
        args.output_csv,
        category_depth=args.category_depth,
        min_categories_per_month=args.min_categories_per_month,
    )
    print(
        json.dumps(
            {
                "panel_csv": str(panel_path),
                "category_depth": args.category_depth,
                "min_categories_per_month": args.min_categories_per_month,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _handle_backtest_demo(args: argparse.Namespace) -> int:
    payload = run_backtest_demo(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part2_demo(args: argparse.Namespace) -> int:
    payload = run_part2_backtest_demo(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part3(args: argparse.Namespace) -> int:
    panel_rows = load_part3_backtest_panel(args.panel_csv)
    result = run_part3_supply_backtest(panel_rows, lookback=args.lookback, top_n=args.top_n)
    payload = {"summary": result["summary"]}
    if args.output_json:
        payload["summary_json"] = str(write_json(args.output_json, result))
    if args.output_svg:
        payload["curve_svg"] = str(write_backtest_curve_svg(result, args.output_svg))
    if args.output_monthly_csv:
        payload["monthly_csv"] = str(write_backtest_monthly_csv(result, args.output_monthly_csv))
    if args.print_report or not args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part4(args: argparse.Namespace) -> int:
    panel_rows = load_part4_backtest_panel(args.panel_csv)
    result = run_part4_channel_backtest(panel_rows, lookback=args.lookback, top_n=args.top_n)
    payload = {"summary": result["summary"]}
    if args.output_json:
        payload["summary_json"] = str(write_json(args.output_json, result))
    if args.output_svg:
        payload["curve_svg"] = str(write_backtest_curve_svg(result, args.output_svg))
    if args.output_monthly_csv:
        payload["monthly_csv"] = str(write_backtest_monthly_csv(result, args.output_monthly_csv))
    if args.print_report or not args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part5(args: argparse.Namespace) -> int:
    panel_rows = load_part5_backtest_panel(args.panel_csv)
    result = run_part5_operating_backtest(panel_rows, lookback=args.lookback, top_n=args.top_n)
    payload = {"summary": result["summary"]}
    if args.output_json:
        payload["summary_json"] = str(write_json(args.output_json, result))
    if args.output_svg:
        payload["curve_svg"] = str(write_backtest_curve_svg(result, args.output_svg))
    if args.output_monthly_csv:
        payload["monthly_csv"] = str(write_backtest_monthly_csv(result, args.output_monthly_csv))
    if args.print_report or not args.output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part3_demo(args: argparse.Namespace) -> int:
    payload = run_part3_backtest_demo(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part4_demo(args: argparse.Namespace) -> int:
    payload = run_part4_backtest_demo(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_part5_demo(args: argparse.Namespace) -> int:
    payload = run_part5_backtest_demo(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _handle_backtest_suite(args: argparse.Namespace) -> int:
    payload = run_full_backtest_suite(args.output_dir, seed=args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quant-framework")
    subparsers = parser.add_subparsers(dest="command", required=True)

    part0_report_parser = subparsers.add_parser("report-part0", help="Build the Part 0 governance report")
    part0_report_parser.add_argument("--data-dir", required=True)
    part0_report_parser.add_argument("--output-json")
    part0_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_part0_assumption_args(part0_report_parser)
    part0_report_parser.set_defaults(func=_handle_part0_report)

    part0_charts_parser = subparsers.add_parser("charts-part0", help="Generate SVG charts for Part 0")
    part0_charts_parser.add_argument("--data-dir", required=True)
    part0_charts_parser.add_argument("--output-dir", required=True)
    part0_charts_parser.add_argument("--report-json")
    _add_part0_assumption_args(part0_charts_parser)
    part0_charts_parser.set_defaults(func=_handle_part0_charts)

    horizontal_report_parser = subparsers.add_parser(
        "report-horizontal",
        help="Build the horizontal system management report",
    )
    horizontal_report_parser.add_argument("--data-dir", required=True)
    horizontal_report_parser.add_argument("--output-json")
    horizontal_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_horizontal_system_assumption_args(horizontal_report_parser)
    horizontal_report_parser.set_defaults(func=_handle_horizontal_system_report)

    horizontal_charts_parser = subparsers.add_parser(
        "charts-horizontal",
        help="Generate SVG charts for the horizontal system management report",
    )
    horizontal_charts_parser.add_argument("--data-dir", required=True)
    horizontal_charts_parser.add_argument("--output-dir", required=True)
    horizontal_charts_parser.add_argument("--report-json")
    _add_horizontal_system_assumption_args(horizontal_charts_parser)
    horizontal_charts_parser.set_defaults(func=_handle_horizontal_system_charts)

    report_parser = subparsers.add_parser("report", help="Build the Part 1 quantitative report")
    report_parser.add_argument("--data-dir", required=True)
    report_parser.add_argument("--output-json")
    report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_assumption_args(report_parser)
    report_parser.set_defaults(func=_handle_report)

    charts_parser = subparsers.add_parser("charts", help="Generate SVG charts for Part 1")
    charts_parser.add_argument("--data-dir", required=True)
    charts_parser.add_argument("--output-dir", required=True)
    charts_parser.add_argument("--report-json")
    _add_assumption_args(charts_parser)
    charts_parser.set_defaults(func=_handle_charts)

    part2_report_parser = subparsers.add_parser(
        "report-part2",
        help="Build the Part 2 quantitative report",
    )
    part2_report_parser.add_argument("--data-dir", required=True)
    part2_report_parser.add_argument("--output-json")
    part2_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_part2_assumption_args(part2_report_parser)
    part2_report_parser.set_defaults(func=_handle_part2_report)

    part2_charts_parser = subparsers.add_parser(
        "charts-part2",
        help="Generate SVG charts for Part 2",
    )
    part2_charts_parser.add_argument("--data-dir", required=True)
    part2_charts_parser.add_argument("--output-dir", required=True)
    part2_charts_parser.add_argument("--report-json")
    _add_part2_assumption_args(part2_charts_parser)
    part2_charts_parser.set_defaults(func=_handle_part2_charts)

    part3_report_parser = subparsers.add_parser(
        "report-part3",
        help="Build the Part 3 quantitative report",
    )
    part3_report_parser.add_argument("--data-dir", required=True)
    part3_report_parser.add_argument("--output-json")
    part3_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_part3_assumption_args(part3_report_parser)
    part3_report_parser.set_defaults(func=_handle_part3_report)

    part3_charts_parser = subparsers.add_parser(
        "charts-part3",
        help="Generate SVG charts for Part 3",
    )
    part3_charts_parser.add_argument("--data-dir", required=True)
    part3_charts_parser.add_argument("--output-dir", required=True)
    part3_charts_parser.add_argument("--report-json")
    _add_part3_assumption_args(part3_charts_parser)
    part3_charts_parser.set_defaults(func=_handle_part3_charts)

    part4_report_parser = subparsers.add_parser(
        "report-part4",
        help="Build the Part 4 quantitative report",
    )
    part4_report_parser.add_argument("--data-dir", required=True)
    part4_report_parser.add_argument("--output-json")
    part4_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_part4_assumption_args(part4_report_parser)
    part4_report_parser.set_defaults(func=_handle_part4_report)

    part4_charts_parser = subparsers.add_parser(
        "charts-part4",
        help="Generate SVG charts for Part 4",
    )
    part4_charts_parser.add_argument("--data-dir", required=True)
    part4_charts_parser.add_argument("--output-dir", required=True)
    part4_charts_parser.add_argument("--report-json")
    _add_part4_assumption_args(part4_charts_parser)
    part4_charts_parser.set_defaults(func=_handle_part4_charts)

    part5_report_parser = subparsers.add_parser(
        "report-part5",
        help="Build the Part 5 quantitative report",
    )
    part5_report_parser.add_argument("--data-dir", required=True)
    part5_report_parser.add_argument("--output-json")
    part5_report_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full report JSON to stdout even when --output-json is provided",
    )
    _add_part5_assumption_args(part5_report_parser)
    part5_report_parser.set_defaults(func=_handle_part5_report)

    part5_charts_parser = subparsers.add_parser(
        "charts-part5",
        help="Generate SVG charts for Part 5",
    )
    part5_charts_parser.add_argument("--data-dir", required=True)
    part5_charts_parser.add_argument("--output-dir", required=True)
    part5_charts_parser.add_argument("--report-json")
    _add_part5_assumption_args(part5_charts_parser)
    part5_charts_parser.set_defaults(func=_handle_part5_charts)

    part5_etl_parser = subparsers.add_parser(
        "etl-part5",
        help="Stage and materialize a Part 5 source bundle into raw/curated ETL directories",
    )
    part5_etl_parser.add_argument("--source-dir", required=True)
    part5_etl_parser.add_argument("--output-dir", required=True)
    part5_etl_parser.add_argument("--batch-id")
    part5_etl_parser.add_argument(
        "--connector",
        choices=["bundle_sync", "export_drop", "api_cache"],
        default="bundle_sync",
    )
    part5_etl_parser.add_argument("--max-retries", type=int, default=3)
    part5_etl_parser.add_argument("--previous-manifest")
    part5_etl_parser.set_defaults(func=_handle_part5_etl)

    clean_parser = subparsers.add_parser("clean", help="Normalize raw platform export data")
    clean_parser.add_argument(
        "--platform",
        choices=["amazon", "ebay", "tiktok", "tiktok-listings"],
        required=True,
    )
    clean_parser.add_argument("--input-csv", required=True)
    clean_parser.add_argument("--output-csv", required=True)
    clean_parser.set_defaults(func=_handle_clean)

    clean_part2_parser = subparsers.add_parser(
        "clean-part2",
        help="Normalize raw platform export data into the Part 2 standard bundle",
    )
    clean_part2_parser.add_argument(
        "--platform",
        choices=["amazon", "ebay", "tiktok", "combine"],
        required=True,
    )
    clean_part2_parser.add_argument("--input-csv")
    clean_part2_parser.add_argument("--output-dir", required=True)
    clean_part2_parser.add_argument("--capture-date")
    clean_part2_parser.add_argument(
        "--bundle-dirs",
        nargs="*",
        default=[],
        help="Used with --platform combine to merge multiple cleaned Part 2 bundle directories",
    )
    clean_part2_parser.set_defaults(func=_handle_clean_part2)

    clean_part3_parser = subparsers.add_parser(
        "clean-part3",
        help="Normalize raw RFQ / logistics / compliance exports into Part 3 standard tables",
    )
    clean_part3_parser.add_argument(
        "--table",
        choices=["suppliers", "rfq", "compliance", "logistics", "tariff", "shipment"],
        required=True,
    )
    clean_part3_parser.add_argument("--input-csv", required=True)
    clean_part3_parser.add_argument("--output-csv", required=True)
    clean_part3_parser.set_defaults(func=_handle_clean_part3)

    backtest_parser = subparsers.add_parser("backtest", help="Run market opportunity backtest on a panel CSV")
    backtest_parser.add_argument("--panel-csv", required=True)
    backtest_parser.add_argument("--lookback", type=int, default=3)
    backtest_parser.add_argument("--top-n", type=int, default=2)
    backtest_parser.add_argument("--output-json")
    backtest_parser.add_argument("--output-svg")
    backtest_parser.add_argument("--output-monthly-csv")
    backtest_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full backtest result JSON to stdout even when output paths are provided",
    )
    backtest_parser.set_defaults(func=_handle_backtest)

    part2_backtest_parser = subparsers.add_parser(
        "backtest-part2",
        help="Run Part 2 competitive-structure backtest on a panel CSV",
    )
    part2_backtest_parser.add_argument("--panel-csv", required=True)
    part2_backtest_parser.add_argument("--lookback", type=int, default=3)
    part2_backtest_parser.add_argument("--top-n", type=int, default=2)
    part2_backtest_parser.add_argument("--output-json")
    part2_backtest_parser.add_argument("--output-svg")
    part2_backtest_parser.add_argument("--output-monthly-csv")
    part2_backtest_parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print the full backtest result JSON to stdout even when output paths are provided",
    )
    part2_backtest_parser.set_defaults(func=_handle_backtest_part2)

    part2_panel_parser = subparsers.add_parser(
        "build-panel-part2",
        help="Build a Part 2 month-category backtest panel from a cleaned Part 2 bundle",
    )
    part2_panel_parser.add_argument("--data-dir", required=True)
    part2_panel_parser.add_argument("--output-csv", required=True)
    part2_panel_parser.add_argument("--category-depth", type=int, default=1)
    part2_panel_parser.add_argument("--min-categories-per-month", type=int, default=3)
    part2_panel_parser.set_defaults(func=_handle_build_part2_panel)

    backtest_demo_parser = subparsers.add_parser(
        "backtest-demo",
        help="Generate a deterministic demo panel and run the market opportunity backtest",
    )
    backtest_demo_parser.add_argument("--output-dir", required=True)
    backtest_demo_parser.add_argument("--seed", type=int, default=42)
    backtest_demo_parser.set_defaults(func=_handle_backtest_demo)

    part2_backtest_demo_parser = subparsers.add_parser(
        "backtest-part2-demo",
        help="Generate a deterministic Part 2 demo panel and run the competitive backtest",
    )
    part2_backtest_demo_parser.add_argument("--output-dir", required=True)
    part2_backtest_demo_parser.add_argument("--seed", type=int, default=42)
    part2_backtest_demo_parser.set_defaults(func=_handle_backtest_part2_demo)

    for command_name, handler, help_text in [
        ("backtest-part3", _handle_backtest_part3, "Run Part 3 supply-path backtest on a panel CSV"),
        ("backtest-part4", _handle_backtest_part4, "Run Part 4 channel backtest on a panel CSV"),
        ("backtest-part5", _handle_backtest_part5, "Run Part 5 operating backtest on a panel CSV"),
    ]:
        parser_obj = subparsers.add_parser(command_name, help=help_text)
        parser_obj.add_argument("--panel-csv", required=True)
        parser_obj.add_argument("--lookback", type=int, default=3)
        parser_obj.add_argument("--top-n", type=int, default=2)
        parser_obj.add_argument("--output-json")
        parser_obj.add_argument("--output-svg")
        parser_obj.add_argument("--output-monthly-csv")
        parser_obj.add_argument(
            "--print-report",
            action="store_true",
            help="Print the full backtest result JSON to stdout even when output paths are provided",
        )
        parser_obj.set_defaults(func=handler)

    for command_name, handler, help_text in [
        ("backtest-part3-demo", _handle_backtest_part3_demo, "Generate a deterministic Part 3 demo panel and run the supply-path backtest"),
        ("backtest-part4-demo", _handle_backtest_part4_demo, "Generate a deterministic Part 4 demo panel and run the channel backtest"),
        ("backtest-part5-demo", _handle_backtest_part5_demo, "Generate a deterministic Part 5 demo panel and run the operating backtest"),
    ]:
        parser_obj = subparsers.add_parser(command_name, help=help_text)
        parser_obj.add_argument("--output-dir", required=True)
        parser_obj.add_argument("--seed", type=int, default=42)
        parser_obj.set_defaults(func=handler)

    backtest_suite_parser = subparsers.add_parser(
        "backtest-suite",
        help="Run the Part 1-5 demo backtest suite and weight self-optimization",
    )
    backtest_suite_parser.add_argument("--output-dir", required=True)
    backtest_suite_parser.add_argument("--seed", type=int, default=42)
    backtest_suite_parser.set_defaults(func=_handle_backtest_suite)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
