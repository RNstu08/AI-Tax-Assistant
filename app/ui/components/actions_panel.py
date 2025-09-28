from __future__ import annotations

import json

import streamlit as st

from app.orchestrator.models import TurnState


def render_actions_panel(state: TurnState | None) -> None:
    st.subheader("Actions")
    if not (state and state.proposed_actions):
        st.info("Send a message in the Chat tab to see proposed actions.")
        return

    for p in state.proposed_actions:
        with st.expander(f"Action: `{p.kind}`"):
            st.caption(f"Rationale: {p.rationale}")
            st.code(json.dumps(p.payload, indent=2), language="json")
            if p.requires_confirmation:
                cols = st.columns(2)
                if cols[0].button("Confirm", key=f"confirm_{p.action_id}"):
                    st.success(f"Confirmed action '{p.kind}' (simulation).")
                if cols[1].button("Decline", key=f"decline_{p.action_id}"):
                    st.warning(f"Declined action '{p.kind}' (simulation).")
