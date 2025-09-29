from __future__ import annotations

import streamlit as st

from app.knowledge.ingest import build_index
from app.ui.components.actions_panel import render_actions_panel
from app.ui.components.chat_panel import render_chat_panel
from app.ui.components.profile_panel import render_profile_panel
from app.ui.components.settings_panel import render_settings_panel
from app.ui.components.summary_panel import render_summary_panel
from app.ui.components.trace_panel import render_trace_panel


@st.cache_resource
def startup() -> None:  # FIX: Add '-> None' return type annotation
    """Builds the rules index on the first run."""
    build_index()


def main() -> None:
    st.set_page_config(page_title="DE Tax Assistant (MVP)", layout="wide")
    st.title("DE Tax Assistant (MVP scaffold)")

    startup()

    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None

    col1, col2 = st.columns([2, 1])

    with col1:
        render_chat_panel()

    with col2:
        tabs = st.tabs(["Actions", "Trace", "Profile", "Settings"])
        with tabs[0]:
            render_actions_panel(st.session_state["last_result"])
        with tabs[1]:
            render_trace_panel(st.session_state["last_result"])
        with tabs[2]:
            render_profile_panel(st.session_state["last_result"])
        with tabs[3]:
            render_summary_panel(st.session_state["last_result"])
        with tabs[4]:
            render_settings_panel()


if __name__ == "__main__":
    main()
