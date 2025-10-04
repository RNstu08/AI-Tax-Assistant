import json
from datetime import datetime

import streamlit as st

from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action
from app.orchestrator.models import TurnState, UIAction


def render_actions_panel(state: TurnState | None) -> None:
    st.subheader("💡 Actions")
    # — General Explanation to Users (shows always, above all) —
    st.markdown(
        """
            <p style='color:#808080; font-size:14px; font-style:italic;'>
            - This is where the assistant proposes actions based on your last message.  <br>
            - ✅ Confirm saves changes to your Profile for use in summaries/export. <br>
            - ⏪ Undo rolls back your last edit. You can always continue chatting!
            </p>
        """,
        unsafe_allow_html=True,
    )

    if "dismissed_actions" not in st.session_state:
        st.session_state["dismissed_actions"] = set()

    # — Show a badge if undo just completed —
    if st.session_state.get("undo_success"):
        st.success(
            "Last edit has been successfully undone! Profile and Summary tabs show previous values."
        )
        st.info(
            "- 👈 You can review your reverted deductions in the Profile tab, "
            "and see the change in the Audit Trail.\n"
            "- If you want to make more changes, return to the Chat tab and ask another question!"
        )
        st.session_state["undo_success"] = False  # Reset for next time

    # — Committed message if relevant —
    if (
        state
        and getattr(state, "committed_action", None)
        and getattr(state.committed_action, "committed", False)
    ):
        st.success(
            f"Profile updated to version {state.profile.version}! ✅ "
            "See updated details in the 'Profile' and 'Summary' tabs. "
            "You may keep chatting or undo."
        )
        return

    # — If there are no actions to show, tell the user what to do next —
    if not (state and state.proposed_actions):
        st.info(
            "- Ask another question in the Chat tab to generate new suggestions.\n"
            "- Actions appear here only after Tax AI has all the facts needed "
            "to calculate your deduction."
        )
        return

    # — Show each action in a clear, friendly expander —
    for p in state.proposed_actions:
        if p.action_id in st.session_state["dismissed_actions"]:
            continue  # Don't show dismissed actions
        # Action time and version (for trust)
        when = datetime.now().strftime("%Y-%m-%d %H:%M")
        rationale = p.rationale or "(No rationale from assistant)"
        with st.expander(
            f"➡️ Action: `{p.kind}` ({when}, ver. {getattr(state.profile, 'version', '?')})"
        ):
            st.markdown(f"**Why:** {rationale}")
            st.code(json.dumps(p.payload, indent=2), language="json")
            st.caption(
                f":clipboard: *This was proposed on {when}, calculated using the current profile"
                "version {getattr(state.profile, 'version', '?')}*"
            )
            if p.requires_confirmation:
                # Highlight next step!
                st.info(
                    "⬇️ Click **Confirm** to save this change, or just keep chatting if "
                    "you’re not sure yet."
                )
                cols = st.columns(2)
                if cols[0].button("✅ Confirm", key=f"confirm_{p.action_id}"):
                    action = UIAction(kind="confirm", ref_action=p.action_id)
                    store = ProfileStore()
                    new_state = apply_ui_action(
                        state.user_id, action, st.session_state["last_result"], store
                    )
                    st.session_state["last_result"] = new_state
                    st.success(
                        "Profile updated! You may continue chatting or Undo this change above."
                    )
                    st.rerun()
                if cols[1].button("❌ Dismiss", key=f"dismiss_{p.action_id}"):
                    st.session_state["dismissed_actions"].add(p.action_id)
                    st.success(
                        "- Action dismissed. No changes were saved."
                        "- You can keep chatting or generate a new action by asking a new question."
                    )
                    st.rerun()
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        Ask another question in Chat any time – or use Undo above to roll back the last change.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        💡 What next?<br>
        Go to the Chat tab to try a new question or deduction.
        </p>
        """,
        unsafe_allow_html=True,
    )
