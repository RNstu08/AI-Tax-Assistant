from app.knowledge.ingest import build_index
from app.orchestrator.graph import run_turn


def setup_module(module):
    build_index()


def test_e2e_commute_and_ho_produces_amounts():
    text = "I commute 30 km for 220 days, but was in home office for 100 days in 2025."
    result = run_turn(user_id="u_numeric1", user_text=text, filing_year_override=2025)

    assert "€1,176.00" in result.answer_revised  # Commute
    assert "€600.00" in result.answer_revised  # Home Office
    assert "amounts_backed_by_calculators" in result.critic_flags


def test_e2e_equipment_produces_amount():
    text = "I bought a new work laptop for 899€ in 2024"
    result = run_turn(user_id="u_numeric2", user_text=text, filing_year_override=2024)

    assert "€899.00" in result.answer_revised
    assert any("equipment_item" in key for key in result.calc_results)
