from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def export_pdf(text: str, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    for line in text.splitlines():
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        story.append(Paragraph(line.replace("# ", "").replace("## ", ""), styles["BodyText"]))
        story.append(Spacer(1, 4))
    doc.build(story)
    return str(output_path)
