from __future__ import annotations

import streamlit as st

from app.orchestrator.models import TurnState


def render_trace_panel(state: TurnState | None) -> None:
    st.subheader("Decision Trace")
    if not state:
        st.info("Send a message in the Chat tab to populate the trace.")
        return

    t = state.trace
    st.markdown("**Nodes Run**")
    st.code("\n".join(t.nodes_run) or "(none)")
    st.markdown("**Rules Used**")
    st.code("\n".join([f"{r['rule_id']} ({r['year']})" for r in t.rules_used]) or "(none)")
    st.markdown("**Critic Flags**")
    st.code("\n".join(t.critic_flags) or "(none)")
