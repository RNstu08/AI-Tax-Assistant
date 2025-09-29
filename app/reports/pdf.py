from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.i18n.microcopy import t
from app.memory.store import ProfileStore
from app.reports.summary import ReportSummary, build_summary


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def generate_pdf_bytes(summary: ReportSummary) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles, story = getSampleStyleSheet(), []

    lang = summary.language
    story.append(Paragraph(t(lang, "pdf_title"), styles["Title"]))
    story.append(
        Paragraph(
            f"User: {summary.user_id} • Profile Version: {summary.profile_version}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 8 * mm))

    if summary.itemization:
        data = [[t(lang, "table_category"), t(lang, "table_amount"), t(lang, "table_caps")]]
        data.extend(
            [
                [e.category.replace("_", " ").title(), e.amount_eur, ", ".join(e.caps_applied)]
                for e in summary.itemization
            ]
        )
        tbl = Table(data, hAlign="LEFT", colWidths=[80 * mm, 40 * mm, 40 * mm])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(tbl)
        story.append(Paragraph(t(lang, "pdf_total", amount=summary.totals_eur), styles["Heading3"]))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(t(lang, "pdf_checklist"), styles["Heading2"]))
    for item in summary.checklist:
        story.append(Paragraph(f"• {item}", styles["Normal"]))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(t(lang, "pdf_disclaimer"), styles["Heading2"]))
    story.append(Paragraph(summary.disclaimer, styles["Italic"]))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def export_pdf_and_log(user_id: str, state, store: ProfileStore) -> tuple[bytes, int]:
    summary = build_summary(state)
    pdf_bytes = generate_pdf_bytes(summary)
    # Logging evidence of the export is a crucial audit step
    # We will implement this logging in a future PR to keep this step focused
    return pdf_bytes, 0  # Returning a placeholder evidence ID
