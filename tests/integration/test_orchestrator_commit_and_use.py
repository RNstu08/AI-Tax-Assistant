import uuid
from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import apply_ui_action, run_turn
from app.orchestrator.models import UIAction


def setup_module(module):
    build_index()


def test_commit_and_reuse_memory(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    user_id = f"commit_test_{uuid.uuid4().hex}"
    state1 = run_turn(
        user_id=user_id, user_text="My commute is 30 km for 220 days in 2025.", store=store
    )
    confirm_action = next(
        (p for p in state1.proposed_actions if p.kind == "confirm_profile_patch"), None
    )
    assert confirm_action is not None
    state2 = apply_ui_action(
        user_id, UIAction(kind="confirm", ref_action=confirm_action.action_id), state1, store
    )
    assert state2.profile.version > state1.profile.version
    state3 = run_turn(user_id=user_id, user_text="What is my commute estimate?", store=store)
    assert state3.profile.version == state2.profile.version
    assert "€2,156.00" in state3.answer_revised
