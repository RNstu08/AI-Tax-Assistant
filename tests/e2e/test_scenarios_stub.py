from pathlib import Path

from app.knowledge.ingest import build_index
from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn
from tests.util.golden import assert_expectations, load_scenarios


def setup_module(module):
    build_index()


def test_golden_scenarios(tmp_path: Path):
    scenarios = load_scenarios(Path("tests/golden"))
    assert scenarios, "No golden scenarios found"
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    for scenario in scenarios:
        for turn in scenario["turns"]:
            result = run_turn(
                user_id=scenario["id"],
                user_text=turn["user"],
                store=store,
                filing_year_override=turn.get("filing_year"),
            )
            assert_expectations(result, turn["expect"])
