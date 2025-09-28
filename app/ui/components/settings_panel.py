from __future__ import annotations

import streamlit as st


def render_settings_panel() -> None:
    st.subheader("Session Settings")
    year_options = [2024, 2025]
    current_year = st.session_state.get("filing_year_override", 2025)
    selected_year = st.selectbox(
        "Override Filing Year for this Session",
        options=year_options,
        index=year_options.index(current_year),
    )
    st.session_state["filing_year_override"] = selected_year
