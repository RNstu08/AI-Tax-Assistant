from __future__ import annotations

import time
from typing import Any

from app.memory.store import ProfileStore


def run_retention_cleanup(store: ProfileStore, apply: bool = False) -> dict:
    summary: dict[str, Any] = {"applied": apply, "users": {}}
    now_ms = int(time.time() * 1000)
    day_ms = 86400 * 1000

    for user_id in store.get_all_user_ids():
        profile = store.get_profile(user_id)
        retention_days = profile.data.get("preferences", {}).get("retention", {})
        user_summary: dict[str, Any] = {}

        if days := retention_days.get("attachments_days"):
            if int(days) > 0:
                cutoff = now_ms - (int(days) * day_ms)
                if apply:
                    count = store.delete_attachments_older_than(user_id, cutoff)
                    if count > 0:
                        user_summary["deleted_attachments"] = count
                else:
                    count = len(store.list_attachments_older_than(user_id, cutoff))
                    if count > 0:
                        user_summary["attachments_to_delete"] = count

        if days := retention_days.get("evidence_days"):
            if int(days) > 0:
                cutoff = now_ms - (int(days) * day_ms)
                if apply:
                    count = store.delete_evidence_older_than(user_id, cutoff)
                    if count > 0:
                        user_summary["deleted_evidence"] = count
                else:
                    count = len(store.list_evidence_older_than(user_id, cutoff))
                    if count > 0:
                        user_summary["evidence_to_delete"] = count

        if user_summary:
            summary["users"][user_id] = user_summary

    if apply and summary["users"]:
        store.log_evidence("system", None, "retention_cleanup", {}, summary)

    return summary
