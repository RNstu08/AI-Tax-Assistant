import base64
import uuid
from decimal import Decimal
from pathlib import Path

from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action, run_turn
from app.orchestrator.models import UIAction
from app.receipts.parser import ParsedItem, ParsedReceipt
from tools.money import D

TINY_PNG_BYTES = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def test_full_ocr_import_flow(tmp_path: Path):
    """
    Tests the full end-to-end flow of importing a parsed receipt item.
    """
    store = ProfileStore(
        sqlite_path=str(tmp_path / "test.db"), upload_dir=str(tmp_path / "uploads")
    )
    user_id = f"ocr_import_user_{uuid.uuid4().hex}"

    # 1. Setup: User gives consent and has an initial turn state
    store.apply_patch(user_id, {"preferences": {"consent": {"ocr": True}}})
    state1 = run_turn(user_id=user_id, user_text="Hello", store=store)
    attachment_meta = store.add_attachment(
        user_id, "mock.png", "image/png", TINY_PNG_BYTES, "equipment", state1.correlation_id
    )

    # 2. Manually create and save a mock parse result to the DB
    mock_parsed_receipt = ParsedReceipt(
        vendor="Mock Store",
        purchase_date="2025-01-15",
        items=[
            ParsedItem(
                description="Laptop",
                quantity=1,
                unit_price_eur=D("950.00"),
                total_eur=D("950.00"),
            )
        ],
        total_eur=D("950.00"),
    )
    store.save_receipt_parse(
        user_id, attachment_meta["id"], "mock text", mock_parsed_receipt, "mock-test"
    )

    # 3. Simulate the user selecting the first item and importing
    payload = {"attachment_id": attachment_meta["id"], "item_indices": [0]}
    action = UIAction(kind="import_parsed_items", payload=payload)
    state2 = apply_ui_action(user_id, action, state1, store)

    # Verify the profile was updated
    assert state2.profile.version > state1.profile.version

    # 4. Run a new turn and verify the calculator uses the imported item
    state3 = run_turn(user_id=user_id, user_text="what is my equipment deduction?", store=store)
    assert "equipment_total" in state3.calc_results
    assert state3.calc_results["equipment_total"]["amount_eur"] == Decimal("950.00")
