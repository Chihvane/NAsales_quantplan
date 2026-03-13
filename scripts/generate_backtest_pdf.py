from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import copy2

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Flowable,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
FINAL_REPORT_DIR = ARTIFACTS_DIR / "final_report"
REPORTS_DIR = FINAL_REPORT_DIR / "reports"
VISUALIZATIONS_DIR = FINAL_REPORT_DIR / "visualizations"
DATA_DIR = FINAL_REPORT_DIR / "data"
INDEX_PATH = FINAL_REPORT_DIR / "index.json"
OUTPUT_PATH = REPORTS_DIR / "all-backtests-report.pdf"


@dataclass
class BacktestBundle:
    slug: str
    name: str
    scope: str
    summary_path: Path
    monthly_csv_path: Path | None
    panel_csv_path: Path | None
    report_path: Path | None
    chart_paths: list[Path]
    extra_data_paths: list[Path]
    notes: list[str]


class LineChartFlowable(Flowable):
    def __init__(
        self,
        title: str,
        monthly_records: list[dict],
        width: float = 250 * mm,
        height: float = 70 * mm,
    ) -> None:
        super().__init__()
        self.title = title
        self.monthly_records = monthly_records
        self.width = width
        self.height = height

    def wrap(self, available_width, available_height):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        left = 18
        right = 12
        top = 22
        bottom = 18
        plot_width = self.width - left - right
        plot_height = self.height - top - bottom

        strategy_curve = []
        benchmark_curve = []
        strategy_value = 1.0
        benchmark_value = 1.0
        for record in self.monthly_records:
            strategy_value *= 1 + float(record["strategy_return"])
            benchmark_value *= 1 + float(record["benchmark_return"])
            strategy_curve.append(strategy_value)
            benchmark_curve.append(benchmark_value)

        all_values = strategy_curve + benchmark_curve
        if not all_values:
            canvas.setFont("STSong-Light", 10)
            canvas.drawString(0, self.height - 10, self.title)
            canvas.drawString(0, self.height - 24, "无月度记录")
            return

        y_min = min(min(all_values), 0.0)
        y_max = max(max(all_values), 1.0)
        if y_max == y_min:
            y_max += 1.0

        def map_point(index: int, value: float) -> tuple[float, float]:
            x = left + plot_width * index / max(len(strategy_curve) - 1, 1)
            y = bottom + (value - y_min) / (y_max - y_min) * plot_height
            return x, y

        canvas.setFont("STSong-Light", 11)
        canvas.drawString(0, self.height - 12, self.title)

        canvas.setStrokeColor(colors.HexColor("#7b8794"))
        canvas.setLineWidth(0.6)
        canvas.line(left, bottom, left, bottom + plot_height)
        canvas.line(left, bottom, left + plot_width, bottom)

        canvas.setFont("STSong-Light", 7)
        for tick in range(5):
            value = y_min + (y_max - y_min) * tick / 4
            y = bottom + plot_height * tick / 4
            canvas.setStrokeColor(colors.HexColor("#d9dde7"))
            canvas.line(left, y, left + plot_width, y)
            canvas.setFillColor(colors.HexColor("#52606d"))
            canvas.drawRightString(left - 4, y - 2, f"{value:.2f}")

        strategy_points = [map_point(i, v) for i, v in enumerate(strategy_curve)]
        benchmark_points = [map_point(i, v) for i, v in enumerate(benchmark_curve)]

        canvas.setStrokeColor(colors.HexColor("#1f77b4"))
        canvas.setLineWidth(1.6)
        for start, end in zip(strategy_points, strategy_points[1:]):
            canvas.line(start[0], start[1], end[0], end[1])

        canvas.setStrokeColor(colors.HexColor("#ef8354"))
        canvas.setLineWidth(1.6)
        for start, end in zip(benchmark_points, benchmark_points[1:]):
            canvas.line(start[0], start[1], end[0], end[1])

        canvas.setFillColor(colors.HexColor("#1f77b4"))
        canvas.circle(left + plot_width - 50, self.height - 10, 2.2, stroke=0, fill=1)
        canvas.setFillColor(colors.black)
        canvas.drawString(left + plot_width - 44, self.height - 13, "策略")
        canvas.setFillColor(colors.HexColor("#ef8354"))
        canvas.circle(left + plot_width - 50, self.height - 22, 2.2, stroke=0, fill=1)
        canvas.setFillColor(colors.black)
        canvas.drawString(left + plot_width - 44, self.height - 25, "基准")

        month_labels = [str(record["month"]) for record in self.monthly_records]
        max_labels = 8
        step = max(1, len(month_labels) // max_labels)
        canvas.setFillColor(colors.HexColor("#52606d"))
        for index, label in enumerate(month_labels):
            if index % step != 0 and index != len(month_labels) - 1:
                continue
            x, _ = map_point(index, y_min)
            canvas.drawCentredString(x, bottom - 11, label)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _build_backtest_bundles() -> list[BacktestBundle]:
    return [
        BacktestBundle(
            slug="part1_demo",
            name="第一部分市场机会回测演示",
            scope="合成类目配置回测",
            summary_path=ROOT / "examples" / "output" / "backtest_demo" / "backtest_summary.json",
            monthly_csv_path=ROOT / "examples" / "output" / "backtest_demo" / "backtest_monthly_returns.csv",
            panel_csv_path=ROOT / "examples" / "output" / "backtest_demo" / "market_opportunity_panel.csv",
            report_path=ROOT / "examples" / "output" / "part1_report.json",
            chart_paths=[
                ROOT / "examples" / "output" / "backtest_demo" / "backtest_curve.svg",
                ROOT / "examples" / "output" / "charts" / "market_demand_trend.svg",
                ROOT / "examples" / "output" / "charts" / "listed_price_band_share.svg",
                ROOT / "examples" / "output" / "charts" / "channel_structure.svg",
            ],
            extra_data_paths=[],
            notes=[
                "使用第一部分的市场机会因子集。",
                "面板是覆盖 24 个月、5 个类目的确定性演示数据。",
            ],
        ),
        BacktestBundle(
            slug="part2_demo",
            name="第二部分竞争结构回测演示",
            scope="合成 SKU 竞争结构回测",
            summary_path=ROOT / "examples" / "output_part2" / "backtest_demo" / "part2_backtest_summary.json",
            monthly_csv_path=ROOT / "examples" / "output_part2" / "backtest_demo" / "part2_backtest_monthly_returns.csv",
            panel_csv_path=ROOT / "examples" / "output_part2" / "backtest_demo" / "part2_competition_panel.csv",
            report_path=ROOT / "examples" / "output_part2" / "part2_report.json",
            chart_paths=[
                ROOT / "examples" / "output_part2" / "backtest_demo" / "part2_backtest_curve.svg",
                ROOT / "examples" / "output_part2" / "charts" / "top_sku_share.svg",
                ROOT / "examples" / "output_part2" / "charts" / "sweet_spot_band.svg",
                ROOT / "examples" / "output_part2" / "charts" / "negative_theme_intensity.svg",
                ROOT / "examples" / "output_part2" / "charts" / "listing_survival_curve.svg",
            ],
            extra_data_paths=[],
            notes=[
                "使用第二部分的竞争结构因子集。",
                "信号包含甜蜜带占比、白空间分数、评论拖累和货架生存表现。",
            ],
        ),
        BacktestBundle(
            slug="github_amazon_open_sample",
            name="GitHub Amazon 开源样本",
            scope="开源 Amazon 样本，清洗为第二部分标准数据包",
            summary_path=ROOT / "external_inputs" / "github_amazon_part2_demo" / "part2_backtest_summary.json",
            monthly_csv_path=ROOT / "external_inputs" / "github_amazon_part2_demo" / "part2_backtest_monthly_returns.csv",
            panel_csv_path=ROOT / "external_inputs" / "github_amazon_part2_demo" / "github_part2_panel.csv",
            report_path=ROOT / "external_inputs" / "github_amazon_part2_demo" / "report.json",
            chart_paths=[
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "part2_backtest_curve.svg",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "charts" / "top_sku_share.svg",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "charts" / "sweet_spot_band.svg",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "charts" / "negative_theme_intensity.svg",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "charts" / "listing_survival_curve.svg",
            ],
            extra_data_paths=[
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "listing_snapshots.csv",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "sold_transactions.csv",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "product_catalog.csv",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "reviews.csv",
                ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "source_manifest.json",
            ],
            notes=[
                "来源：GitHub 上的 luminati-io/Amazon-dataset-samples。",
                "成交量使用代理口径：bought_past_month 字段加排名校准估计。",
                "该样本是月度类目横截面，不是干净的持续 SKU 面板。",
            ],
        ),
    ]


def _panel_meta(panel_path: Path | None) -> dict[str, str]:
    if panel_path is None or not panel_path.exists():
        return {"rows": "0", "months": "0", "categories": "0"}
    rows = _read_csv_rows(panel_path)
    months = sorted({row.get("month", "") for row in rows if row.get("month")})
    categories = sorted({row.get("category", "") for row in rows if row.get("category")})
    return {
        "rows": str(len(rows)),
        "months": str(len(months)),
        "categories": str(len(categories)),
    }


def _summary_table_data(bundle: BacktestBundle, summary: dict, panel_meta: dict[str, str]) -> list[list[str]]:
    return [
        ["指标", "数值"],
        ["范围", bundle.scope],
        ["回测期数", str(summary.get("periods", 0))],
        ["面板行数", panel_meta["rows"]],
        ["月份数", panel_meta["months"]],
        ["类目数", panel_meta["categories"]],
        ["策略月均收益", _format_pct(float(summary.get("avg_strategy_return", 0.0)))],
        ["基准月均收益", _format_pct(float(summary.get("avg_benchmark_return", 0.0)))],
        ["月均超额收益", _format_pct(float(summary.get("avg_excess_return", 0.0)))],
        ["命中率", _format_pct(float(summary.get("hit_rate", 0.0)))],
        ["累计策略收益", _format_pct(float(summary.get("cumulative_strategy_return", 0.0)))],
        ["累计基准收益", _format_pct(float(summary.get("cumulative_benchmark_return", 0.0)))],
        ["累计超额收益", _format_pct(float(summary.get("cumulative_excess_return", 0.0)))],
    ]


def _monthly_table_data(summary_json: dict, monthly_csv_path: Path | None) -> list[list[str]]:
    if monthly_csv_path and monthly_csv_path.exists():
        rows = _read_csv_rows(monthly_csv_path)
        data = [["月份", "下期", "选中类别（名称保留原文）", "策略", "基准", "超额"]]
        for row in rows:
            data.append(
                [
                    row.get("month", ""),
                    row.get("next_month", ""),
                    row.get("selected_categories", ""),
                    _format_pct(float(row.get("strategy_return", "0") or 0)),
                    _format_pct(float(row.get("benchmark_return", "0") or 0)),
                    _format_pct(float(row.get("excess_return", "0") or 0)),
                ]
            )
        return data

    records = summary_json.get("monthly_records", [])
    data = [["月份", "下期", "选中类别（名称保留原文）", "策略", "基准", "超额"]]
    for row in records:
        data.append(
            [
                row.get("month", ""),
                row.get("next_month", ""),
                "|".join(row.get("selected_categories", [])),
                _format_pct(float(row.get("strategy_return", 0.0))),
                _format_pct(float(row.get("benchmark_return", 0.0))),
                _format_pct(float(row.get("excess_return", 0.0))),
            ]
        )
    return data


def _comparison_rows(bundles: list[BacktestBundle]) -> list[list[str]]:
    rows = [[
        "回测",
        "期数",
        "策略月均",
        "基准月均",
        "月均超额",
        "命中率",
        "累计策略",
        "累计基准",
    ]]
    for bundle in bundles:
        summary = _load_json(bundle.summary_path).get("summary", {})
        rows.append(
            [
                bundle.name,
                str(summary.get("periods", 0)),
                _format_pct(float(summary.get("avg_strategy_return", 0.0))),
                _format_pct(float(summary.get("avg_benchmark_return", 0.0))),
                _format_pct(float(summary.get("avg_excess_return", 0.0))),
                _format_pct(float(summary.get("hit_rate", 0.0))),
                _format_pct(float(summary.get("cumulative_strategy_return", 0.0))),
                _format_pct(float(summary.get("cumulative_benchmark_return", 0.0))),
            ]
        )
    return rows


def _make_table(data: list[list[str]], col_widths=None, header_bg=colors.HexColor("#dbeafe")) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102a43")),
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("FONTNAME", (0, 0), (-1, 0), "STSong-Light"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd2d9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _copy_if_exists(source_path: Path | None, target_path: Path) -> str | None:
    if source_path is None or not source_path.exists():
        return None
    target_path.parent.mkdir(parents=True, exist_ok=True)
    copy2(source_path, target_path)
    return str(target_path)


def _write_monthly_records_csv(summary_path: Path, target_path: Path) -> str | None:
    if not summary_path.exists():
        return None
    payload = _load_json(summary_path)
    monthly_records = payload.get("monthly_records", [])
    if not monthly_records:
        return None

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "month",
                "next_month",
                "selected_categories",
                "strategy_return",
                "benchmark_return",
                "excess_return",
            ]
        )
        for record in monthly_records:
            categories = record.get("selected_categories", [])
            if isinstance(categories, list):
                categories_value = "|".join(categories)
            else:
                categories_value = str(categories)
            writer.writerow(
                [
                    record.get("month", ""),
                    record.get("next_month", ""),
                    categories_value,
                    record.get("strategy_return", 0.0),
                    record.get("benchmark_return", 0.0),
                    record.get("excess_return", 0.0),
                ]
            )
    return str(target_path)


