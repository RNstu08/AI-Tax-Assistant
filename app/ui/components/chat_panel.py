from __future__ import annotations

import streamlit as st

from app.orchestrator.graph import run_turn


def render_chat_panel() -> None:
    """Renders the chat input and streams the assistant's response."""
    st.subheader("Chat")

    # Use a form to handle user input
    with st.form("chat_form", clear_on_submit=True):
        # FIX: Break long default value string to satisfy line-length limit
        default_prompt = "I commute 30 km and worked from home 100 days in 2025."
        user_text = st.text_area(
            "Your message:",
            value=st.session_state.get("last_input", default_prompt),
            height=100,
            help="Ask about your deductions (DE employee, 2024–2025).",
        )
        submitted = st.form_submit_button("Send")

    if submitted and user_text:
        st.session_state["last_input"] = user_text
        filing_year = st.session_state.get("filing_year_override")

        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            result = run_turn(user_id="demo", user_text=user_text, filing_year_override=filing_year)
            st.session_state["last_result"] = result
            placeholder.markdown(result.answer_revised)
