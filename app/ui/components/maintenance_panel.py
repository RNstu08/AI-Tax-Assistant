from __future__ import annotations

import streamlit as st

from app.maintenance.retention import run_retention_cleanup
from app.memory.store import ProfileStore


def render_maintenance_panel(state) -> None:
    st.subheader("Maintenance")
    store = ProfileStore()

    st.markdown("**Data Retention**")
    apply_changes = st.checkbox("Apply deletions (otherwise, this is a dry run)")
    if st.button("Run Retention Cleanup"):
        with st.spinner("Running cleanup..."):
            result = run_retention_cleanup(store, apply=apply_changes)
        st.success("Cleanup process finished.")
        st.json(result)
