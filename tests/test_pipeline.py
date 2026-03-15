from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from quant_framework.charts import (
    generate_horizontal_system_chart_assets,
    generate_part0_chart_assets,
    generate_part1_chart_assets,
    generate_part2_chart_assets,
    generate_part3_chart_assets,
    generate_part4_chart_assets,
    generate_part5_chart_assets,
)
from quant_framework.backtest import (
    build_part2_backtest_panel_from_directory,
    load_part2_backtest_panel,
    run_full_backtest_suite,
    run_backtest_demo,
    run_part2_backtest_demo,
    run_part2_competition_backtest,
    run_part3_backtest_demo,
    run_part4_backtest_demo,
    run_part5_backtest_demo,
)
from quant_framework.cleaners import (
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
    normalize_tiktok_channels_export,
)
from quant_framework.cli import main as cli_main
from quant_framework.gate_engine import evaluate_gate
from quant_framework.horizontal_pipeline import (
    DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS,
    build_horizontal_system_dataset_from_directory,
)
from quant_framework.horizontal_system import build_horizontal_system_report
from quant_framework.io_utils import read_csv_rows
from quant_framework.part0 import build_part0_quant_report
from quant_framework.part1 import build_part1_quant_report
from quant_framework.part2 import build_part2_quant_report
from quant_framework.part3 import build_part3_quant_report
from quant_framework.part4 import build_part4_quant_report
from quant_framework.part5 import build_part5_quant_report
from quant_framework.part0_pipeline import (
    DEFAULT_PART0_ASSUMPTIONS,
    build_part0_dataset_from_directory,
)
from quant_framework.part5_etl import run_part5_etl_skeleton
from quant_framework.part2_pipeline import (
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)
from quant_framework.part3_pipeline import (
    DEFAULT_PART3_ASSUMPTIONS,
    build_part3_dataset_from_directory,
)
from quant_framework.part4_pipeline import (
    DEFAULT_PART4_ASSUMPTIONS,
    build_part4_dataset_from_directory,
)
from quant_framework.part5_pipeline import (
    DEFAULT_PART5_ASSUMPTIONS,
    build_part5_dataset_from_directory,
)
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PART0_EXAMPLES = EXAMPLES / "part0_demo"
HORIZONTAL_EXAMPLES = EXAMPLES / "horizontal_system_demo"
PART2_EXAMPLES = EXAMPLES / "part2_demo"
PART3_EXAMPLES = EXAMPLES / "part3_demo"
PART4_EXAMPLES = EXAMPLES / "part4_demo"
PART5_EXAMPLES = EXAMPLES / "part5_demo"
EXTERNAL_INPUTS = ROOT / "external_inputs"


def _assert_standard_report_contract(test_case: unittest.TestCase, report: dict) -> None:
    test_case.assertIn("metadata", report)
    test_case.assertIn("overview", report)
    test_case.assertIn("sections", report)
    test_case.assertIn("assumptions", report["metadata"])
    test_case.assertIn("table_inventory", report["metadata"])
    test_case.assertIn("validation_summary", report["overview"])
    test_case.assertIn("headline_metrics", report["overview"])
    test_case.assertIn("connected_channel_scope", report["overview"])
    test_case.assertIn("control_tower_binding", report["overview"])
    test_case.assertIsInstance(report["overview"]["headline_metrics"], list)
    for section_id, section_payload in report["sections"].items():
        test_case.assertEqual(section_payload["id"], section_id)
        test_case.assertIn("required_tables", section_payload)
        test_case.assertIn("metric_ids", section_payload)
        test_case.assertIn("granularity", section_payload)
        test_case.assertIn("channel_scope", section_payload)
        test_case.assertIn("master_data_ref", section_payload)
        test_case.assertIn("evidence_ref", section_payload)
        test_case.assertIn("rule_ref", section_payload)
        test_case.assertIn("gate_result", section_payload)
        test_case.assertIn("data_quality", section_payload)
        test_case.assertIn("confidence", section_payload)
        test_case.assertIn("metrics", section_payload)
        test_case.assertIn("record_counts", section_payload["data_quality"])
        test_case.assertIn("quality_score", section_payload["data_quality"])
        test_case.assertIn("score", section_payload["confidence"])


