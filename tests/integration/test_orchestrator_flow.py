from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn


def setup_module(module):
    build_index()


def test_happy_path_commute_2025(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    result = run_turn(
        user_id="u1", user_text="I commute 30 km.", store=store, filing_year_override=2025
    )
    assert not result.errors
    assert any(p.kind == "compute_estimate" for p in result.proposed_actions)
    assert any(p.kind == "confirm_profile_patch" for p in result.proposed_actions)


def test_off_scope_freelancer(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    result = run_turn(user_id="u2", user_text="I'm a freelancer.", store=store)
    assert any(e.code == "out_of_scope" for e in result.errors)
