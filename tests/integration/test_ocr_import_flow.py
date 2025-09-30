from decimal import Decimal
from pathlib import Path

from app.memory.store import ProfileStore
from app.ocr.runner import run_ocr_on_attachment
from app.orchestrator.graph import apply_ui_action, run_turn
from app.orchestrator.models import UIAction


def test_full_ocr_import_flow(tmp_path: Path):
    """
    Tests the full end-to-end flow:
    1. Upload a file.
    2. Run mock OCR.
    3. Simulate user selecting items and importing them.
    4. Run a new turn and verify the imported items are used in the calculation.
    """
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    user_id = "ocr_import_user"

    # 1. Initial state and upload
    state1 = run_turn(user_id=user_id, user_text="Hello", store=store)
    attachment_meta = store.add_attachment(
        user_id, "mock.png", "image/png", b"dummy", "equipment", state1.correlation_id
    )

    # 2. Run OCR
    parsed = run_ocr_on_attachment(store, attachment_meta["id"])
    assert parsed is not None

    # 3. Simulate user selecting the first item and importing
    payload = {"attachment_id": attachment_meta["id"], "item_indices": [0]}
    action = UIAction(kind="import_parsed_items", payload=payload)
    state2 = apply_ui_action(user_id, action, state1, store)
    assert state2.profile.version > state1.profile.version

    # 4. Run a new turn and verify the calculator uses the imported item
    state3 = run_turn(user_id=user_id, user_text="what is my equipment deduction?", store=store)
    assert "equipment_total" in state3.calc_results
    assert state3.calc_results["equipment_total"]["amount_eur"] == Decimal(
        "950.00"
    )  # From the mock OCR data
