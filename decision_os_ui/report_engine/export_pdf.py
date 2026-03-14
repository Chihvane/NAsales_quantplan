from __future__ import annotations

from pathlib import Path

import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def export_markdown_and_pdf(markdown_text: str, output_dir: str | Path, basename: str) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / f"{basename}.md"
    html_path = output_dir / f"{basename}.html"
    pdf_path = output_dir / f"{basename}.pdf"

    markdown_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(markdown.markdown(markdown_text), encoding="utf-8")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(f"<b>{line[2:]}</b>", styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(f"<b>{line[3:]}</b>", styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"&bull; {line[2:]}", styles["BodyText"]))
        else:
            story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 6))
    doc.build(story)

    return {
        "markdown_path": str(markdown_path),
        "html_path": str(html_path),
        "pdf_path": str(pdf_path),
    }
