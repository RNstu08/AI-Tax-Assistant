# tests/integration/test_attachments.py
import uuid
from pathlib import Path

from app.memory.store import ProfileStore


def test_add_and_list_attachment(tmp_path: Path):
    store = ProfileStore(
        sqlite_path=str(tmp_path / "test.db"), upload_dir=str(tmp_path / "uploads")
    )
    user_id = f"user_{uuid.uuid4().hex}"
    meta = store.add_attachment(
        user_id, "receipt.pdf", "application/pdf", b"dummydata", "equipment", "turn1"
    )
    assert meta["id"] > 0
    assert Path(meta["path"]).exists()
    attachments = store.list_attachments(user_id)
    assert len(attachments) == 1 and attachments[0]["id"] == meta["id"]
