from __future__ import annotations

from pathlib import Path

from jinja2 import Template


ROOT = Path(__file__).resolve().parent


def generate_decision_report(snapshot: dict) -> str:
    template = Template((ROOT / "templates" / "report_template.md").read_text(encoding="utf-8"))
    return template.render(
        factor_score=round(snapshot["factor_score"], 4),
        profit_p50=round(snapshot["model_outputs"]["profit_p50"], 2),
        loss_probability=round(snapshot["model_outputs"]["loss_probability"], 4),
        decision=snapshot["decision"],
    )
