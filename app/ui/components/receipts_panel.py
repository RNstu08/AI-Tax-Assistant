from __future__ import annotations

import streamlit as st

from app.memory.store import ProfileStore
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
    st.markdown("**Your Uploaded Files**")
    attachments = store.list_attachments(state.user_id)
    if not attachments:
        st.write("No files uploaded yet.")
    else:
        st.dataframe(attachments)
