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
    ui_lang = prefs.get("language", "auto")
    if ui_lang == "auto":
        ui_lang = "en"

    st.subheader(t(ui_lang, CopyKey.SETTINGS_TITLE))

    current_lang = prefs.get("language", "auto")
    lang_index = ["auto", "en", "de"].index(current_lang)

    lang = st.selectbox(
        label=t(ui_lang, CopyKey.LANGUAGE), options=["auto", "en", "de"], index=lang_index
    )

    if st.button(t(ui_lang, CopyKey.SAVE_SETTINGS)):
        action = UIAction(kind="set_preferences", payload={"language": lang})
        store = ProfileStore(AppSettings().sqlite_path)
        new_state = apply_ui_action(state.user_id, action, state, store)

        st.session_state["last_result"] = new_state
        if new_state.errors:
            st.error(f"Failed to save: {new_state.errors[0].message}")
        else:
            st.success(t(ui_lang, CopyKey.SETTINGS_SAVED))
            st.rerun()
