from __future__ import annotations

from hashlib import sha256

from app.memory.store import ProfileStore


def run_integrity_scan(store: ProfileStore, user_id: str) -> dict:
    """
    Performs an integrity scan for a user's data.
    1. Verifies all evidence payload hashes.
    2. Verifies all attachment file hashes.
    """
    report = {"user_id": user_id, "issues": []}

    # 1. Verify evidence hashes
    all_evidence = store.get_all_evidence_for_scan(user_id)
    for ev in all_evidence:
        if not ev["payload"] or not ev["payload_hash"]:
            continue

        expected_hash = sha256(ev["payload"].encode()).hexdigest()
        if ev["payload_hash"] != expected_hash:
            report["issues"].append(
                {"type": "evidence_hash_mismatch", "id": ev["id"], "kind": ev["kind"]}
            )

    # 2. Verify attachment file hashes
    all_attachments = store.list_attachments(user_id)
    for attachment in all_attachments:
        try:
            with open(attachment["path"], "rb") as f:
                data = f.read()

            actual_hash = sha256(data).hexdigest()
            if attachment["sha256"] != actual_hash:
                report["issues"].append(
                    {
                        "type": "attachment_hash_mismatch",
                        "id": attachment["id"],
                        "filename": attachment["filename"],
                    }
                )
        except FileNotFoundError:
            report["issues"].append(
                {
                    "type": "attachment_file_missing",
                    "id": attachment["id"],
                    "filename": attachment["filename"],
                }
            )

    return report
