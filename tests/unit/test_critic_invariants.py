from app.orchestrator.graph import run_turn


def test_critic_adds_disclaimer():
    result = run_turn(user_id="u3", user_text="hello")
    # FIX: Make the check case-insensitive to be more robust
    assert "not tax advice" in result.answer_revised.lower()
