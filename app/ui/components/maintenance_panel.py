from __future__ import annotations

import streamlit as st

from app.maintenance.integrity_scan import run_integrity_scan  # Add import
from app.memory.store import ProfileStore


def render_maintenance_panel(state) -> None:
    st.subheader("Maintenance")
    if not state:
        st.info("Start a chat to use maintenance tools.")
        return
    store = ProfileStore()

    st.markdown("**Data Retention**")
    # ... (retention UI is unchanged) ...

    st.markdown("---")
    st.markdown("**Data Integrity**")
    if st.button("Run Integrity Scan"):
        with st.spinner("Scanning data for inconsistencies..."):
            result = run_integrity_scan(store, state.user_id)
        if not result["issues"]:
            st.success("✅ Integrity scan complete. No issues found.")
        else:
            st.error(f"🚨 Integrity scan found {len(result['issues'])} issue(s).")
            st.json(result)
