import streamlit as st


def render_trace_panel(state):
    st.subheader("Decision Trace")
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        - Each time you send a message in the Chat, AI follows a step-by-step process.  <br>
        - These steps ensure that your deductions are checked, calculated, and explained. <br>
        - Here's how your last request was handled:
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not state:
        st.info(
            "Send a message in the Chat tab to see how the assistant reasons through your question!"
        )
        return

    STEPS = [
        ("Safety gate", "Checks if your question is supported."),
        ("Router", "Understands your topic."),
        ("Extractor", "Finds facts (like distance, amounts, dates)."),
        ("Knowledge agent", "Looks up tax rules."),
        ("Question generator", "Asks for missing information, if needed."),
        ("Calculators", "Does the math."),
        ("Reasoner", "Writes the answer."),
        ("Critic", "Double-checks the results."),
        ("Action planner", "Suggests what to do next."),
        ("Trace emitter", "Records all steps above."),
    ]
    nodes_run = set(state.trace.nodes_run)
    # Find what field was last missing, if any clarifying question was asked
    last_missing = None
    questions = getattr(state, "questions", [])
    if questions and hasattr(questions[-1], "field_key"):
        last_missing = questions[-1].field_key
    # -----------------------------------
    st.markdown("### How your last question was processed:")
    for node, desc in STEPS:
        emoji = "🟢" if node.replace(" ", "_").lower() in nodes_run else "⚪️"
        st.markdown(f"{emoji} **{node}**: {desc}")
        if node == "Question generator" and last_missing:
            st.markdown(f"↪️ **Asked for missing info:** `{last_missing.replace('_',' ')}`")

    st.markdown("### Rules Used")
    if state.trace.rules_used:
        for rule in state.trace.rules_used:
            st.write(f"- **{rule['rule_id']}** (Year: {rule['year']})")
    else:
        st.warning(
            ":grey_exclamation: No rules were matched for this question."
            " Try being more specific (year, amount, category)."
        )

    st.markdown("### Additional Checks")
    if state.trace.critic_flags:
        st.warning("Tax AI found something worth double-checking:")
        for flag in state.trace.critic_flags:
            st.write(f"- {flag}")
    else:
        st.success("All calculations checked and grounded in tax rules.")

    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        Visit Audit or Profile for full details of your saved info and history.
        </p>
        """,
        unsafe_allow_html=True,
    )
