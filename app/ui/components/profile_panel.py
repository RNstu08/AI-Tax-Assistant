from __future__ import annotations

import json

import streamlit as st

from app.orchestrator.models import TurnState


def render_profile_panel(state: TurnState | None) -> None:
    st.subheader("User Profile (Read-Only)")
    if not state:
        st.info("Send a message to view the profile state for the turn.")
        return

    st.markdown(f"**Version:** {state.profile.version}")
    st.code(json.dumps(state.profile.data, indent=2), language="json")
