from decimal import Decimal
from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn


def setup_module(module):
    build_index()


def test_multi_item_extraction_leads_to_calculation(tmp_path: Path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    text = "I bought 2x Laptop for 900€ each in 2024"
    result = run_turn(user_id="nlu_user", user_text=text, store=store)

    assert "equipment_total" in result.calc_results
    # FIX: The correct total is 1800.00 (2 * 900)
    assert result.calc_results["equipment_total"]["amount_eur"] == Decimal("1800.00")
