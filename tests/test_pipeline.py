from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from quant_framework.charts import (
    generate_part1_chart_assets,
    generate_part2_chart_assets,
    generate_part3_chart_assets,
)
from quant_framework.backtest import (
    build_part2_backtest_panel_from_directory,
    load_part2_backtest_panel,
    run_backtest_demo,
    run_part2_backtest_demo,
    run_part2_competition_backtest,
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
from quant_framework.io_utils import read_csv_rows
from quant_framework.part1 import build_part1_quant_report
from quant_framework.part2 import build_part2_quant_report
from quant_framework.part3 import build_part3_quant_report
from quant_framework.part2_pipeline import (
    DEFAULT_PART2_ASSUMPTIONS,
    build_part2_dataset_from_directory,
)
from quant_framework.part3_pipeline import (
    DEFAULT_PART3_ASSUMPTIONS,
    build_part3_dataset_from_directory,
)
from quant_framework.pipeline import DEFAULT_ASSUMPTIONS, build_dataset_from_directory


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
PART2_EXAMPLES = EXAMPLES / "part2_demo"
PART3_EXAMPLES = EXAMPLES / "part3_demo"
EXTERNAL_INPUTS = ROOT / "external_inputs"


class Part1PipelineTests(unittest.TestCase):
    def test_build_report_from_examples(self) -> None:
        dataset = build_dataset_from_directory(EXAMPLES)
        report = build_part1_quant_report(dataset, DEFAULT_ASSUMPTIONS)

        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertLess(
            report["sections"]["1.3"]["metrics"]["triangulation"]["top_down_vs_bottom_up_gap_ratio"],
            0.02,
        )
        self.assertIn("uncertainty", report)
        self.assertIn("market_size", report["uncertainty"])
        self.assertEqual(
            report["sections"]["1.3"]["metrics"]["bottom_up"]["concentration_level"],
            "highly_concentrated",
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

        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertGreater(report["sections"]["2.1"]["metrics"]["total_gmv"], 0)
        self.assertIn("uncertainty", report)
        self.assertGreater(
            report["sections"]["2.2"]["metrics"]["sweet_spot_band"]["share"],
            0,
        )
        self.assertGreater(
            report["sections"]["2.6"]["metrics"]["median_lifetime_days"],
            0,
        )

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

        self.assertEqual(report["validation"]["summary"]["fail_count"], 0)
        self.assertEqual(report["validation"]["summary"]["review_count"], 0)
        self.assertIn("uncertainty", report)
        self.assertIn("monte_carlo", report["sections"]["3.5"]["metrics"])
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
            self.assertEqual(len(logistics_rows), 5)
            self.assertEqual(logistics_rows[0]["shipping_mode"], "sea_fcl")


if __name__ == "__main__":
    unittest.main()
