from __future__ import annotations

import streamlit as st

from app.memory.store import ProfileStore
from app.orchestrator.models import TurnState


def render_audit_panel(state: TurnState | None) -> None:
    st.subheader("Audit Trail")
    if not state:
        st.info("Start a chat to view the audit trail.")
        return

    store = ProfileStore()
    st.markdown("**Recent Actions (State Changes)**")
    actions = store.list_actions(state.user_id)
    st.dataframe(actions)

    st.markdown("**Recent Evidence (Read-Only Events)**")
    evidence = store.list_evidence(state.user_id)
    st.dataframe(evidence)
