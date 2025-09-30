from __future__ import annotations

import streamlit as st

from app.i18n.microcopy import t
from app.infra.config import AppSettings
from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_settings_panel(state: TurnState | None) -> None:
    """Renders the panel for managing persistent user preferences."""
    if not state:
        st.info("Start a chat to manage settings.")
        return
    prefs = state.profile.data.get("preferences", {})
    lang = st.selectbox(
        "Language",
        options=["auto", "en", "de"],
        index=["auto", "en", "de"].index(prefs.get("language", "auto")),
    )
    if st.button("Save Settings"):
        action = UIAction(kind="set_preferences", payload={"language": lang})
        store = ProfileStore()
        new_state = apply_ui_action(state.user_id, action, state, store)
        st.session_state["last_result"] = new_state
        st.success("Settings saved.")
        st.rerun()
    # def render_settings_panel(state: TurnState | None) -> None:
    #     """Renders the panel for managing persistent user preferences."""
    #     if not state:
    #         st.info("Start a chat to manage settings.")
    #         return

    # Determine the language for the UI labels themselves
    ui_lang = state.profile.data.get("preferences", {}).get("language", "auto")
    if ui_lang == "auto":
        ui_lang = "en"  # Default UI to English if preference is auto

    st.subheader(t(ui_lang, "settings_title"))

    # Get current preferences from the profile, with safe defaults
    prefs = state.profile.data.get("preferences", {})
    current_lang = prefs.get("language", "auto")

    # Language Selector
    lang = st.selectbox(
        label=t(ui_lang, "language"),
        options=["auto", "en", "de"],
        index=["auto", "en", "de"].index(current_lang),
    )

    if st.button("Save Settings"):
        action = UIAction(kind="set_preferences", payload={"language": lang})
        # We need a store instance to apply the action
        store = ProfileStore(AppSettings().sqlite_path)
        new_state = apply_ui_action(state.user_id, action, state, store)

        st.session_state["last_result"] = new_state
        if new_state.errors:
            st.error(f"Failed to save: {new_state.errors[0].message}")
        else:
            st.success("Settings saved.")
            st.rerun()
