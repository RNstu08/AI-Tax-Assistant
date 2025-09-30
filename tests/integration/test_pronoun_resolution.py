from pathlib import Path

from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn


def test_multi_turn_pronoun_resolution(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    user_id = "pronoun_user"

    # Turn 1: User mentions a specific item.
    # FIX: Assign to '_' to signal that the return value is intentionally unused.
    _ = run_turn(user_id=user_id, user_text="I bought a monitor for 450.50€", store=store)

    # The memory from turn 1 is now saved in the user's profile in the DB.
    # Turn 2: User refers to the item with a pronoun
    state2 = run_turn(user_id=user_id, user_text="I bought another one", store=store)

    # Verify that the extractor in Turn 2 created a patch for a 450.50€ item
    assert state2.patch_proposal is not None
    patch = state2.patch_proposal.patch
    assert patch["deductions"]["equipment_items"][0]["amount_gross_eur"] == "450.50"
