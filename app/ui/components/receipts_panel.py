from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_receipts_panel(state: TurnState | None) -> None:
    """Renders the panel for uploading, processing, and importing receipts."""
    st.subheader("Receipts & Evidence")
    if not state:
        st.info("Start a chat to upload and process receipts.")
        return

    store = ProfileStore()

    category = st.selectbox(
        "Assign Category for New Uploads",
        options=["equipment", "donations", "general"],
        help="This category will be assigned to the files you upload below.",
    )

    uploaded_files = st.file_uploader(
        "Upload receipts (PDF, JPG, PNG)",
        type=["pdf", "jpg", "png"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        with st.spinner("Uploading and saving your files..."):
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
                    store.log_evidence(
                        user_id=state.user_id,
                        turn_id=state.correlation_id,
                        kind="receipt_upload",
                        payload={"filename": meta["filename"]},
                        result={"attachment_id": meta["id"]},
                    )
                except ValueError as e:
                    st.error(f"Failed to upload {file.name}: {e}")
        st.success("✅ Upload complete! Your files now appear in the list below.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### Process Uploaded Files")
    attachments = store.list_attachments(state.user_id)
    if not attachments:
        st.write("No files uploaded yet.")
        return

    for attachment in attachments:
        dt = datetime.fromtimestamp(attachment["created_at"] / 1000).strftime("%Y-%m-%d %H:%M")
        expander_title = f"📄 **{attachment['filename']}** (Uploaded: {dt})"

        with st.expander(expander_title):
            parsed = store.get_receipt_parse_by_attachment(attachment["id"])

            if not parsed:
                st.info("This receipt has not been processed yet.")
                if st.button("🔍 Run OCR", key=f"ocr_{attachment['id']}"):
                    with st.spinner("Processing document..."):
                        run_ocr_on_attachment(store, attachment["id"])
                    st.rerun()
            else:
                st.caption(f"Processed with: `{parsed['engine']}`")
                with st.form(key=f"import_form_{attachment['id']}"):
                    st.write("**Parsed Items (Select to Import into Profile):**")
                    items_from_parse = parsed["parsed_data"].get("items", [])
                    selected_item_indices = []

                    for i, item in enumerate(items_from_parse):
                        cols = st.columns([1, 4])
                        is_selected = cols[0].checkbox(
                            " ",
                            key=f"select_{attachment['id']}_{i}",
                            value=True,
                            label_visibility="collapsed",
                        )
                        cols[1].text(
                            f"{item.get('description', 'N/A')} - {item.get('total_eur', '0.00')}€"
                        )
                        if is_selected:
                            selected_item_indices.append(i)

                    submitted = st.form_submit_button("✅ Import Selected Items")
                    if submitted:
                        payload = {
                            "attachment_id": attachment["id"],
                            "item_indices": selected_item_indices,
                        }
                        action = UIAction(kind="import_parsed_items", payload=payload)

                        new_state = apply_ui_action(state.user_id, action, state, store)
                        st.session_state["last_result"] = new_state
                        st.success(
                            f"Imported {len(selected_item_indices)} items! "
                            "Ask for a new estimate in the Chat tab."
                        )
                        st.rerun()
