from __future__ import annotations

import json

import streamlit as st

from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_actions_panel(state: TurnState | None) -> None:
    """Renders the panel for proposed actions with confirm/decline buttons."""
    st.subheader("Actions")
    if not (state and state.proposed_actions):
        st.info(
            "Action committed, or no new actions proposed. "
            "See the 'Profile' and 'Audit' tabs for history."
        )
        return

    if "last_result" not in st.session_state:
        st.session_state["last_result"] = state

    for p in state.proposed_actions:
        with st.expander(f"Action: `{p.kind}`"):
            st.caption(f"Rationale: {p.rationale}")
            st.code(json.dumps(p.payload, indent=2), language="json")
            if p.requires_confirmation:
                cols = st.columns(2)
                if cols[0].button("Confirm", key=f"confirm_{p.action_id}"):
                    action = UIAction(kind="confirm", ref_action=p.action_id)
                    store = ProfileStore()
                    new_state = apply_ui_action(
                        "demo", action, st.session_state["last_result"], store
                    )
                    st.session_state["last_result"] = new_state
                    st.success(f"Profile updated to version {new_state.profile.version}! ✅")
                    st.info(
                        "View the changes in the 'Profile' tab and the record of this "
                        "action in the 'Audit' tab."
                    )
                    st.rerun()
