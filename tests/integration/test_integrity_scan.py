import uuid
from pathlib import Path

from app.maintenance.integrity_scan import run_integrity_scan
from app.memory.store import ProfileStore


def test_integrity_scan_clean(tmp_path: Path):
    """Tests that a clean, untouched database passes the scan."""
    store = ProfileStore(
        sqlite_path=str(tmp_path / "test.db"), upload_dir=str(tmp_path / "uploads")
    )
    user_id = f"user_{uuid.uuid4().hex}"

    # Log some events and add a file
    store.log_evidence(user_id, "turn1", "test_event", {"data": "A"}, {"ok": True})
    store.add_attachment(user_id, "receipt.txt", "text/plain", b"file content", "general", "turn1")

    report = run_integrity_scan(store, user_id)
    assert not report["issues"]


def test_integrity_scan_tampered_file(tmp_path: Path):
    """Tests that the scan detects a file that has been modified on disk."""
    store = ProfileStore(
        sqlite_path=str(tmp_path / "test.db"), upload_dir=str(tmp_path / "uploads")
    )
    user_id = f"user_{uuid.uuid4().hex}"

    meta = store.add_attachment(
        user_id, "receipt.txt", "text/plain", b"original content", "general", "turn1"
    )

    # Tamper with the file on disk after it has been saved
    with open(meta["path"], "wb") as f:
        f.write(b"tampered content")

    report = run_integrity_scan(store, user_id)
    assert len(report["issues"]) == 1
    assert report["issues"][0]["type"] == "attachment_hash_mismatch"
