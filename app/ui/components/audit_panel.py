from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from app.memory.store import ProfileStore
from app.orchestrator.models import TurnState

# === Mappings for prettification ===
FIELD_LABELS = {
    "work_days_per_year": "Work days per year",
    "commute_km_per_day": "Commute distance (km)",
    "home_office_days": "Home office days",
    "equipment_items": "Work equipment",
    "deductions": "Deductions",
    "filing.filing_year": "Tax year",
    "donations": "Charitable donations",
    "profile_version": "Profile version",
    # Add as needed!
}
ACTION_LABELS = {
    "confirm_profile_patch": "Profile update",
    "compute_estimate": "Estimate calculation",
    "import_parsed_items": "Imported item(s)",
    "set_preferences": "Settings changed",
    "undo": "Undo",
    # add others...
}
EVIDENCE_LABELS = {
    "receipt_upload": "Uploaded receipt/document",
    "ocr_run": "OCR extraction",
    "retention_cleanup": "Data retention cleanup",
    # add others...
}


def prettify_field(field):
    field_key = field.rsplit(".", 1)[-1]
    return FIELD_LABELS.get(
        field, FIELD_LABELS.get(field_key, field_key.replace("_", " ").capitalize())
    )


def prettify_action(kind):
    return ACTION_LABELS.get(kind, kind.replace("_", " ").capitalize())


def prettify_evidence(kind):
    return EVIDENCE_LABELS.get(kind, kind.replace("_", " ").capitalize())


def format_diff(diff_json):
    try:
        diffs = json.loads(diff_json)
    except Exception:
        return "-"
    if not diffs:
        return "No direct change"
    lines = []
    for d in diffs[:2]:
        field = d.get("path", "")
        pretty = prettify_field(field)
        old = d.get("old", "")
        new = d.get("new", "")
        old = "-" if old in (None, "None") else old
        new = "-" if new in (None, "None") else new
        line = f"{pretty}: {old} → {new}"
        lines.append(line)
    if len(diffs) > 2:
        lines.append(f"...(+{len(diffs)-2} more)")
    return "; ".join(lines)


