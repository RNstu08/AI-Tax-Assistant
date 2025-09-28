import uuid
from pathlib import Path

from app.memory.store import ProfileStore


def test_store_create_patch_undo(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    user_id = f"test_user_{uuid.uuid4().hex}"
    snap1 = store.get_profile(user_id)
    assert snap1.version == 0
    patch1 = {"filing": {"filing_year": 2025}}
    snap2, diff1 = store.apply_patch(user_id, patch1)
    assert snap2.version == 1
    action_id = f"action_{uuid.uuid4().hex}"
    store.commit_action(user_id, action_id, "set_filing_year", patch1, "hash1", diff1, True)
    snap3 = store.undo_action(user_id, f"undo:{action_id}")
    assert snap3.version == 2
    assert "filing" not in snap3.data or "filing_year" not in snap3.data.get("filing", {})
