import base64
from pathlib import Path

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment

# A valid, 1x1 transparent PNG image represented as bytes.
TINY_PNG_BYTES = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def test_mock_ocr_flow(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    uid = "ocr_user"

    # First, simulate the user giving consent in their profile settings.
    consent_patch = {"preferences": {"consent": {"ocr": True}}}
    store.apply_patch(uid, consent_patch)

    # Now, the rest of the test can proceed as before.
    meta = store.add_attachment(uid, "mock.png", "image/png", TINY_PNG_BYTES, "equipment", "t1")

    # This call will now succeed because consent has been granted.
    parsed = run_ocr_on_attachment(store, meta["id"])

    assert parsed is not None
    # FIX: The test should accept a result from either the mock or real engine.
    assert parsed["engine"] in ["mock", "tesseract"]
    # We also make the final check more robust.
    assert "items" in parsed["parsed_data"]
