from __future__ import annotations

import streamlit as st

from app.i18n.microcopy import t
from app.knowledge.rules_service import RulesService


def render_rules_panel(state) -> None:
    lang = state.profile.data.get("preferences", {}).get("language", "en") if state else "en"
    st.subheader(t(lang, "rules_browser_title"))
    svc = RulesService()

    query = st.text_input(t(lang, "search_rules"))
    year = st.selectbox(t(lang, "year_filter"), options=[None, 2024, 2025], index=0)

    rules = svc.search(query=query, year=year)
    for rule in rules:
        with st.expander(f"{rule.get('title', 'N/A')} ({rule.get('year')})"):
            st.markdown(f"**ID:** `{rule.get('rule_id')}`")
            st.markdown(f"**Category:** `{rule.get('category')}`")
            st.caption(rule.get("summary"))
