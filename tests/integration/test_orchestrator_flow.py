from app.knowledge.ingest import build_index
from app.orchestrator.graph import run_turn


def setup_module(module):
    """Ensure the rules index exists before running tests."""
    build_index()


def test_happy_path_commute_2025():
    result = run_turn(user_id="u1", user_text="I commute 30 km.", filing_year_override=2025)

    assert not result.errors
    assert "de_2025_commuting_allowance" in result.answer_revised
    assert result.trace.rules_used[0]["year"] == 2025
    assert any(p.kind == "compute_estimate" for p in result.proposed_actions)
    assert "critic" in result.trace.nodes_run


def test_off_scope_freelancer():
    result = run_turn(user_id="u2", user_text="I'm a freelancer.")
    assert any(e.code == "out_of_scope" for e in result.errors)