class Part0PipelineTests(unittest.TestCase):
    def test_build_part0_report_from_examples(self) -> None:
        dataset = build_part0_dataset_from_directory(PART0_EXAMPLES)
        report = build_part0_quant_report(dataset, DEFAULT_PART0_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("governance_quality_band", report["uncertainty"])
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(
            report["overview"]["decision_signal"],
            {"ready_for_execution_system", "governance_needs_hardening", "not_ready"},
        )
        self.assertEqual(len(report["overview"]["decision_summary"]["scorecard"]), 3)
        self.assertGreater(report["sections"]["0.1"]["metrics"]["decision_node_count"], 0)
        self.assertLessEqual(report["sections"]["0.1"]["metrics"]["decision_tree_score"], 1.0)
        self.assertGreater(report["sections"]["0.4"]["metrics"]["gate_operability_score"], 0)
        self.assertGreater(report["sections"]["0.4"]["metrics"]["strategic_gate_score"], 0)
        self.assertEqual(
            report["sections"]["0.4"]["metrics"]["strategic_metric_family_coverage_ratio"],
            1.0,
        )
        self.assertGreater(report["sections"]["0.7"]["metrics"]["naming_compliance_ratio"], 0)
        self.assertEqual(report["sections"]["0.8"]["metrics"]["active_market_count"], 10)
        self.assertEqual(report["sections"]["0.8"]["metrics"]["habit_vector_coverage_ratio"], 1.0)
        self.assertEqual(report["sections"]["0.8"]["metrics"]["weight_profile_coverage_ratio"], 1.0)
        self.assertGreater(report["sections"]["0.8"]["metrics"]["localization_governance_score"], 0.5)

    def test_generate_part0_charts(self) -> None:
        dataset = build_part0_dataset_from_directory(PART0_EXAMPLES)
        report = build_part0_quant_report(dataset, DEFAULT_PART0_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part0_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cli_part0_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "part0_report.json"
            charts_dir = temp_path / "part0_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-part0",
                        "--data-dir",
                        str(PART0_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-part0",
                        "--data-dir",
                        str(PART0_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "confidence_grade_mix.svg").exists())
            self.assertTrue((charts_dir / "governance_scorecard.svg").exists())


class HorizontalSystemPipelineTests(unittest.TestCase):
    def test_build_horizontal_report_from_examples(self) -> None:
        dataset = build_horizontal_system_dataset_from_directory(HORIZONTAL_EXAMPLES)
        report = build_horizontal_system_report(dataset, DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("master_data_band", report["uncertainty"])
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(
            report["overview"]["decision_signal"],
            {"control_tower_ready", "control_tower_needs_hardening", "control_tower_not_ready"},
        )
        self.assertGreater(report["sections"]["H1"]["metrics"]["master_data_health_score"], 0.8)
        self.assertGreater(report["sections"]["H2"]["metrics"]["traceback_sla_ratio"], 0.8)
        self.assertEqual(report["sections"]["H3"]["metrics"]["scenario_coverage_ratio"], 1.0)

    def test_generate_horizontal_charts(self) -> None:
        dataset = build_horizontal_system_dataset_from_directory(HORIZONTAL_EXAMPLES)
        report = build_horizontal_system_report(dataset, DEFAULT_HORIZONTAL_SYSTEM_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_horizontal_system_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cli_horizontal_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "horizontal_report.json"
            charts_dir = temp_path / "horizontal_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-horizontal",
                        "--data-dir",
                        str(HORIZONTAL_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-horizontal",
                        "--data-dir",
                        str(HORIZONTAL_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "master_data_governance.svg").exists())
            self.assertTrue((charts_dir / "evidence_audit_chain.svg").exists())
            self.assertTrue((charts_dir / "decision_threshold_system.svg").exists())


class Part1PipelineTests(unittest.TestCase):
    def test_build_report_from_examples(self) -> None:
        dataset = build_dataset_from_directory(EXAMPLES)
        report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertLess(
            report["sections"]["1.3"]["metrics"]["triangulation"]["top_down_vs_bottom_up_gap_ratio"],
            0.02,
        )
        self.assertIn("uncertainty", report)
        self.assertIn("market_size", report["uncertainty"])
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(report["overview"]["decision_signal"], {"attractive", "watchlist", "caution"})
        self.assertEqual(len(report["overview"]["decision_summary"]["scorecard"]), 5)
        self.assertIn("factor_snapshots", report)
        self.assertEqual(report["overview"]["factor_snapshot_count"], 6)
        self.assertEqual(
            report["sections"]["1.3"]["metrics"]["bottom_up"]["concentration_level"],
            "highly_concentrated",
        )
        self.assertGreater(
            report["sections"]["1.3"]["metrics"]["market_size_inputs"]["consistency_ratio"],
            0.9,
        )
        self.assertLessEqual(
            report["sections"]["1.3"]["metrics"]["bottom_up"]["sample_monthly_gmv"],
            report["sections"]["1.3"]["metrics"]["bottom_up"]["sample_monthly_gmv_raw"],
        )
        self.assertAlmostEqual(
            report["sections"]["1.4"]["metrics"]["channels"][0]["conversion_rate"],
            0.1213,
            places=4,
        )
        self.assertEqual(
            report["sections"]["1.4"]["metrics"]["totals"]["benchmark_coverage_ratio"],
            0.8,
        )
        self.assertIn("event_library", report["metadata"]["table_inventory"])
        self.assertIn("source_registry", report["metadata"]["table_inventory"])
        self.assertIn("part1_threshold_registry", report["metadata"]["table_inventory"])
        self.assertEqual(report["metadata"]["table_inventory"]["event_library"]["record_count"], 4)
        self.assertEqual(report["sections"]["1.1"]["data_quality"]["record_counts"]["event_library"], 4)
        self.assertGreater(report["sections"]["1.1"]["metrics"]["source_health"]["coverage_ratio"], 0.5)
        self.assertGreater(report["sections"]["1.1"]["metrics"]["threshold_coverage_ratio"], 0.0)
        self.assertGreater(report["sections"]["1.3"]["metrics"]["market_size_inputs"]["market_attractiveness_factor"], 0.0)
        self.assertGreaterEqual(report["sections"]["1.4"]["metrics"]["channel_dependency_score"], 0.6)
        self.assertIn("FAC-MARKET-ATTRACT", report["factor_snapshots"])
        self.assertIn("part1_data_quality_log", report)
        self.assertIn("part1_evidence_trace_index", report)
        self.assertIn("part1_forecast_engine", report)
        self.assertIn("part1_drift_report", report)
        self.assertIn("part1_calibration_report", report)
        self.assertIn("part1_advanced_quant_tools", report)
        self.assertIn("part1_market_destination_engine", report)
        self.assertGreater(report["part1_data_quality_log"]["summary"]["table_count"], 0)
        self.assertGreater(report["part1_evidence_trace_index"]["summary"]["evidence_trace_coverage_ratio"], 0.0)
        self.assertEqual(len(report["part1_forecast_engine"]["next_forecast"]), 3)
        self.assertGreater(report["part1_forecast_engine"]["backtest"]["observation_count"], 0)
        self.assertGreater(report["part1_drift_report"]["summary"]["check_count"], 0)
        self.assertGreaterEqual(report["part1_calibration_report"]["summary"]["threshold_alignment_ratio"], 0.0)
        self.assertEqual(report["part1_advanced_quant_tools"]["summary"]["tool_count"], 5)
        self.assertEqual(report["part1_market_destination_engine"]["summary"]["market_count"], 10)
        self.assertIn(
            report["part1_market_destination_engine"]["summary"]["top_market_code"],
            {"EU", "JP", "KR", "TW", "PH", "VN", "TH", "KH", "LA", "ID"},
        )
        self.assertIn("advanced_time_series", report["sections"]["1.1"]["metrics"])
        self.assertIn(
            report["sections"]["1.1"]["metrics"]["advanced_time_series"]["signal_regime"],
            {"seasonal", "trend", "noisy"},
        )
        self.assertGreaterEqual(
            report["sections"]["1.1"]["metrics"]["advanced_time_series"]["spectral_features"]["seasonality_confidence_score"],
            0.0,
        )
        self.assertIn("continuous_quant_outputs", report["overview"])
        self.assertEqual(report["metadata"]["table_inventory"]["market_destination_registry"]["record_count"], 10)
        self.assertEqual(report["metadata"]["table_inventory"]["consumer_habit_vectors"]["record_count"], 10)
        self.assertEqual(report["metadata"]["table_inventory"]["region_weight_profiles"]["record_count"], 10)

    def test_generate_charts(self) -> None:
        dataset = build_dataset_from_directory(EXAMPLES)
        report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part1_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cleaners_normalize_raw_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            normalize_amazon_listings_export(
                EXAMPLES / "raw_amazon_listing_export.csv",
                temp_path / "amazon_listings.csv",
            )
            normalize_ebay_transactions_export(
                EXAMPLES / "raw_ebay_sold_export.csv",
                temp_path / "ebay_transactions.csv",
            )
            normalize_tiktok_channels_export(
                EXAMPLES / "raw_tiktok_channel_export.csv",
                temp_path / "tiktok_channels.csv",
            )

            amazon_rows = read_csv_rows(temp_path / "amazon_listings.csv")
            ebay_rows = read_csv_rows(temp_path / "ebay_transactions.csv")
            tiktok_rows = read_csv_rows(temp_path / "tiktok_channels.csv")

            self.assertEqual(len(amazon_rows), 3)
            self.assertEqual(amazon_rows[0]["platform"], "Amazon")
            self.assertEqual(len(ebay_rows), 3)
            self.assertEqual(ebay_rows[0]["platform"], "eBay")
            self.assertEqual(len(tiktok_rows), 1)
            self.assertEqual(tiktok_rows[0]["channel"], "TikTok Shop")

    def test_cli_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "report.json"
            charts_dir = temp_path / "charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report",
                        "--data-dir",
                        str(EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts",
                        "--data-dir",
                        str(EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "market_demand_trend.svg").exists())

    def test_backtest_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with redirect_stdout(io.StringIO()):
                payload = run_backtest_demo(temp_dir, seed=42)

            self.assertTrue(Path(payload["panel_csv"]).exists())
            self.assertTrue(Path(payload["summary_json"]).exists())
            self.assertTrue(Path(payload["curve_svg"]).exists())
            self.assertTrue(Path(payload["monthly_csv"]).exists())
            self.assertGreater(payload["summary"]["periods"], 10)
            self.assertGreater(payload["summary"]["avg_excess_return"], 0)


class Part2PipelineTests(unittest.TestCase):
    def test_build_part2_report_from_examples(self) -> None:
        dataset = build_part2_dataset_from_directory(PART2_EXAMPLES)
        report = build_part2_quant_report(dataset, DEFAULT_PART2_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(len(dataset.part2_source_registry), 3)
        self.assertEqual(len(dataset.part2_threshold_registry), 2)
        self.assertEqual(len(dataset.part2_benchmark_registry), 3)
        self.assertEqual(len(dataset.voc_event_registry), 2)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertGreater(report["sections"]["2.1"]["metrics"]["total_gmv"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(report["overview"]["decision_signal"], {"promising", "selective", "crowded"})
        self.assertEqual(len(report["overview"]["decision_summary"]["scorecard"]), 4)
        self.assertIn("factor_snapshots", report)
        self.assertEqual(report["overview"]["factor_snapshot_count"], 6)
        self.assertGreater(
            report["sections"]["2.2"]["metrics"]["sweet_spot_band"]["share"],
            0,
        )
        self.assertGreater(
            report["sections"]["2.6"]["metrics"]["median_lifetime_days"],
            0,
        )
        self.assertEqual(report["sections"]["2.2"]["metrics"]["benchmark_registry_count"], 3)
        self.assertEqual(report["sections"]["2.5"]["metrics"]["voc_event_registry_count"], 2)
        self.assertIn("FAC-PRICING-FIT", report["factor_snapshots"])
        self.assertIn("FAC-VALUE-ADVANTAGE", report["factor_snapshots"])
        self.assertIn("FAC-VOC-RISK", report["factor_snapshots"])
        self.assertEqual(report["part2_registry_bindings"]["part2_source_registry_count"], 3)
        self.assertIn("confidence_band", report)
        self.assertIn(report["confidence_band"]["label"], {"high", "medium", "low"})
        self.assertIn("proxy_usage_flags", report)

    def test_generate_part2_charts(self) -> None:
        dataset = build_part2_dataset_from_directory(PART2_EXAMPLES)
        report = build_part2_quant_report(dataset, DEFAULT_PART2_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part2_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_clean_part2_bundle_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            amazon_dir = temp_path / "amazon"
            ebay_dir = temp_path / "ebay"
            tiktok_dir = temp_path / "tiktok"
            combined_dir = temp_path / "combined"

            normalize_amazon_part2_export(
                EXAMPLES / "raw_part2_amazon_export.csv",
                amazon_dir,
                capture_date="2025-11-30",
            )
            normalize_ebay_part2_export(
                EXAMPLES / "raw_part2_ebay_sold_export.csv",
                ebay_dir,
            )
            normalize_tiktok_part2_export(
                EXAMPLES / "raw_part2_tiktok_export.csv",
                tiktok_dir,
                capture_date="2025-11-30",
            )
            combine_part2_bundles([amazon_dir, ebay_dir, tiktok_dir], combined_dir)

            amazon_listing_rows = read_csv_rows(amazon_dir / "listing_snapshots.csv")
            ebay_transaction_rows = read_csv_rows(ebay_dir / "sold_transactions.csv")
            tiktok_review_rows = read_csv_rows(tiktok_dir / "reviews.csv")
            combined_catalog_rows = read_csv_rows(combined_dir / "product_catalog.csv")

            self.assertEqual(len(amazon_listing_rows), 3)
            self.assertEqual(amazon_listing_rows[0]["platform"], "Amazon")
            self.assertEqual(len(ebay_transaction_rows), 4)
            self.assertEqual(ebay_transaction_rows[0]["platform"], "eBay")
            self.assertGreaterEqual(len(tiktok_review_rows), 2)
            self.assertGreaterEqual(len(combined_catalog_rows), 8)

    def test_cli_part2_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "part2_report.json"
            charts_dir = temp_path / "part2_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-part2",
                        "--data-dir",
                        str(PART2_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-part2",
                        "--data-dir",
                        str(PART2_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "top_sku_share.svg").exists())

    def test_cli_part2_clean_and_backtest_demo_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            amazon_dir = temp_path / "amazon_bundle"
            backtest_dir = temp_path / "part2_backtest"

            with redirect_stdout(io.StringIO()):
                clean_exit_code = cli_main(
                    [
                        "clean-part2",
                        "--platform",
                        "amazon",
                        "--input-csv",
                        str(EXAMPLES / "raw_part2_amazon_export.csv"),
                        "--output-dir",
                        str(amazon_dir),
                        "--capture-date",
                        "2025-11-30",
                    ]
                )
                backtest_exit_code = cli_main(
                    [
                        "backtest-part2-demo",
                        "--output-dir",
                        str(backtest_dir),
                    ]
                )

            self.assertEqual(clean_exit_code, 0)
            self.assertEqual(backtest_exit_code, 0)
            self.assertTrue((amazon_dir / "listing_snapshots.csv").exists())
            self.assertTrue((backtest_dir / "part2_competition_panel.csv").exists())

    def test_part2_backtest_demo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with redirect_stdout(io.StringIO()):
                payload = run_part2_backtest_demo(temp_dir, seed=42)

            self.assertTrue(Path(payload["panel_csv"]).exists())
            self.assertTrue(Path(payload["summary_json"]).exists())
            self.assertTrue(Path(payload["curve_svg"]).exists())
            self.assertTrue(Path(payload["monthly_csv"]).exists())
            self.assertGreater(payload["summary"]["periods"], 10)
            self.assertGreater(payload["summary"]["avg_excess_return"], 0)

    def test_external_github_part2_pipeline(self) -> None:
        github_csv = EXTERNAL_INPUTS / "github_amazon_products.csv"
        if not github_csv.exists():
            self.skipTest("external GitHub sample not downloaded")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bundle_dir = temp_path / "bundle"
            panel_csv = temp_path / "part2_panel.csv"

            normalize_amazon_part2_export(github_csv, bundle_dir)
            build_part2_backtest_panel_from_directory(
                bundle_dir,
                panel_csv,
                category_depth=1,
                min_categories_per_month=3,
            )
            panel_rows = load_part2_backtest_panel(panel_csv)
            result = run_part2_competition_backtest(panel_rows, lookback=2, top_n=2)

            self.assertGreater(len(panel_rows), 20)
            self.assertGreater(result["summary"]["periods"], 5)


class Part3PipelineTests(unittest.TestCase):
    def test_build_part3_report_from_examples(self) -> None:
        dataset = build_part3_dataset_from_directory(PART3_EXAMPLES)
        report = build_part3_quant_report(dataset, DEFAULT_PART3_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(len(dataset.part3_source_registry), 3)
        self.assertEqual(len(dataset.part3_threshold_registry), 2)
        self.assertEqual(len(dataset.part3_scenario_registry), 4)
        self.assertEqual(len(dataset.part3_optimizer_registry), 1)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(report["overview"]["decision_signal"], {"high_priority", "pilot_candidate", "hold"})
        self.assertEqual(len(report["overview"]["decision_summary"]["scorecard"]), 4)
        self.assertIn("monte_carlo", report["sections"]["3.5"]["metrics"])
        self.assertIn("sample_adequacy", report["sections"]["3.1"]["metrics"])
        self.assertGreater(
            report["sections"]["3.2"]["metrics"]["quote_quality"]["average_quote_confidence"],
            0,
        )
        self.assertIn("stage_distribution", report["sections"]["3.4"]["metrics"])
        self.assertGreater(
            report["sections"]["3.5"]["metrics"]["best_scenario"]["landed_cost"],
            0,
        )
        self.assertGreater(
            report["sections"]["3.5"]["metrics"]["best_scenario"]["net_margin"],
            0,
        )
        self.assertGreater(
            report["sections"]["3.5"]["metrics"]["monte_carlo"]["iterations"],
            1000,
        )
        self.assertIn("part3_risk_metrics", report["sections"]["3.5"]["metrics"])
        self.assertIn("value_at_risk_95", report["sections"]["3.5"]["metrics"]["part3_risk_metrics"])
        self.assertIn("expected_shortfall_95", report["sections"]["3.5"]["metrics"]["part3_risk_metrics"])
        self.assertIn("margin_rate_sharpe_like", report["sections"]["3.5"]["metrics"]["part3_risk_metrics"])
        self.assertIn("margin_rate_sortino_like", report["sections"]["3.5"]["metrics"]["part3_risk_metrics"])
        self.assertIn("factor_snapshots", report)
        self.assertEqual(len(report["factor_snapshots"]), 6)
        self.assertIn("confidence_band", report)
        self.assertIn(report["confidence_band"]["label"], {"high", "medium", "low"})
        self.assertIn("proxy_usage_flags", report)
        self.assertIn("scenario_table", report["sections"]["3.5"]["metrics"])
        self.assertGreater(
            report["sections"]["3.7"]["metrics"]["optimizer"]["feasible_scenarios_count"],
            0,
        )
        self.assertGreaterEqual(
            len(report["sections"]["3.5"]["metrics"]["monte_carlo"]["sensitivity"]),
            3,
        )

    def test_generate_part3_charts(self) -> None:
        dataset = build_part3_dataset_from_directory(PART3_EXAMPLES)
        report = build_part3_quant_report(dataset, DEFAULT_PART3_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part3_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cli_part3_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "part3_report.json"
            charts_dir = temp_path / "part3_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-part3",
                        "--data-dir",
                        str(PART3_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-part3",
                        "--data-dir",
                        str(PART3_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "supplier_type_share.svg").exists())
            self.assertTrue((charts_dir / "monte_carlo_margin_band.svg").exists())
            self.assertTrue((charts_dir / "monte_carlo_sensitivity.svg").exists())

    def test_cli_clean_part3_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_csv = temp_path / "rfq_quotes.csv"

            with redirect_stdout(io.StringIO()):
                exit_code = cli_main(
                    [
                        "clean-part3",
                        "--table",
                        "rfq",
                        "--input-csv",
                        str(EXAMPLES / "raw_part3_rfq_export.csv"),
                        "--output-csv",
                        str(output_csv),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_csv.exists())

    def test_clean_part3_raw_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            normalize_part3_suppliers_export(
                EXAMPLES / "raw_part3_suppliers_export.csv",
                temp_path / "suppliers.csv",
            )
            normalize_part3_rfq_export(
                EXAMPLES / "raw_part3_rfq_export.csv",
                temp_path / "rfq_quotes.csv",
            )
            normalize_part3_compliance_export(
                EXAMPLES / "raw_part3_compliance_export.csv",
                temp_path / "compliance_requirements.csv",
            )
            normalize_part3_logistics_export(
                EXAMPLES / "raw_part3_logistics_export.csv",
                temp_path / "logistics_quotes.csv",
            )
            normalize_part3_tariff_export(
                EXAMPLES / "raw_part3_tariff_export.csv",
                temp_path / "tariff_tax.csv",
            )
            normalize_part3_shipment_export(
                EXAMPLES / "raw_part3_shipment_export.csv",
                temp_path / "shipment_events.csv",
            )

            supplier_rows = read_csv_rows(temp_path / "suppliers.csv")
            rfq_rows = read_csv_rows(temp_path / "rfq_quotes.csv")
            logistics_rows = read_csv_rows(temp_path / "logistics_quotes.csv")

            self.assertEqual(len(supplier_rows), 6)
            self.assertEqual(supplier_rows[0]["supplier_type"], "factory")
            self.assertEqual(len(rfq_rows), 8)
            self.assertEqual(rfq_rows[0]["incoterm"], "EXW")
            self.assertEqual(rfq_rows[0]["quote_id"], "Q001")
            self.assertEqual(rfq_rows[0]["source_confidence"], "0.86")
            self.assertEqual(len(logistics_rows), 5)
            self.assertEqual(logistics_rows[0]["shipping_mode"], "sea_fcl")


class Part4PipelineTests(unittest.TestCase):
    def test_build_part4_report_from_examples(self) -> None:
        dataset = build_part4_dataset_from_directory(PART4_EXAMPLES)
        report = build_part4_quant_report(dataset, DEFAULT_PART4_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(len(dataset.part4_source_registry), 3)
        self.assertEqual(len(dataset.part4_threshold_registry), 3)
        self.assertEqual(len(dataset.part4_benchmark_registry), 5)
        self.assertEqual(len(dataset.part4_optimizer_registry), 1)
        self.assertEqual(len(dataset.part4_stress_registry), 3)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("roi_monte_carlo", report["uncertainty"])
        self.assertIn("decision_summary", report["overview"])
        self.assertIn(report["overview"]["decision_signal"], {"go", "pilot", "hold"})
        self.assertEqual(len(report["overview"]["decision_summary"]["scorecard"]), 4)
        self.assertIn("monte_carlo", report["sections"]["4.5"]["metrics"])
        self.assertIn("channel_performance_metrics", report["sections"]["4.5"]["metrics"])
        self.assertIn("stress_suite", report["sections"]["4.5"]["metrics"])
        self.assertIn("tail_risk", report["sections"]["4.5"]["metrics"]["monte_carlo"]["overall"])
        self.assertIn("risk_adjusted", report["sections"]["4.5"]["metrics"]["monte_carlo"]["overall"])
        self.assertIn("factor_snapshots", report)
        self.assertEqual(len(report["factor_snapshots"]), 6)
        self.assertIn("confidence_band", report)
        self.assertIn(report["confidence_band"]["label"], {"high", "medium", "low"})
        self.assertIn("proxy_usage_flags", report)
        self.assertIn("execution_friction_flags", report)
        self.assertIn("part4_optimizer_runs", report)
        self.assertGreater(len(report["part4_optimizer_runs"]), 0)
        self.assertIn("optimal_budget_mix", report["sections"]["4.7"]["metrics"]["optimizer"])
        self.assertIn("portfolio_constraints", report["sections"]["4.7"]["metrics"]["optimizer"])
        self.assertIn("optimizer_feasibility_report", report["sections"]["4.5"]["metrics"]["stress_suite"])
        self.assertIn("gate_flip_report", report["sections"]["4.5"]["metrics"]["stress_suite"])
        self.assertGreater(
            report["sections"]["4.5"]["metrics"]["blended"]["revenue"],
            0,
        )
        self.assertGreater(
            report["sections"]["4.7"]["metrics"]["optimizer"]["feasible_channels_count"],
            0,
        )
        self.assertIn(
            report["sections"]["4.7"]["metrics"]["recommendation"],
            {"go", "pilot_first", "no_go"},
        )

    def test_generate_part4_charts(self) -> None:
        dataset = build_part4_dataset_from_directory(PART4_EXAMPLES)
        report = build_part4_quant_report(dataset, DEFAULT_PART4_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part4_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cli_part4_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "part4_report.json"
            charts_dir = temp_path / "part4_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-part4",
                        "--data-dir",
                        str(PART4_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-part4",
                        "--data-dir",
                        str(PART4_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "channel_contribution_margin.svg").exists())
            self.assertTrue((charts_dir / "roi_band.svg").exists())


class Part5PipelineTests(unittest.TestCase):
    def test_build_part5_report_from_examples(self) -> None:
        dataset = build_part5_dataset_from_directory(PART5_EXAMPLES)
        report = build_part5_quant_report(dataset, DEFAULT_PART5_ASSUMPTIONS)

        _assert_standard_report_contract(self, report)
        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("daily_contribution_margin_rate", report["uncertainty"])
        self.assertIn("operating_health_score", report["sections"]["5.1"]["metrics"])
        self.assertIn(
            report["sections"]["5.7"]["metrics"]["expansion_gate_status"],
            {"scale_up", "hold_and_optimize", "pilot_only", "rollback"},
        )
        self.assertGreater(
            len(report["sections"]["5.1"]["metrics"]["channel_health_rows"]),
            0,
        )
        self.assertGreater(
            report["sections"]["5.6"]["metrics"]["sample_size_guidance"]["sample_size_per_variant"],
            0,
        )
        self.assertIn("audit_pack", report)
        self.assertIn("data_contract", report["overview"])
        self.assertIn("data_contract", report["sections"]["5.2"]["metrics"])
        self.assertIn(
            "customer_identity_available",
            report["overview"]["data_contract"]["data_availability_flags"],
        )
        self.assertIn("weekly_channel_pnl", report["sections"]["5.2"]["metrics"])
        self.assertIn("fee_version_binding_rows", report["sections"]["5.2"]["metrics"])
        self.assertIn("weekly_contribution_profit", report["sections"]["5.2"]["metrics"])
        self.assertIn("readouts", report["sections"]["5.6"]["metrics"])
        self.assertGreater(
            report["sections"]["5.6"]["metrics"]["readouts"]["readout_count"],
            0,
        )
        self.assertGreater(
            report["sections"]["5.6"]["metrics"]["readouts"]["average_posterior_win_probability"],
            0,
        )
        self.assertGreater(
            report["sections"]["5.6"]["metrics"]["readouts"]["average_hierarchical_win_probability"],
            0,
        )
        self.assertGreaterEqual(
            report["sections"]["5.6"]["metrics"]["readouts"]["temporal_consistency_score"],
            0,
        )
        self.assertGreater(
            report["sections"]["5.6"]["metrics"]["incrementality_score"],
            0,
        )
        self.assertIn("auto_stop_policy", report["sections"]["5.6"]["metrics"])
        self.assertIn("auto_stop_summary", report["sections"]["5.6"]["metrics"]["readouts"])
        self.assertIn("experiments_without_readouts", report["sections"]["5.6"]["metrics"]["readouts"])
        first_readout = report["sections"]["5.6"]["metrics"]["readouts"]["experiment_readouts"][0]
        self.assertIn("bayesian_status", first_readout)
        self.assertIn("hierarchical_status", first_readout)
        self.assertIn("posterior_probability_treatment_best", first_readout)
        self.assertIn("hierarchical_probability_treatment_best", first_readout)
        self.assertIn("slice_readouts", first_readout)
        self.assertIn("auto_stop_decision", first_readout)
        alerts = report["sections"]["5.7"]["metrics"]["alerts"]
        self.assertIn("change_signal_count", alerts)
        if alerts["alerts"]:
            self.assertIn("runbook_action", alerts["alerts"][0])
        self.assertIn("factor_snapshots", report)
        self.assertEqual(len(report["factor_snapshots"]), 7)
        self.assertIn("confidence_band", report)
        self.assertIn(report["confidence_band"]["label"], {"high", "medium", "low"})
        self.assertIn("proxy_usage_flags", report)
        self.assertIn(
            first_readout["auto_stop_decision"],
            {"ship_winner", "stop_for_loss", "stop_for_futility", "prepare_rollout", "watch_for_loss", "continue_collecting"},
        )

    def test_generate_part5_charts(self) -> None:
        dataset = build_part5_dataset_from_directory(PART5_EXAMPLES)
        report = build_part5_quant_report(dataset, DEFAULT_PART5_ASSUMPTIONS)

        with tempfile.TemporaryDirectory() as temp_dir:
            chart_paths = generate_part5_chart_assets(report, temp_dir)
            for chart_path in chart_paths.values():
                content = Path(chart_path).read_text(encoding="utf-8")
                self.assertIn("<svg", content)

    def test_cli_part5_report_and_chart_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            report_path = temp_path / "part5_report.json"
            charts_dir = temp_path / "part5_charts"

            with redirect_stdout(io.StringIO()):
                report_exit_code = cli_main(
                    [
                        "report-part5",
                        "--data-dir",
                        str(PART5_EXAMPLES),
                        "--output-json",
                        str(report_path),
                    ]
                )
                chart_exit_code = cli_main(
                    [
                        "charts-part5",
                        "--data-dir",
                        str(PART5_EXAMPLES),
                        "--output-dir",
                        str(charts_dir),
                    ]
                )

            self.assertEqual(report_exit_code, 0)
            self.assertEqual(chart_exit_code, 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIn("validation", report)
            self.assertTrue((charts_dir / "operating_health_by_channel.svg").exists())
            self.assertTrue((charts_dir / "budget_allocation.svg").exists())
            self.assertTrue((charts_dir / "weekly_contribution_profit.svg").exists())

    def test_part5_etl_skeleton_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            etl_dir = temp_path / "part5_etl"

            payload = run_part5_etl_skeleton(
                PART5_EXAMPLES,
                etl_dir,
                batch_id="test-batch",
                connector="export_drop",
            )
            self.assertTrue(Path(payload["manifest_json"]).exists())
            self.assertTrue(Path(payload["run_log_json"]).exists())
            self.assertTrue((etl_dir / "raw" / "test-batch" / "kpi_daily_snapshots.csv").exists())
            self.assertTrue((etl_dir / "curated" / "test-batch" / "experiment_metrics.csv").exists())
            first_manifest = json.loads(Path(payload["manifest_json"]).read_text(encoding="utf-8"))
            self.assertEqual(first_manifest["connector"], "export_drop")
            self.assertIn("manifest_diff", first_manifest)

            second_payload = run_part5_etl_skeleton(
                PART5_EXAMPLES,
                etl_dir,
                batch_id="test-batch-2",
                previous_manifest=payload["manifest_json"],
            )
            second_manifest = json.loads(Path(second_payload["manifest_json"]).read_text(encoding="utf-8"))
            self.assertEqual(second_manifest["manifest_diff"]["changed_files"], [])
            self.assertIn("experiment_metrics.csv", second_manifest["manifest_diff"]["unchanged_files"])

            with redirect_stdout(io.StringIO()):
                exit_code = cli_main(
                    [
                        "etl-part5",
                        "--source-dir",
                        str(PART5_EXAMPLES),
                        "--output-dir",
                        str(temp_path / "cli_etl"),
                        "--batch-id",
                        "cli-batch",
                        "--connector",
                        "api_cache",
                        "--max-retries",
                        "2",
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertTrue((temp_path / "cli_etl" / "audit" / "part5_etl_manifest_cli-batch.json").exists())
            self.assertTrue((temp_path / "cli_etl" / "audit" / "part5_etl_run_log_cli-batch.json").exists())


class BacktestSuiteTests(unittest.TestCase):
    def test_part3_part4_part5_backtests_and_suite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with redirect_stdout(io.StringIO()):
                part3_payload = run_part3_backtest_demo(temp_path / "part3", seed=42)
                part4_payload = run_part4_backtest_demo(temp_path / "part4", seed=42)
                part5_payload = run_part5_backtest_demo(temp_path / "part5", seed=42)
                suite_payload = run_full_backtest_suite(temp_path / "suite", seed=42)

            for payload in (part3_payload, part4_payload, part5_payload):
                self.assertTrue(Path(payload["panel_csv"]).exists())
                self.assertTrue(Path(payload["summary_json"]).exists())
                self.assertTrue(Path(payload["curve_svg"]).exists())
                self.assertTrue(Path(payload["monthly_csv"]).exists())
                self.assertGreater(payload["summary"]["periods"], 10)

            self.assertTrue(Path(suite_payload["suite_summary_json"]).exists())
            self.assertIn("part1", suite_payload["parts"])
            self.assertIn("part5", suite_payload["parts"])


class DecisionOSPackageTests(unittest.TestCase):
    def test_gate_engine_go_path(self) -> None:
        gate_config = {
            "gate_schema": {
                "gate_id": "GATE-MARKET-ENTRY-01",
                "schema_version": "2.0",
                "logic": "AND",
                "trigger": {
                    "conditions": [
                        {"source": "metric", "ref": "profit_p50", "operator": ">=", "value": 0.0},
                        {"source": "metric", "ref": "loss_probability", "operator": "<=", "value": 0.25},
                        {"source": "factor", "ref": "FAC-MARKET-ATTRACT-01", "operator": ">=", "value": 0.5},
                    ]
                },
                "capital_constraint": {"lhs": "required_capital", "operator": "<=", "rhs": "capital_free"},
                "risk_budget": {"lhs": "expected_drawdown", "operator": "<=", "rhs": "risk_limit"},
            }
        }
        result = evaluate_gate(
            gate_config,
            model_outputs={"profit_p50": 0.18, "loss_probability": 0.12},
            factor_outputs={"FAC-MARKET-ATTRACT-01": 0.64},
            capital_state={"required_capital": 400000, "capital_free": 1300000},
            risk_state={"expected_drawdown": 0.09, "risk_limit": 0.2},
        )
        self.assertEqual(result.status, "GO")
        self.assertEqual(result.failed_conditions, ())

    def test_gate_engine_capital_block(self) -> None:
        gate_config = {
            "gate_schema": {
                "gate_id": "GATE-SCALE-01",
                "schema_version": "2.0",
                "logic": "AND",
                "trigger": {
                    "conditions": [
                        {"source": "metric", "ref": "profit_p50", "operator": ">=", "value": 0.0},
                    ]
                },
                "capital_constraint": {"lhs": "required_capital", "operator": "<=", "rhs": "capital_free"},
            }
        }
        result = evaluate_gate(
            gate_config,
            model_outputs={"profit_p50": 0.05},
            capital_state={"required_capital": 900000, "capital_free": 250000},
        )
        self.assertEqual(result.status, "NO_GO_CAPITAL")

    def test_gate_engine_risk_block(self) -> None:
        gate_config = {
            "gate_schema": {
                "gate_id": "GATE-OPERATE-01",
                "schema_version": "2.0",
                "logic": "AND",
                "trigger": {
                    "conditions": [
                        {"source": "metric", "ref": "profit_p50", "operator": ">=", "value": 0.0},
                    ]
                },
                "risk_budget": {"lhs": "expected_drawdown", "operator": "<=", "rhs": "risk_limit"},
            }
        }
        result = evaluate_gate(
            gate_config,
            model_outputs={"profit_p50": 0.03},
            risk_state={"expected_drawdown": 0.34, "risk_limit": 0.2},
        )
        self.assertEqual(result.status, "NO_GO_RISK")


if __name__ == "__main__":
    unittest.main()
