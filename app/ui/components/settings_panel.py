from __future__ import annotations

import streamlit as st

from app.i18n.microcopy import CopyKey, t
from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_settings_panel(state: TurnState | None) -> None:
    """Renders the panel for managing persistent user preferences, available at startup."""
    store = ProfileStore()
    # Load the profile directly so the panel works even without a chat session
    # For this prototype, we'll use a fixed user_id "demo"
    user_id = "demo"
    profile = store.get_profile(user_id)

    # Use the profile's language preference to render the UI, defaulting to English
    prefs = profile.data.get("preferences", {})
    ui_lang = prefs.get("language", "auto")
    if ui_lang == "auto":
        ui_lang = "en"

    st.subheader(t(ui_lang, CopyKey.SETTINGS_TITLE))

    # --- Language ---
    current_lang = prefs.get("language", "auto")
    lang_index = ["auto", "en", "de"].index(current_lang)
    lang = st.selectbox(
        label=t(ui_lang, CopyKey.LANGUAGE), options=["auto", "en", "de"], index=lang_index
    )

    # --- Distance Unit ---
    st.markdown("---")
    st.markdown(t(ui_lang, CopyKey.DISTANCE_UNIT))
    current_unit = prefs.get("distance_unit", "km")
    unit = st.radio(
        "", options=["km", "mi"], index=["km", "mi"].index(current_unit), horizontal=True
    )

    # --- OCR Consent ---
    st.markdown("---")
    consent = prefs.get("consent", {})
    ocr_consent = st.checkbox(
        label=t(ui_lang, CopyKey.CONSENT_OCR), value=bool(consent.get("ocr", False))
    )

    # --- Data Retention ---
    st.markdown("---")
    st.markdown(t(ui_lang, CopyKey.RETENTION_TITLE))
    retention = prefs.get("retention", {})
    attach_days = st.number_input(
        t(ui_lang, CopyKey.RETENTION_ATTACHMENTS_DAYS),
        min_value=0,
        value=retention.get("attachments_days", 0),
    )
    evidence_days = st.number_input(
        t(ui_lang, CopyKey.RETENTION_EVIDENCE_DAYS),
        min_value=0,
        value=retention.get("evidence_days", 0),
    )

    # --- Save Button ---
    if st.button(t(ui_lang, CopyKey.SAVE_SETTINGS)):
        payload = {
            "language": lang,
            "distance_unit": unit,
            "consent": {"ocr": ocr_consent},
            "retention": {"attachments_days": attach_days, "evidence_days": evidence_days},
        }
        action = UIAction(kind="set_preferences", payload=payload)

        # The backend needs a TurnState, so we create a minimal one for this action
        # If a chat has happened, use that state, otherwise create a temporary one.
        base_state = state or TurnState(
            correlation_id="", user_id=user_id, user_input="", profile=profile
        )

        new_state = apply_ui_action(user_id, action, base_state, store)

        # Update the session state to keep the whole app in sync
        st.session_state["last_result"] = new_state
        if new_state.errors:
            st.error(f"Failed to save: {new_state.errors[0].message}")
        else:
            st.success(t(ui_lang, CopyKey.SETTINGS_SAVED))
            st.rerun()
