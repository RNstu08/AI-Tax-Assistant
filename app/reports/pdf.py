from __future__ import annotations

import io
from collections.abc import Iterable
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.i18n.microcopy import CopyKey, t
from app.memory.store import ProfileStore
from app.orchestrator.models import TurnState
from app.reports.summary import ReportSummary, build_summary
from tools.money import D, fmt_eur  # FIX: Add the missing imports for D and fmt_eur


def _on_page(canvas: Any, doc: Any, watermark_text: str | None = None) -> None:
    """Draws the footer (page number) and optional watermark on each page."""
    canvas.saveState()
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
    # Watermark
    if watermark_text:
        canvas.setFont("Helvetica-Bold", 72)
        canvas.setFillColor(colors.Color(0.8, 0.8, 0.8, alpha=0.3))
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, watermark_text)
    canvas.restoreState()


def generate_pdf_bytes(
    summary: ReportSummary,
    include_categories: Iterable[str] | None = None,
    watermark_text: str | None = None,
) -> bytes:
    """Generates a PDF from a summary, with filtering and branding."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story: list[Flowable] = []
    lang = summary.language

    story.append(Paragraph(t(lang, CopyKey.PDF_TITLE), styles["Title"]))
    story.append(
        Paragraph(
            f"User: {summary.user_id} • Profile Version: {summary.profile_version}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 8 * mm))

    include = set(include_categories) if include_categories else None
    display_items = [e for e in summary.itemization if not include or e.category in include]

    if display_items:
        data = [
            [
                t(lang, CopyKey.TABLE_CATEGORY),
                t(lang, CopyKey.TABLE_AMOUNT),
                t(lang, CopyKey.TABLE_CAPS),
            ]
        ]
        total = D(0)
        for e in display_items:
            data.append(
                [e.category.replace("_", " ").title(), e.amount_eur, ", ".join(e.caps_applied)]
            )
            total += D(e.raw_amount)

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
        story.append(
            Paragraph(t(lang, CopyKey.PDF_TOTAL, amount=fmt_eur(total)), styles["Heading3"])
        )

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(t(lang, CopyKey.PDF_CHECKLIST), styles["Heading2"]))
    for item in summary.checklist:
        story.append(Paragraph(f"• {item}", styles["Normal"]))

    # In a real app, we would add sections for rule footnotes, attachments, etc. here

    doc.build(
        story,
        onFirstPage=lambda c, d: _on_page(c, d, watermark_text),
        onLaterPages=lambda c, d: _on_page(c, d, watermark_text),
    )
    return buf.getvalue()


def export_pdf_and_log(
    user_id: str,
    state: TurnState,
    store: ProfileStore,
    include_categories: Iterable[str] | None = None,
    watermark_text: str | None = None,
) -> tuple[bytes, int]:
    summary = build_summary(state)
    pdf_bytes = generate_pdf_bytes(summary, include_categories, watermark_text)
    # Logging evidence will be fully implemented in a future PR
    return pdf_bytes, 0
