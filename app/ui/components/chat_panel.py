from __future__ import annotations

import streamlit as st

from app.orchestrator.graph import run_turn_streaming


def render_chat_panel() -> None:
    st.subheader("Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    with st.form("chat_form", clear_on_submit=True):
        user_text = st.text_area(
            "Your message:",
            placeholder="Ask about your deductions, e.g., 'I commute 30km for 220 days.'",
            key="chat_input",  # A key helps Streamlit manage the state of this widget
        )
        submitted = st.form_submit_button("Send")

    if submitted and user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            def on_token(token: str):
                nonlocal full_response
                full_response += token
                placeholder.markdown(full_response + "▌")

            filing_year = st.session_state.get("filing_year_override")
            result = run_turn_streaming(
                user_id="demo",
                user_text=user_text,
                on_token=on_token,
                filing_year_override=filing_year,
            )

            # --- Show clarifying question with blue highlight (if needed) ---
            if result.questions:
                # Show newest question
                question = result.questions[-1]
                display_text = getattr(question, "text", question)
                st.info(f"❓ <b>More info needed:</b> {display_text}")
                # st.info(f"❓ <b>More info needed:</b> {result.questions[-1].text}")
                # st.session_state["last_result"] = result
                # last_q = result.questions[-1]
                # q_text = getattr(last_q, "text", last_q)
                # st.session_state.messages.append(
                #     {"role": "assistant", "content": f"❓ {q_text}"}
                # )
                st.session_state["last_result"] = result
                question = result.questions[-1]
                display_text = getattr(question, "text", question)
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"❓ {display_text}"}
                )
            else:
                # Normal answer
                placeholder.markdown(result.answer_revised)
                st.session_state["last_result"] = result
                st.session_state.messages.append(
                    {"role": "assistant", "content": result.answer_revised}
                )
        st.rerun()

        # --- NEW CODE BLOCK STARTS HERE ---
    # Add a visual separator
    st.divider()

    # Add the "Ask a human" button with conditional logic
    if st.button("❔ Ask a human about this answer"):
        # Check if a conversation has started
        if st.session_state.messages:
            st.info(
                "Your question has been flagged for human review (demo)."
                "Support will contact you soon!"
            )
            # In a real app, you would add the escalation logic here.
        else:
            # If no conversation has started, guide the user.
            st.warning(
                "Please ask a question in the chat box above before requesting a human review."
            )
    # --- NEW CODE BLOCK ENDS HERE ---

    st.caption("Examples: 'I worked from home 150 days in 2024', 'I bought a laptop for 900€'")
