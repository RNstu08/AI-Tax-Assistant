from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from app.orchestrator.models import TurnState


def render_profile_panel(state: TurnState | None) -> None:
    st.subheader("📖 Profile – Your Tax Data")
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        - This tab shows your current saved deductions and settings. <br>
        - Confirmed actions (from the Actions tab) update your profile instantly. <br>
        - Use Undo to revert the last change and see it reflected here.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not state:
        st.info("Send a message in the Chat tab to build your profile step by step.")
        return

    # Plain-language summary of key fields
    profile_data = state.profile.data
    deductions = profile_data.get("deductions", {})
    summary = []
    if "commute_km_per_day" in deductions:
        summary.append(f"* Daily commute: **{deductions['commute_km_per_day']} km**")
    if "work_days_per_year" in deductions:
        summary.append(f"* Work days this year: **{deductions['work_days_per_year']}**")
    if "home_office_days" in deductions:
        summary.append(f"* Home office days: **{deductions['home_office_days']}**")
    if "equipment_items" in deductions:
        count = len(deductions["equipment_items"])
        summary.append(f"* Work equipment items: **{count}**")
    if not summary:
        summary.append("You haven’t saved any deductions yet.")

    st.markdown("### 🔍 At a Glance")
    st.success("\n".join(summary))

    # Version badge
    version_html = (
        f'<span style="font-weight:600; margin-right:0.5em;">'
        f"Version {state.profile.version}</span>"
    )
    updated_html = (
        f'<span style="color:#5A789A;">Updated: '
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>"
    )
    st.markdown(f"...{version_html}{updated_html}...", unsafe_allow_html=True)

    # Show recent diffs
    diffs = state.profile_diff or []
    if diffs:
        st.markdown("### 🟡 Recent Change")
        for d in diffs:
            st.markdown(
                f"- **{d.path}**: "
                f"<span style='color:red;'>{d.old}</span> → "
                f"<span style='color:green;'>{d.new}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No recent edits. Make a change in the Chat tab to see updates here.")

    # Raw JSON for power users
    if st.checkbox("Show raw profile data (JSON)", value=False):
        st.code(json.dumps(state.profile.data, indent=2), language="json")

    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        💡 Next: Use the Audit tab to see a full timeline of every action—
        or return to Chat to adjust or add deductions!
        </p>
        """,
        unsafe_allow_html=True,
    )
