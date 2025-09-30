from __future__ import annotations

import streamlit as st

from app.i18n.microcopy import CopyKey, t
from app.knowledge.rules_service import RulesService
from app.orchestrator.models import TurnState


def render_rules_panel(state: TurnState | None) -> None:
    """Renders a UI for browsing and searching the knowledge base rules."""
    lang = "en"
    if state and state.profile:
        lang = state.profile.data.get("preferences", {}).get("language", "en")

    st.subheader(t(lang, CopyKey.RULES_BROWSER_TITLE))
    svc = RulesService()

    # FIX: Use the correct enum member 'CopyKey.SEARCH_RULES'
    query = st.text_input(t(lang, CopyKey.SEARCH_RULES))
    year = st.selectbox(t(lang, CopyKey.YEAR_FILTER), options=[None, 2024, 2025], index=0)

    rules = svc.search(query=query, year=year)
    for rule in rules:
        with st.expander(f"{rule.get('title', 'N/A')} ({rule.get('year')})"):
            st.markdown(f"**ID:** `{rule.get('rule_id')}`")
            st.markdown(f"**Category:** `{rule.get('category')}`")
            st.caption(rule.get("summary"))
