from __future__ import annotations

import streamlit as st

from app.i18n.microcopy import CopyKey, t
from app.infra.config import AppSettings
from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_settings_panel(state: TurnState | None) -> None:
    if not state:
        st.info("Start a chat to manage settings.")
        return

    prefs = state.profile.data.get("preferences", {})
    consent = prefs.get("consent", {})
    retention = prefs.get("retention", {})
    ui_lang = prefs.get("language", "auto")
    if ui_lang == "auto":
        ui_lang = "en"

    st.subheader(t(ui_lang, CopyKey.SETTINGS_TITLE))

    current_lang = prefs.get("language", "auto")
    lang_index = ["auto", "en", "de"].index(current_lang)

    lang = st.selectbox(
        label=t(ui_lang, CopyKey.LANGUAGE), options=["auto", "en", "de"], index=lang_index
    )

    st.markdown("---")
    st.markdown(t(ui_lang, CopyKey.DISTANCE_UNIT))
    unit = st.radio(
        "",
        options=["km", "mi"],
        index=0 if prefs.get("distance_unit", "km") == "km" else 1,
        horizontal=True,
    )

    st.markdown("---")
    st.markdown(t(ui_lang, CopyKey.CONSENT_OCR))
    ocr_consent = st.checkbox(
        "I agree to let the system process my uploaded receipts.",
        value=bool(consent.get("ocr", False)),
    )

    st.markdown("---")
    st.markdown(t(ui_lang, CopyKey.RETENTION_TITLE))
    attach_days = st.number_input(
        "Attachments", min_value=0, value=retention.get("attachments_days", 0)
    )
    evidence_days = st.number_input(
        "Audit Logs", min_value=0, value=retention.get("evidence_days", 0)
    )

    if st.button(t(ui_lang, CopyKey.SAVE_SETTINGS)):
        payload = {
            "language": lang,
            "distance_unit": unit,
            "consent": {"ocr": ocr_consent},
            "retention": {"attachments_days": attach_days, "evidence_days": evidence_days},
        }
        action = UIAction(kind="set_preferences", payload=payload)
        # action = UIAction(kind="set_preferences", payload={"language": lang})
        store = ProfileStore(AppSettings().sqlite_path)
        new_state = apply_ui_action(state.user_id, action, state, store)

        st.session_state["last_result"] = new_state
        if new_state.errors:
            st.error(f"Failed to save: {new_state.errors[0].message}")
        else:
            st.success(t(ui_lang, CopyKey.SETTINGS_SAVED))
            st.rerun()
