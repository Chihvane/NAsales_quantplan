from __future__ import annotations

import csv
import json
from pathlib import Path


def write_json(path: str | Path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_csv(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_curve_svg(path: str | Path, strategy_curve: list[float], benchmark_curve: list[float], title: str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 960, 420
    left, top = 60, 60
    chart_w, chart_h = 840, 280
    all_values = strategy_curve + benchmark_curve or [1.0]
    min_v, max_v = min(all_values), max(all_values)
    spread = max(max_v - min_v, 0.0001)

    def to_points(curve: list[float]) -> str:
        if not curve:
            return ""
        points = []
        for index, value in enumerate(curve):
            x = left + (index / max(len(curve) - 1, 1)) * chart_w
            y = top + chart_h - ((value - min_v) / spread) * chart_h
            points.append(f"{x:.2f},{y:.2f}")
        return " ".join(points)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#f8fafc"/>
  <text x="{left}" y="32" font-size="24" font-family="Arial, sans-serif" fill="#0f172a">{title}</text>
  <line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#94a3b8"/>
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#94a3b8"/>
  <polyline fill="none" stroke="#2563eb" stroke-width="3" points="{to_points(strategy_curve)}"/>
  <polyline fill="none" stroke="#f97316" stroke-width="3" points="{to_points(benchmark_curve)}"/>
  <text x="{left + chart_w - 160}" y="{top + 18}" font-size="12" font-family="Arial, sans-serif" fill="#2563eb">Strategy</text>
  <text x="{left + chart_w - 90}" y="{top + 18}" font-size="12" font-family="Arial, sans-serif" fill="#f97316">Benchmark</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")
    return path


def write_markdown_report(path: str | Path, summary: dict, artifacts: dict[str, str]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "# Decision OS Backtest Report",
            "",
            "## Summary",
            f"- Periods: {summary['periods']}",
            f"- GO count: {summary['go_count']}",
            f"- Reject count: {summary['reject_count']}",
            f"- Strategy cumulative return: {summary['strategy_cumulative_return']:.2%}",
            f"- Benchmark cumulative return: {summary['benchmark_cumulative_return']:.2%}",
            f"- Alpha: {summary['alpha']:.2%}",
            f"- Strategy max drawdown: {summary['strategy_max_drawdown']:.2%}",
            f"- Decision hit rate: {summary['decision_hit_rate']:.2%}",
            f"- Rejection precision: {summary['rejection_precision']:.2%}",
            "",
            "## Artifacts",
            *(f"- {key}: {value}" for key, value in artifacts.items()),
        ]
    )
    path.write_text(body, encoding="utf-8")
    return path
