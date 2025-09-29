from app.memory.store import ProfileStore
from app.orchestrator.graph import run_turn


def test_critic_adds_disclaimer(tmp_path):
    store = ProfileStore(sqlite_path=str(tmp_path / "test.db"))
    result = run_turn(user_id="u3", user_text="hello", store=store)
    assert "not tax advice" in result.answer_revised.lower()
