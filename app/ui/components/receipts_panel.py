from datetime import datetime

import streamlit as st

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction
from app.safety.files import sanitize_filename


def render_receipts_panel(state: TurnState | None) -> None:
    st.subheader("Receipts & Documents")

    # --- SHOW FRIENDLY OCR CONSENT WARNING IF BLOCKED LAST TIME ---
    if st.session_state.get("ocr_blocked", False):
        st.warning(
            "OCR consent not given. To use receipt text extraction, please go to "
            "the **Settings** tab and enable 'Allow processing of uploaded receipts (OCR)'."
        )
        # Optionally: "Go to Settings" button if you track tab in session state
        if st.button("Go to Settings"):
            st.session_state["active_tab"] = "Settings"
        st.session_state["ocr_blocked"] = False  # reset so not sticky forever

    if not state:
        st.info("Start a chat to upload and process receipts.")
        return

    store = ProfileStore()
    category = st.selectbox(
        "Assign Category for New Uploads",
        options=["equipment", "donations", "general", "other"],
        help="Pick a category for your upload (use 'other' for random docs).",
    )

    if "pending_uploads" not in st.session_state:
        st.session_state["pending_uploads"] = []

    uploaded_files = st.file_uploader(
        "Choose receipts or other documents (PDF, JPG, PNG)",
        type=["pdf", "jpg", "png"],
        accept_multiple_files=True,
        key="receipt_file_uploader",
    )

    if uploaded_files:
        for file in uploaded_files:
            key = (file.name, file.size)
            if key not in st.session_state["pending_uploads"]:
                st.session_state["pending_uploads"].append(key)
        st.success(
            f"{len(uploaded_files)} file(s) staged! For each, review below and click"
            "**Add to My List** to finish upload."
        )

    st.write("---")
    if st.session_state["pending_uploads"]:
        st.write("#### Staged Files (Ready to Add):")
        for idx, (name, size) in enumerate(st.session_state["pending_uploads"]):
            st.markdown(f"- **{sanitize_filename(name)}** ({size//1024} KB)")
            if st.button(f"Add to My List: {name}", key=f"add_file_{idx}"):
                for file in uploaded_files:
                    if (file.name, file.size) == (name, size):
                        try:
                            meta = store.add_attachment(
                                state.user_id,
                                sanitize_filename(file.name),
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
                            st.success(f"Added {sanitize_filename(file.name)} to your file list!")
                        except Exception as e:
                            st.error(f"Upload problem: {e}")
                        break
                st.session_state["pending_uploads"].remove((name, size))
                st.rerun()

    st.markdown("---")
    st.markdown("#### Your Files (Recent first)")
    attachments = store.list_attachments(state.user_id)
    N_RECENT = 8
    show_all = st.checkbox(f"Show all files ({len(attachments)})", value=False)
    display_attachments = attachments if show_all else attachments[:N_RECENT]
    if not attachments:
        st.info("No files uploaded yet.")
        return

    for attachment in display_attachments:
        dt = datetime.fromtimestamp(attachment["created_at"] / 1000).strftime("%Y-%m-%d %H:%M")
        label = f"📄 {attachment['filename']} (Uploaded: {dt} | {attachment['category']})"
        with st.expander(label, expanded=False):
            parsed = store.get_receipt_parse_by_attachment(attachment["id"])
            if parsed and parsed["parsed_data"]["items"]:
                for item in parsed["parsed_data"]["items"]:
                    # Simplified category guessing (very basic -- use smarter rules in prod!)
                    desc = item.get("description", "").lower()
                    if any(word in desc for word in ["ipad", "laptop", "macbook", "notebook"]):
                        # Ask the user for confirmation, or auto preselect
                        st.info(
                            f"💡 It looks like '{item['description']}' might be work equipment. "
                            f"Would you like to import this to your 2025 deductions?"
                        )

            st.caption(
                f"Type: {attachment['content_type']} (Size: {attachment['size_bytes']//1024} KB)"
            )
            # For normal user display:
            st.markdown(
                f"🆔 <b>File Integrity ID:</b> <code>...{attachment['sha256'][-8:]}</code>",
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <p style='color:#808080; font-size:14px; font-style:italic;'>
                This secure ID is a digital fingerprint for your file.<br>
                It helps auditors and the assistant ensure your document is authentic and unchanged.
                </p>
                """,
                unsafe_allow_html=True,
            )

            # # For technical details:
            # with st.expander("Show full technical details"):
            #     st.write(f"Full SHA256 hash: {attachment['sha256']}")
            # st.write(f"SHA: ...{attachment['sha256'][-8:]}")
            just_ocrd = st.session_state.get("just_ocr_id") == attachment["id"]
            if not parsed:
                st.info("Not OCR-processed yet. Click below to extract text/data.")
                if st.button(f"Run OCR - {attachment['id']}", key=f"ocr_{attachment['id']}"):
                    try:
                        run_ocr_on_attachment(store, attachment["id"])
                        st.session_state["just_ocr_id"] = attachment["id"]
                        st.success("OCR complete!")
                    except PermissionError:
                        st.session_state["ocr_blocked"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"OCR failed: {e}")
                    st.rerun()
            elif parsed["parsed_data"]["items"]:
                if just_ocrd:
                    st.info(
                        "✅ OCR complete! Now select the item(s) below and click"
                        " **Import Selected** "
                        "to add them to your deductions profile. Only imported items will be "
                        "counted in your tax summary and answers."
                    )
                    st.session_state["just_ocr_id"] = None
                with st.form(key=f"import_form_{attachment['id']}"):
                    st.write("**Parsed Items (Select to Import):**")
                    items_to_import = []
                    for i, item in enumerate(parsed["parsed_data"]["items"]):
                        cols = st.columns([1, 5])
                        is_selected = cols[0].checkbox(
                            "", key=f"select_{attachment['id']}_{i}", value=True
                        )
                        item_text = (
                            f"**{item.get('description', 'N/A')}** — "
                            f"{item.get('total_eur', '0.00')} €"
                        )
                        cols[1].markdown(item_text, unsafe_allow_html=True)

                        if is_selected:
                            items_to_import.append(item)
                    if st.form_submit_button("✅ Import Selected"):
                        action = UIAction(
                            kind="import_parsed_items", payload={"items": items_to_import}
                        )
                        new_state = apply_ui_action(state.user_id, action, state, store)
                        st.session_state["last_result"] = new_state
                        st.success(
                            f"Imported {len(items_to_import)} item(s)! You can review all imported"
                            "items in your Profile tab."
                        )
                        st.rerun()
                st.caption(
                    "Imported items will show up in your Profile and be used in summary,"
                    " PDF export, and all calculations."
                )
            else:
                st.warning("✅ OCR complete, but no deductible items found.")

    if len(attachments) > N_RECENT:
        st.caption(
            f"Showing {N_RECENT} recent. Check the box above for all ({len(attachments)}) files."
        )
