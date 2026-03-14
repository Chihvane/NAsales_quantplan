from __future__ import annotations

from pathlib import Path

from jinja2 import Template


ROOT = Path(__file__).resolve().parent


def generate_report(snapshot: dict) -> str:
    template_path = ROOT / "report_template.md"
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.render(
        factor_score=round(snapshot["factor_score"], 3),
        profit_p10=round(snapshot["model_outputs"]["profit_p10"], 2),
        profit_p50=round(snapshot["model_outputs"]["profit_p50"], 2),
        profit_p90=round(snapshot["model_outputs"]["profit_p90"], 2),
        loss_probability=round(snapshot["model_outputs"]["loss_probability"], 3),
        free_capital=snapshot["free_capital"],
        required_capital=snapshot["required_capital"],
        decision=snapshot["decision"],
        portfolio_rows=snapshot["portfolio_rows"],
    )
