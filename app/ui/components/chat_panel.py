from __future__ import annotations

import streamlit as st

from app.orchestrator.graph import run_turn


def render_chat_panel() -> None:
    """Renders the main chat interface with history and input form."""
    st.subheader("Chat")

    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_area(
            "Your message:",
            placeholder="Ask about your deductions, e.g., 'I commute 30km for 220 days.'",
            key="chat_input",  # Use a key to help Streamlit manage state
        )
        submitted = st.form_submit_button("Send")

    if submitted and user_text:
        # Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                filing_year = st.session_state.get("filing_year_override")
                result = run_turn(
                    user_id="demo", user_text=user_text, filing_year_override=filing_year
                )
                st.session_state["last_result"] = result
                st.markdown(result.answer_revised)
                # Add assistant response to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": result.answer_revised}
                )

        # Rerun to clear the input form correctly after processing
        st.rerun()

    st.caption("Examples: 'I worked from home 150 days in 2024', 'I bought a laptop for 900€'")
