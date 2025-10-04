from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.memory.store import ProfileStore
from app.orchestrator.models import TurnState
from app.reports.json_export import export_json_and_log
from app.reports.pdf import export_pdf_and_log
from app.reports.summary import build_summary


def render_summary_panel(state: TurnState | None) -> None:
    st.subheader("Your Tax Deduction Summary")
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        - This table summarizes your calculated tax deductions so far.  <br>
        - Each row shows the deduction category, amount, and any tax caps applied. <br>
        - You can save, edit, or add receipts as you go!
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Summary and Export")
    if not (state and state.calc_results):
        st.info("Chat about some deductions to generate a summary.")
        return

    summary = build_summary(state)
    store = ProfileStore()

    st.markdown("### Export Options")
    all_categories = sorted([e.category for e in summary.itemization])

    # UI Controls for filtering and branding
    selected_categories = st.multiselect(
        "Include categories in export:", options=all_categories, default=all_categories
    )
    add_watermark = st.checkbox("Add 'DRAFT' watermark to PDF", value=True)

    col1, col2 = st.columns(2)
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        📝 You can download your full summary as a PDF or JSON for your own records
        or to show to a tax professional.*
        </p>
        """,
        unsafe_allow_html=True,
    )
    with col1:
        if st.button("Generate PDF"):
            with st.spinner("Generating PDF..."):
                pdf_bytes, _ = export_pdf_and_log(
                    state.user_id,
                    state,
                    store,
                    selected_categories,
                    "DRAFT" if add_watermark else None,
                )
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"DE_Tax_Assistant_Summary_Profile_{state.profile.version}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )
    with col2:
        if st.button("Generate JSON"):
            with st.spinner("Generating JSON..."):
                json_bytes, _ = export_json_and_log(
                    state.user_id, state, store, selected_categories
                )
                st.download_button(
                    label="Download JSON",
                    data=json_bytes,
                    file_name=f"tax_summary_{summary.hash}.json",
                    mime="application/json",
                )

    st.markdown("---")
    st.markdown(f"### Itemized Summary (Total: {summary.totals_eur})")
    st.dataframe(summary.itemization)
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        💡 What next?<br>
        Go to the Chat tab to try a new question or deduction.
        </p>
        """,
        unsafe_allow_html=True,
    )
