from __future__ import annotations

from html import escape
from pathlib import Path


def _write_svg(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _format_value(value: float, as_percent: bool) -> str:
    if as_percent:
        return f"{value * 100:.1f}%"
    if float(value).is_integer():
        return f"{int(value)}"
    return f"{value:.2f}"


def _render_line_chart(
    series: dict[str, float],
    title: str,
    output_path: Path,
) -> None:
    width = 960
    height = 540
    left = 80
    right = 40
    top = 60
    bottom = 70
    plot_width = width - left - right
    plot_height = height - top - bottom

    labels = list(series.keys())
    values = list(series.values())
    max_value = max(values) if values else 1
    y_max = max(max_value * 1.1, 1)
    step_x = plot_width / max(len(values) - 1, 1)

    points = []
    for index, value in enumerate(values):
        x = left + index * step_x
        y = top + plot_height - (value / y_max) * plot_height
        points.append((x, y, value, labels[index]))

    grid_lines = []
    for tick in range(6):
        y = top + plot_height - (plot_height / 5) * tick
        tick_value = y_max / 5 * tick
        grid_lines.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            f'stroke="#d9dde7" stroke-width="1" />'
        )
        grid_lines.append(
            f'<text x="{left - 12}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12" fill="#5f6b7a">{tick_value:.0f}</text>'
        )

    x_labels = []
    for x, _, _, label in points:
        x_labels.append(
            f'<text x="{x:.1f}" y="{height - 25}" text-anchor="middle" '
            f'font-size="12" fill="#5f6b7a">{escape(label)}</text>'
        )

    polyline_points = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
    circles = []
    value_labels = []
    for x, y, value, _ in points:
        circles.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#1f77b4" />'
        )
        value_labels.append(
            f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
            f'font-size="11" fill="#1f77b4">{value:.0f}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{left}" y="32" font-size="24" font-family="Arial, sans-serif" fill="#102a43">{escape(title)}</text>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  {''.join(grid_lines)}
  <polyline fill="none" stroke="#1f77b4" stroke-width="3" points="{polyline_points}" />
  {''.join(circles)}
  {''.join(value_labels)}
  {''.join(x_labels)}
</svg>"""
    _write_svg(output_path, svg)


def _render_vertical_bar_chart(
    series: dict[str, float],
    title: str,
    output_path: Path,
    as_percent: bool = False,
) -> None:
    width = 960
    height = 540
    left = 80
    right = 40
    top = 60
    bottom = 90
    plot_width = width - left - right
    plot_height = height - top - bottom

    labels = list(series.keys())
    values = list(series.values())
    max_value = max(values) if values else 1
    y_max = max(max_value * 1.15, 1)
    slot_width = plot_width / max(len(values), 1)
    bar_width = slot_width * 0.56

    grid_lines = []
    for tick in range(6):
        y = top + plot_height - (plot_height / 5) * tick
        tick_value = y_max / 5 * tick
        grid_lines.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            f'stroke="#d9dde7" stroke-width="1" />'
        )
        grid_lines.append(
            f'<text x="{left - 12}" y="{y + 5:.1f}" text-anchor="end" '
            f'font-size="12" fill="#5f6b7a">{_format_value(tick_value, as_percent)}</text>'
        )

    bars = []
    labels_svg = []
    value_labels = []
    for index, (label, value) in enumerate(series.items()):
        x = left + index * slot_width + (slot_width - bar_width) / 2
        bar_height = (value / y_max) * plot_height if y_max else 0
        y = top + plot_height - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'rx="8" fill="#2ca58d" />'
        )
        value_labels.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
            f'font-size="12" fill="#1f2933">{_format_value(value, as_percent)}</text>'
        )
        labels_svg.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - 28}" text-anchor="middle" '
            f'font-size="12" fill="#5f6b7a">{escape(label)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{left}" y="32" font-size="24" font-family="Arial, sans-serif" fill="#102a43">{escape(title)}</text>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" stroke="#7b8794" stroke-width="1.5" />
  {''.join(grid_lines)}
  {''.join(bars)}
  {''.join(value_labels)}
  {''.join(labels_svg)}
</svg>"""
    _write_svg(output_path, svg)


def _render_horizontal_bar_chart(
    series: dict[str, float],
    title: str,
    output_path: Path,
    as_percent: bool = False,
) -> None:
    width = 960
    height = 540
    left = 200
    right = 60
    top = 60
    bottom = 40
    plot_width = width - left - right
    plot_height = height - top - bottom

    values = list(series.values())
    max_value = max(values) if values else 1
    x_max = max(max_value * 1.1, 1)
    slot_height = plot_height / max(len(series), 1)
    bar_height = slot_height * 0.56

    grid_lines = []
    for tick in range(6):
        x = left + (plot_width / 5) * tick
        tick_value = x_max / 5 * tick
        grid_lines.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height - bottom}" '
            f'stroke="#d9dde7" stroke-width="1" />'
        )
        grid_lines.append(
            f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" '
            f'font-size="12" fill="#5f6b7a">{_format_value(tick_value, as_percent)}</text>'
        )

    bars = []
    labels_svg = []
    value_labels = []
    for index, (label, value) in enumerate(series.items()):
        y = top + index * slot_height + (slot_height - bar_height) / 2
        bar_width = (value / x_max) * plot_width if x_max else 0
        bars.append(
            f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" '
            f'rx="8" fill="#ef8354" />'
        )
        labels_svg.append(
            f'<text x="{left - 12}" y="{y + bar_height / 2 + 4:.1f}" text-anchor="end" '
            f'font-size="12" fill="#5f6b7a">{escape(label)}</text>'
        )
        value_labels.append(
            f'<text x="{left + bar_width + 10:.1f}" y="{y + bar_height / 2 + 4:.1f}" '
            f'font-size="12" fill="#1f2933">{_format_value(value, as_percent)}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f8fafc" />
  <text x="{left}" y="32" font-size="24" font-family="Arial, sans-serif" fill="#102a43">{escape(title)}</text>
  {''.join(grid_lines)}
  {''.join(bars)}
  {''.join(labels_svg)}
  {''.join(value_labels)}
</svg>"""
    _write_svg(output_path, svg)


def generate_part1_chart_assets(report: dict, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trend_series = (
        report.get("sections", {})
        .get("1.1", {})
        .get("metrics", {})
        .get("trend", {})
        .get("monthly_average_interest", {})
    )
    price_band_series = (
        report.get("sections", {})
        .get("1.5", {})
        .get("metrics", {})
        .get("price_band_share", {})
    )
    channel_series = {
        row["channel"]: row["revenue_share"]
        for row in report.get("sections", {}).get("1.4", {}).get("metrics", {}).get("channels", [])
    }

    trend_path = output_dir / "market_demand_trend.svg"
    price_band_path = output_dir / "listed_price_band_share.svg"
    channel_path = output_dir / "channel_structure.svg"

    _render_line_chart(trend_series, "Market Demand Trend", trend_path)
    _render_vertical_bar_chart(
        price_band_series,
        "Listed Price Band Share",
        price_band_path,
        as_percent=True,
    )
    _render_horizontal_bar_chart(
        channel_series,
        "Channel Revenue Share",
        channel_path,
        as_percent=True,
    )

    return {
        "trend_chart": str(trend_path),
        "price_band_chart": str(price_band_path),
        "channel_chart": str(channel_path),
    }


def generate_part2_chart_assets(report: dict, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    top_sku_series = {
        row["canonical_sku"]: row["gmv_share"]
        for row in report.get("sections", {}).get("2.1", {}).get("metrics", {}).get("top_skus", [])[:8]
    }
    sweet_spot_series = (
        report.get("sections", {})
        .get("2.2", {})
        .get("metrics", {})
        .get("price_band_share", {})
    )
    pain_point_series = {
        row["theme"]: row["intensity"]
        for row in report.get("sections", {}).get("2.5", {}).get("metrics", {}).get("pain_points", [])
    }
    survival_series = {
        str(row["day"]): row["survival_rate"]
        for row in report.get("sections", {}).get("2.6", {}).get("metrics", {}).get("survival_curve", [])
    }

    top_sku_path = output_dir / "top_sku_share.svg"
    sweet_spot_path = output_dir / "sweet_spot_band.svg"
    pain_point_path = output_dir / "negative_theme_intensity.svg"
    survival_path = output_dir / "listing_survival_curve.svg"

    _render_horizontal_bar_chart(
        top_sku_series,
        "Top SKU GMV Share",
        top_sku_path,
        as_percent=True,
    )
    _render_vertical_bar_chart(
        sweet_spot_series,
        "Sweet Spot Price Band Share",
        sweet_spot_path,
        as_percent=True,
    )
    _render_horizontal_bar_chart(
        pain_point_series,
        "Negative Theme Intensity",
        pain_point_path,
        as_percent=False,
    )
    _render_line_chart(
        survival_series,
        "Listing Survival Curve",
        survival_path,
    )

    return {
        "top_sku_chart": str(top_sku_path),
        "sweet_spot_chart": str(sweet_spot_path),
        "pain_point_chart": str(pain_point_path),
        "survival_chart": str(survival_path),
    }


def generate_part3_chart_assets(report: dict, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    supplier_share_series = (
        report.get("sections", {})
        .get("3.1", {})
        .get("metrics", {})
        .get("supplier_type_share", {})
    )
    incoterm_cost_series = (
        report.get("sections", {})
        .get("3.2", {})
        .get("metrics", {})
        .get("incoterm_median_quoted_cost", {})
    )
    cost_breakdown_series = (
        report.get("sections", {})
        .get("3.5", {})
        .get("metrics", {})
        .get("cost_breakdown", {})
    )
    risk_series = {
        row["risk_name"]: row["severity_score"]
        for row in report.get("sections", {}).get("3.6", {}).get("metrics", {}).get("priority_risks", [])
    }
    monte_carlo_margin_band = (
        report.get("sections", {})
        .get("3.5", {})
        .get("metrics", {})
        .get("monte_carlo", {})
        .get("percentile_bands", {})
        .get("net_margin_rate", {})
    )
    sensitivity_rows = (
        report.get("sections", {})
        .get("3.5", {})
        .get("metrics", {})
        .get("monte_carlo", {})
        .get("sensitivity", [])
    )
    sensitivity_series = {
        row["driver"]: abs(row["downside_impact"])
        for row in sensitivity_rows[:6]
    }

    supplier_path = output_dir / "supplier_type_share.svg"
    incoterm_path = output_dir / "incoterm_median_cost.svg"
    cost_path = output_dir / "landed_cost_breakdown.svg"
    risk_path = output_dir / "risk_priority.svg"
    monte_carlo_path = output_dir / "monte_carlo_margin_band.svg"
    sensitivity_path = output_dir / "monte_carlo_sensitivity.svg"

    _render_horizontal_bar_chart(
        supplier_share_series,
        "Supplier Type Share",
        supplier_path,
        as_percent=True,
    )
    _render_vertical_bar_chart(
        incoterm_cost_series,
        "Incoterm Median Quoted Cost",
        incoterm_path,
        as_percent=False,
    )
    _render_horizontal_bar_chart(
        cost_breakdown_series,
        "Best Scenario Landed Cost Breakdown",
        cost_path,
        as_percent=False,
    )
    _render_horizontal_bar_chart(
        risk_series,
        "Risk Priority",
        risk_path,
        as_percent=False,
    )
    _render_vertical_bar_chart(
        monte_carlo_margin_band,
        "Monte Carlo Net Margin Rate Band",
        monte_carlo_path,
        as_percent=True,
    )
    _render_horizontal_bar_chart(
        sensitivity_series,
        "Monte Carlo Sensitivity",
        sensitivity_path,
        as_percent=False,
    )

    return {
        "supplier_share_chart": str(supplier_path),
        "incoterm_cost_chart": str(incoterm_path),
        "landed_cost_chart": str(cost_path),
        "risk_chart": str(risk_path),
        "monte_carlo_chart": str(monte_carlo_path),
        "sensitivity_chart": str(sensitivity_path),
    }


def generate_part4_chart_assets(report: dict, output_dir: str | Path) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    channel_margin_series = {
        row["channel"]: row["contribution_margin_rate"]
        for row in report.get("sections", {}).get("4.5", {}).get("metrics", {}).get("channel_pnl", [])
    }
    traffic_source_series = (
        report.get("sections", {})
        .get("4.4", {})
        .get("metrics", {})
        .get("traffic_source_sessions_share", {})
    )
    payback_series = {
        row["channel"]: row["payback_period_months"]
        for row in report.get("sections", {}).get("4.5", {}).get("metrics", {}).get("channel_pnl", [])
    }
    roi_band_series = {
        channel: metrics.get("roi", {}).get("p50", 0.0)
        for channel, metrics in report.get("sections", {})
        .get("4.5", {})
        .get("metrics", {})
        .get("monte_carlo", {})
        .get("channels", {})
        .items()
    }

    margin_path = output_dir / "channel_contribution_margin.svg"
    traffic_path = output_dir / "traffic_source_mix.svg"
    payback_path = output_dir / "channel_payback_period.svg"
    roi_band_path = output_dir / "roi_band.svg"

    _render_horizontal_bar_chart(
        channel_margin_series,
        "Channel Contribution Margin",
        margin_path,
        as_percent=True,
    )
    _render_vertical_bar_chart(
        traffic_source_series,
        "Traffic Source Session Share",
        traffic_path,
        as_percent=True,
    )
    _render_horizontal_bar_chart(
        payback_series,
        "Channel Payback Period (Months)",
        payback_path,
        as_percent=False,
    )
    _render_horizontal_bar_chart(
        roi_band_series,
        "Monte Carlo ROI P50",
        roi_band_path,
        as_percent=False,
    )

    return {
        "channel_margin_chart": str(margin_path),
        "traffic_source_chart": str(traffic_path),
        "channel_payback_chart": str(payback_path),
        "roi_band_chart": str(roi_band_path),
    }
