from pathlib import Path

from app.knowledge.ingest import build_index
from app.orchestrator.graph import run_turn
from tests.util.golden import assert_expectations, load_scenarios


def setup_module(module):
    """Ensure the rules index exists before running e2e tests."""
    build_index()


def test_golden_scenarios():
    scenarios = load_scenarios(Path("tests/golden"))
    assert scenarios, "No golden scenarios found"

    for scenario in scenarios:
        for turn in scenario["turns"]:
            result = run_turn(
                user_id=scenario["id"],
                user_text=turn["user"],
                filing_year_override=turn["filing_year"],
            )
            assert_expectations(result, turn["expect"])
