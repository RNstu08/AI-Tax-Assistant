from __future__ import annotations

import json

import streamlit as st

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment
from app.orchestrator.models import TurnState


def render_receipts_panel(state: TurnState | None) -> None:
    st.subheader("Receipts & Evidence")
    if not state:
        st.info("Start a chat to upload receipts.")
        return

    store = ProfileStore()
    category = st.selectbox(
        "Assign Category for Upload", options=["equipment", "donations", "commuting", "general"]
    )

    uploaded_files = st.file_uploader(
        "Upload receipts (PDF, JPG, PNG)", type=["pdf", "jpg", "png"], accept_multiple_files=True
    )
    if uploaded_files:
        for file in uploaded_files:
            try:
                meta = store.add_attachment(
                    state.user_id,
                    file.name,
                    file.type,
                    file.getvalue(),
                    category,
                    state.correlation_id,
                )
                st.success(f"Uploaded {meta['filename']} ({meta['size_bytes'] // 1024} KB)")
            except ValueError as e:
                st.error(f"Failed to upload {file.name}: {e}")

    st.markdown("---")
    st.markdown("**Process Uploaded Files**")
    attachments = store.list_attachments(state.user_id)
    for attachment in attachments:
        with st.expander(f"File: {attachment['filename']}"):
            cols = st.columns([3, 1])
            cols[0].write(
                f"Category: {attachment['category']}, Size: {attachment['size_bytes'] // 1024} KB"
            )
            if cols[1].button("Run OCR", key=f"ocr_{attachment['id']}"):
                with st.spinner("Performing OCR..."):
                    run_ocr_on_attachment(store, attachment["id"])

            # Display parsed results if they exist
            parsed = store.get_receipt_parse_by_attachment(attachment["id"])
            if parsed:
                st.caption(f"Parsed with: {parsed['engine']}")
                st.code(json.dumps(parsed["parsed_data"]["items"], indent=2), language="json")
                # In a full app, we'd add an "Import" button here
