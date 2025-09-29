from __future__ import annotations

import streamlit as st

from app.memory.store import ProfileStore
from app.reports.pdf import export_pdf_and_log
from app.reports.summary import build_summary  # FIX: Add the missing import


def render_summary_panel(state) -> None:
    """Renders the summary panel with itemization, checklist, and export button."""
    st.subheader("Summary and Export")
    if not (state and state.calc_results):
        st.info("Chat about some deductions to generate a summary.")
        return

    summary = build_summary(state)

    st.metric("Total Estimated Deduction", summary.totals_eur)

    st.dataframe(summary.itemization)

    with st.expander("Receipts & Evidence Checklist"):
        for item in summary.checklist:
            st.write(f"- {item}")

    if st.button("Export PDF"):
        pdf_bytes, _ = export_pdf_and_log(state.user_id, state, ProfileStore())
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"tax_summary_{summary.hash}.pdf",
            mime="application/pdf",
        )
