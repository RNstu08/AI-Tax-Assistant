from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn


def setup_module(module):
    build_index()


def test_e2e_commute_and_ho_produces_amounts(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    text = "I commute 30 km for 220 days, but was in home office for 100 days in 2025."
    result = run_turn(user_id="u_numeric1", user_text=text, store=store, filing_year_override=2025)
    assert "€1,176.00" in result.answer_revised
    assert "€600.00" in result.answer_revised


def test_e2e_equipment_produces_amount(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    text = "I bought a new work laptop for 899€ in 2024"
    result = run_turn(user_id="u_numeric2", user_text=text, store=store, filing_year_override=2024)
    assert "€899.00" in result.answer_revised
