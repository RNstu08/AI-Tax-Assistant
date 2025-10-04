from __future__ import annotations

import io
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.i18n.microcopy import CopyKey, t
from app.reports.summary import ReportSummary, build_summary


class PDFStyler:
    """Centralizes all styling for the PDF report for a consistent and modern look."""

    def __init__(self):
        # --- Color Palette ---
        self.primary_color = colors.HexColor("#0056B3")  # A professional blue
        self.text_color = colors.HexColor("#333333")  # Dark grey for text
        self.accent_color_light = colors.HexColor("#E8F1FF")  # Light blue for backgrounds
        self.grey_color = colors.grey
        self.light_grey_color = colors.HexColor("#F3F4F6")  # For alternating table rows

        # --- Base Styles ---
        self.styles = getSampleStyleSheet()
        self.styles.add(
            ParagraphStyle(
                name="Body",
                fontName="Helvetica",
                fontSize=10,
                textColor=self.text_color,
                leading=14,
            )
        )

        title_style = self.styles["Title"]
        title_style.fontName = "Helvetica-Bold"
        title_style.fontSize = 22
        title_style.textColor = self.primary_color
        title_style.spaceAfter = 8 * mm
        # --- END OF FIX ---

        self.styles.add(
            ParagraphStyle(
                name="H2",
                parent=self.styles["Body"],
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=self.primary_color,
                spaceAfter=4 * mm,
                spaceBefore=6 * mm,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Total",
                parent=self.styles["Body"],
                fontName="Helvetica-Bold",
                fontSize=11,
                alignment=2,  # Right aligned
                spaceBefore=4 * mm,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="ListItem",
                parent=self.styles["Body"],
                leftIndent=6 * mm,
                spaceAfter=2 * mm,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Body"],
                fontSize=8,
                textColor=self.grey_color,
            )
        )

    def get_modern_table_style(self) -> TableStyle:
        """Returns a clean, modern table style without grids."""
        return TableStyle(
            [
                # Header Style
                ("BACKGROUND", (0, 0), (-1, 0), self.primary_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                # General Cell Style
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("TEXTCOLOR", (0, 1), (-1, -1), self.text_color),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                # Zebra Striping (alternating row colors)
                ("BACKGROUND", (0, 1), (-1, -1), self.light_grey_color),
                ("BACKGROUND", (0, 2), (-1, -2), colors.white),
            ]
        )


def _on_page_stylish(
    canvas: Any, doc: Any, styler: PDFStyler, watermark_text: str | None = None
) -> None:
    """Draws the footer and watermark on each page using centralized styles."""
    canvas.saveState()
    # Footer
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    footer_text = f"DE Tax Assistant - Page {canvas.getPageNumber()} | Generated {date_str}"
    canvas.setFillColor(styler.grey_color)
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, footer_text)

    # Watermark
    if watermark_text:
        canvas.setFont("Helvetica-Bold", 72)
        canvas.setFillColor(colors.Color(0.85, 0.85, 0.85, alpha=0.3))
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, watermark_text)
    canvas.restoreState()


def _build_header(story: list, summary: ReportSummary, styler: PDFStyler):
    """Builds the main title and subtitle section."""
    story.append(Paragraph(t(summary.language, CopyKey.PDF_TITLE), styler.styles["Title"]))
    meta_text = (
        f"<b>User:</b> {summary.user_id} &nbsp;&nbsp; "
        f"<b>Profile Version:</b> {summary.profile_version}"
    )
    story.append(Paragraph(meta_text, styler.styles["Body"]))
    story.append(Spacer(1, 8 * mm))