def render_audit_panel(state: TurnState | None) -> None:
    st.subheader("📑 Audit Trail")
    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        - This tab shows every action and event (uploads, imports, undos, settings changes). <br>
        - Use it to track who did what, when, and why.<br>
        - See full technical/log fields or only what matters to you. <br>
        - Perfect for compliance, support, or your own peace of mind.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # The Audit Trail is only available after a chat has started
    if not state:
        st.info("Start a chat to view the audit trail.")
        return

    store = ProfileStore()
    user_id = state.user_id

    st.markdown("### 🔄 Recent State Changes (Profile Actions)")
    actions = store.list_actions(user_id)
    if not actions:
        st.info("No state-changing actions have been committed yet.")
    else:
        # 1. Compose a prettified summary table
        pretty_rows = []
        for act in actions:
            dt = datetime.fromtimestamp(act["created_at"] / 1000).strftime("%Y-%m-%d %H:%M")
            kind = prettify_action(act.get("kind", "action"))
            diffstr = format_diff(act.get("diff", "[]")) if act.get("diff") else "See Fields"
            version = act.get("version_after", "-")
            try:
                payload = json.loads(act["payload"])
            except json.JSONDecodeError:
                payload = {}
            edited = []
            if "deductions" in payload:
                edited = [prettify_field(x) for x in payload["deductions"].keys()]
            elif "filing" in payload:
                edited = ["Tax Year"]
            elif "preferences" in payload:
                edited = ["Preferences"]
            else:
                edited = list(payload.keys())
            primary = ", ".join(edited) if edited else "-"
            pretty_rows.append(
                {
                    "Type": kind,
                    "When": dt,
                    "Profile ver.": version,
                    "What changed": diffstr,
                    "Fields": primary,
                    "Raw ID": act.get("id", "-"),  # Show raw ids for audit/power use
                }
            )

        deletes = [
            ev
            for ev in store.list_evidence(user_id)
            if "delete" in ev.get("kind", "") or "retention" in ev.get("kind", "")
        ]
        if deletes:
            st.markdown("### 🗑️ Data Deletion Log")
            for d in deletes:
                dt = datetime.fromtimestamp(d["created_at"] / 1000).strftime("%Y-%m-%d %H:%M")
                st.write(f"- {dt}: {d.get('kind')} — {d.get('result', '')}")
        else:
            st.info("No deletion events found.")

        st.markdown("**Summary view (readable for non-technical users):**")
        st.table(pd.DataFrame(pretty_rows))

        with st.expander(
            "See all raw data as a table (sortable/filterable, for power users)", expanded=False
        ):
            st.dataframe(pd.DataFrame(actions))

        for i, act in enumerate(actions):
            with st.expander(
                f"Show full details for {pretty_rows[i]['Type']} at {pretty_rows[i]['When']}",
                expanded=False,
            ):
                st.markdown("**Payload:**")
                try:
                    st.json(json.loads(act["payload"]))
                except Exception:
                    st.write(act["payload"])
                if act.get("diff"):
                    st.markdown("**Changes (diff):**")
                    try:
                        st.json(json.loads(act["diff"]))
                    except Exception:
                        st.write(act["diff"])

    st.markdown("---")
    st.markdown("### 📂 Recent Evidence Events (Read-Only)")
    evidence = store.list_evidence(user_id)
    if not evidence:
        st.info("No evidence events have been logged yet.")
    else:
        pretty_ev_rows = []
        for ev in evidence:
            dt = datetime.fromtimestamp(ev["created_at"] / 1000).strftime("%Y-%m-%d %H:%M")
            kind = prettify_evidence(ev.get("kind", "event"))
            try:
                payload = json.loads(ev["payload"]) if ev.get("payload") else {}
            except Exception:
                payload = {}
            try:
                result = json.loads(ev["result"]) if ev.get("result") else {}
            except Exception:
                result = {}
            file_info = payload.get("filename") or payload.get("attachment_id") or "-"
            # Compose result/summary
            if "parse_id" in result and "items_found" in result:
                result_info = f"OCR: {result['items_found']} items found"
            elif "reason" in result:
                result_info = result["reason"]
            elif "deleted_attachments" in result:
                result_info = f"Deleted {result['deleted_attachments']} attachments"
            elif isinstance(result, dict) and result:
                k, v = next(iter(result.items()))
                result_info = f"{k}: {v}"
            else:
                result_info = "-"
            pretty_ev_rows.append(
                {
                    "Event": kind,
                    "When": dt,
                    "File/Info": file_info,
                    "Result": result_info,
                    "Raw ID": ev.get("id", "-"),
                }
            )

        st.markdown("**Summary view (readable for non-technical users):**")
        st.table(pd.DataFrame(pretty_ev_rows))

        with st.expander(
            "See all raw evidence as a table (sortable/filterable, for power users)", expanded=False
        ):
            st.dataframe(pd.DataFrame(evidence))

        for i, ev in enumerate(evidence):
            with st.expander(
                f"Show full details for {pretty_ev_rows[i]['Event']}"
                "at {pretty_ev_rows[i]['When']}",
                expanded=False,
            ):
                st.markdown("**Payload:**")
                try:
                    st.json(json.loads(ev["payload"]))
                except Exception:
                    st.write(ev["payload"])
                st.markdown("**Result:**")
                try:
                    st.json(json.loads(ev["result"]))
                except Exception:
                    st.write(ev["result"])

    st.markdown(
        """
        <p style='color:#808080; font-size:14px; font-style:italic;'>
        * You can view both easy-to-read summaries and all technical details.<br>
        * Use sortable/filterable tables to investigate further.<br>
        * Click "Show full details" for raw data, if needed for compliance/support.<br>
        </p>
        """,
        unsafe_allow_html=True,
    )
