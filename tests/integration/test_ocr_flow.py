# tests/integration/test_ocr_flow.py
from pathlib import Path

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment


def test_mock_ocr_flow(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    uid = "ocr_user"
    meta = store.add_attachment(uid, "mock.png", "image/png", b"dummy", "equipment", "t1")
    parsed = run_ocr_on_attachment(store, meta["id"])
    assert parsed is not None and parsed["engine"] == "mock"
    assert len(parsed["parsed_data"]["items"]) > 0