def _materialize_report_bundle(bundles: list[BacktestBundle], pdf_path: Path) -> dict:
    FINAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    VISUALIZATIONS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    bundle_manifest = []
    for bundle in bundles:
        bundle_visual_dir = VISUALIZATIONS_DIR / bundle.slug
        bundle_data_dir = DATA_DIR / bundle.slug

        visualization_files = []
        for source_path in bundle.chart_paths:
            copied_path = _copy_if_exists(source_path, bundle_visual_dir / source_path.name)
            if copied_path:
                visualization_files.append(copied_path)

        data_sources = [
            bundle.summary_path,
            bundle.monthly_csv_path,
            bundle.panel_csv_path,
            bundle.report_path,
            *bundle.extra_data_paths,
        ]
        data_files = []
        for source_path in data_sources:
            if source_path is None:
                continue
            copied_path = _copy_if_exists(source_path, bundle_data_dir / source_path.name)
            if copied_path:
                data_files.append(copied_path)

        if bundle.monthly_csv_path is None or not bundle.monthly_csv_path.exists():
            generated_monthly_csv = _write_monthly_records_csv(
                bundle.summary_path,
                bundle_data_dir / "monthly_returns.csv",
            )
            if generated_monthly_csv:
                data_files.append(generated_monthly_csv)

        bundle_manifest.append(
            {
                "slug": bundle.slug,
                "name": bundle.name,
                "report_data_dir": str(bundle_data_dir),
                "visualization_dir": str(bundle_visual_dir),
                "visualization_files": visualization_files,
                "data_files": data_files,
            }
        )

    manifest = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report_pdf": str(pdf_path),
        "reports_dir": str(REPORTS_DIR),
        "visualizations_dir": str(VISUALIZATIONS_DIR),
        "data_dir": str(DATA_DIR),
        "bundles": bundle_manifest,
    }
    INDEX_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _build_pdf() -> Path:
    registerFont(UnicodeCIDFont("STSong-Light"))
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCJK",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=20,
        leading=26,
        textColor=colors.HexColor("#102a43"),
    )
    heading_style = ParagraphStyle(
        "HeadingCJK",
        parent=styles["Heading2"],
        fontName="STSong-Light",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#102a43"),
    )
    body_style = ParagraphStyle(
        "BodyCJK",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#243b53"),
    )
    small_style = ParagraphStyle(
        "SmallCJK",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#52606d"),
    )

    manifest_label_map = {
        "platform": "平台",
        "transaction_mode": "成交口径",
        "capture_date": "抓取日期",
        "rows_in": "原始行数",
        "rank_sales_curve": "排名-销量校准曲线",
        "sample_size": "样本量",
        "intercept": "截距",
        "slope": "斜率",
    }
    manifest_value_map = {
        "bought_past_month_plus_rank_calibrated_proxy": "基于 bought_past_month 与排名校准的代理口径",
    }

    bundles = _build_backtest_bundles()
    story = []

    story.append(Paragraph("全部回测结果汇总 PDF", title_style))
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            "内容范围：第一部分演示、第二部分演示、GitHub 开源 Amazon 样本回测。",
            body_style,
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("总览对比", heading_style))
    story.append(Spacer(1, 2 * mm))
    story.append(
        _make_table(
            _comparison_rows(bundles),
            col_widths=[62 * mm, 16 * mm, 23 * mm, 23 * mm, 21 * mm, 18 * mm, 23 * mm, 23 * mm],
            header_bg=colors.HexColor("#c6f6d5"),
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        Paragraph(
            "说明：GitHub 外部样本属于开源横截面商品快照，交易量为代理估计。"
            "因此它更适合做框架验证，不适合直接当成正式商业结论。",
            small_style,
        )
    )

    for index, bundle in enumerate(bundles, start=1):
        payload = _load_json(bundle.summary_path)
        summary = payload.get("summary", {})
        monthly_records = payload.get("monthly_records", [])
        meta = _panel_meta(bundle.panel_csv_path)

        story.append(PageBreak())
        story.append(Paragraph(f"{index}. {bundle.name}", heading_style))
        story.append(Spacer(1, 2 * mm))
        for note in bundle.notes:
            story.append(Paragraph(f"- {note}", body_style))
        story.append(Spacer(1, 3 * mm))
        story.append(
            _make_table(
                _summary_table_data(bundle, summary, meta),
                col_widths=[48 * mm, 120 * mm],
            )
        )
        story.append(Spacer(1, 4 * mm))
        story.append(LineChartFlowable(f"{bundle.name}累计收益曲线", monthly_records))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("月度回测明细", body_style))
        story.append(Spacer(1, 2 * mm))
        story.append(
            _make_table(
                _monthly_table_data(payload, bundle.monthly_csv_path),
                col_widths=[20 * mm, 20 * mm, 98 * mm, 22 * mm, 22 * mm, 22 * mm],
                header_bg=colors.HexColor("#fde68a"),
            )
        )

    external_manifest = ROOT / "external_inputs" / "github_amazon_part2_demo" / "bundle" / "source_manifest.json"
    if external_manifest.exists():
        manifest = _load_json(external_manifest)
        story.append(PageBreak())
        story.append(Paragraph("附录：GitHub 外部样本说明", heading_style))
        story.append(Spacer(1, 2 * mm))
        manifest_rows = [["字段", "数值"]]
        for key, value in manifest.items():
            label = manifest_label_map.get(key, key)
            if isinstance(value, dict):
                translated = {
                    manifest_label_map.get(inner_key, inner_key): inner_value
                    for inner_key, inner_value in value.items()
                }
                manifest_rows.append([label, json.dumps(translated, ensure_ascii=False)])
            else:
                manifest_rows.append([label, str(manifest_value_map.get(str(value), value))])
        story.append(_make_table(manifest_rows, col_widths=[46 * mm, 126 * mm], header_bg=colors.HexColor("#fecaca")))

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    doc.build(story)
    _materialize_report_bundle(bundles, OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    pdf_path = _build_pdf()
    print(
        json.dumps(
            {
                "pdf": str(pdf_path),
                "reports_dir": str(REPORTS_DIR),
                "visualizations_dir": str(VISUALIZATIONS_DIR),
                "data_dir": str(DATA_DIR),
                "index": str(INDEX_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