def _build_intro_summary(story: list, summary: ReportSummary, styler: PDFStyler):
    """Builds the personalized plain-language summary section."""
    ded = {e.category: e for e in summary.itemization}
    equip_items = [e for e in summary.itemization if "equipment_item" in e.category]

    intro_text = (
        "This report summarizes the deductions you entered using the DE Tax "
        f"Assistant (v{summary.profile_version}) for your German tax return."
    )
    story.append(Paragraph(intro_text, styler.styles["Body"]))

    story.append(Spacer(1, 4 * mm))

    if "commuting" in ded:
        commute_text = (
            f"• <b>Commuting:</b> You reported work-related travel for a calculated "
            f"allowance of {ded['commuting'].amount_eur}."
        )
        story.append(Paragraph(commute_text, styler.styles["ListItem"]))

    if "home_office" in ded:
        ho_days = ded["home_office"].details.get("days", "N/A")
        ho_amount = ded["home_office"].amount_eur
        home_office_text = (
            f"• <b>Home Office:</b> You logged {ho_days} days, for a calculated lump sum "
            f"of {ho_amount}."
        )
        story.append(Paragraph(home_office_text, styler.styles["ListItem"]))

    if equip_items:
        equip_text = (
            f"• <b>Work Equipment:</b> You added {len(equip_items)} piece(s) of "
            "equipment for deduction."
        )
        story.append(Paragraph(equip_text, styler.styles["ListItem"]))

    if not any(k in ded for k in ["commuting", "home_office"]) and not equip_items:
        story.append(
            Paragraph("You haven't claimed any major deductions yet.", styler.styles["Body"])
        )


def _build_deductions_table(
    story: list, summary: ReportSummary, styler: PDFStyler, include_categories: set | None
):
    """Builds and styles the main table of itemized deductions."""
    story.append(Paragraph("Your Calculated Deductions", styler.styles["H2"]))

    display_items = [
        e for e in summary.itemization if not include_categories or e.category in include_categories
    ]
    if not display_items:
        story.append(Paragraph("No deduction amounts calculated yet.", styler.styles["Body"]))
        return

    # Prepare table data, wrapping amounts in Paragraphs for right alignment
    data = [["Category", "Amount", "Limits/Notes"]]
    for e in display_items:
        cap_note = ", ".join(e.caps_applied) if e.caps_applied else ""
        note = cap_note or (e.details.get("year") or "")
        data.append(
            [
                e.category.replace("_", " ").title(),
                Paragraph(e.amount_eur, styler.styles["Body"]),
                note,
            ]
        )

    tbl = Table(data, hAlign="LEFT", colWidths=[70 * mm, 40 * mm, 60 * mm])
    tbl.setStyle(styler.get_modern_table_style())
    story.append(tbl)

    total_para = Paragraph(f"<b>Total: {summary.totals_eur}</b>", styler.styles["Total"])
    story.append(total_para)


def _build_checklist_and_footer(story: list, summary: ReportSummary, styler: PDFStyler):
    """Builds the final checklist and disclaimer sections."""
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Receipts & Document Checklist", styler.styles["H2"]))
    for item in summary.checklist:
        story.append(Paragraph(f"• {item}", styler.styles["ListItem"]))

    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph(summary.disclaimer, styler.styles["Footer"]))


def generate_pdf_bytes(
    summary: ReportSummary,
    include_categories: Iterable[str] | None = None,
    watermark_text: str | None = None,
) -> bytes:
    """Generates a stylish, user-friendly PDF summary from report data."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )
    styler = PDFStyler()
    story: list = []

    # --- Build Document Sections ---
    _build_header(story, summary, styler)
    _build_intro_summary(story, summary, styler)
    _build_deductions_table(
        story, summary, styler, set(include_categories) if include_categories else None
    )
    _build_checklist_and_footer(story, summary, styler)

    # --- Compile the PDF ---
    def on_page_handler(canvas, doc):
        _on_page_stylish(canvas, doc, styler, watermark_text)

    doc.build(story, onFirstPage=on_page_handler, onLaterPages=on_page_handler)
    # on_page_handler = lambda canvas, doc: _on_page_stylish(canvas, doc, styler, watermark_text)
    # doc.build(story, onFirstPage=on_page_handler, onLaterPages=on_page_handler)
    return buf.getvalue()


# This function remains the same, as its logic is about orchestration, not presentation.
def export_pdf_and_log(
    user_id: str,
    state,
    store,
    include_categories: Iterable[str] | None = None,
    watermark_text: str | None = None,
) -> tuple[bytes, int]:
    summary = build_summary(state)
    pdf_bytes = generate_pdf_bytes(summary, include_categories, watermark_text)
    # Optionally log the export as evidence/event in store here if needed
    return pdf_bytes, 0
