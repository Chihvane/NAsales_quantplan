from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Decision-OS-ER.pdf"


def draw_node(c: canvas.Canvas, x: int, y: int, width: int, height: int, title: str, fill_color) -> None:
    c.setFillColor(fill_color)
    c.roundRect(x, y, width, height, 10, stroke=1, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + width / 2, y + height / 2 - 4, title)


def draw_arrow(c: canvas.Canvas, x1: int, y1: int, x2: int, y2: int, label: str) -> None:
    c.setStrokeColor(colors.darkgray)
    c.line(x1, y1, x2, y2)
    c.line(x2, y2, x2 - 8, y2 + 4)
    c.line(x2, y2, x2 - 8, y2 - 4)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    c.drawString((x1 + x2) / 2 - 20, (y1 + y2) / 2 + 6, label)


def generate_pdf() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(letter))
    width, height = landscape(letter)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 32, "Decision OS v3.0 ER Diagram")
    c.setFont("Helvetica", 9)
    c.drawString(36, height - 48, "Generated from the production schema and repository design.")

    nodes = {
        "TENANT_REGISTRY": (40, 420, colors.HexColor("#dbeafe")),
        "FIELD_REGISTRY": (230, 420, colors.HexColor("#dcfce7")),
        "METRIC_REGISTRY": (410, 420, colors.HexColor("#dcfce7")),
        "FACTOR_REGISTRY": (590, 420, colors.HexColor("#dcfce7")),
        "MODEL_REGISTRY": (770, 420, colors.HexColor("#fef3c7")),
        "GATE_REGISTRY": (950, 420, colors.HexColor("#fde68a")),
        "DECISION_LOG": (950, 280, colors.HexColor("#fecaca")),
        "CAPITAL_POOL": (770, 280, colors.HexColor("#e9d5ff")),
        "RISK_BUDGET": (770, 180, colors.HexColor("#e9d5ff")),
        "PORTFOLIO_REGISTRY": (590, 280, colors.HexColor("#cffafe")),
        "EXECUTION_FEEDBACK": (950, 140, colors.HexColor("#bfdbfe")),
        "AUDIT_LOG": (1130, 280, colors.HexColor("#f5d0fe")),
    }

    for title, (x, y, fill) in nodes.items():
        draw_node(c, x, y, 140, 46, title, fill)

    arrows = [
        ("TENANT_REGISTRY", "FIELD_REGISTRY", "scope"),
        ("FIELD_REGISTRY", "METRIC_REGISTRY", "feeds"),
        ("METRIC_REGISTRY", "FACTOR_REGISTRY", "aggregates"),
        ("FACTOR_REGISTRY", "MODEL_REGISTRY", "inputs"),
        ("MODEL_REGISTRY", "GATE_REGISTRY", "evaluated_by"),
        ("GATE_REGISTRY", "DECISION_LOG", "produces"),
        ("CAPITAL_POOL", "DECISION_LOG", "capital"),
        ("RISK_BUDGET", "DECISION_LOG", "risk"),
        ("PORTFOLIO_REGISTRY", "DECISION_LOG", "allocation"),
        ("DECISION_LOG", "EXECUTION_FEEDBACK", "feedback"),
        ("DECISION_LOG", "AUDIT_LOG", "audit"),
    ]

    for source, target, label in arrows:
        sx, sy, _ = nodes[source]
        tx, ty, _ = nodes[target]
        draw_arrow(c, sx + 140, sy + 23, tx, ty + 23, label)

    c.setFont("Helvetica", 9)
    legend_y = 88
    c.drawString(36, legend_y, "Artifacts:")
    c.drawString(96, legend_y, "Mermaid source: docs/er_diagram.mmd")
    c.drawString(96, legend_y - 12, "Graphviz source: docs/er_diagram.dot")
    c.drawString(96, legend_y - 24, "Fallback PDF renderer: scripts/generate_er_pdf.py")

    c.showPage()
    c.save()
    return OUTPUT


if __name__ == "__main__":
    pdf_path = generate_pdf()
    print(pdf_path)
