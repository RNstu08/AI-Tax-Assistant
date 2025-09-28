from __future__ import annotations

from pydantic import BaseModel

from app.knowledge.models import RuleHit
from app.memory.store import ProfileSnapshot


class ClarifyingQuestion(BaseModel):
    id: str
    text: str
    field_key: str
    why_it_matters: str
    options: list[str] | None = None


class ActionProposal(BaseModel):
    action_id: str
    kind: str
    payload: dict
    payload_hash: str
    rationale: str
    expected_effect: str
    requires_confirmation: bool = True


class DecisionTrace(BaseModel):
    nodes_run: list[str] = []
    rules_used: list[dict] = []
    fields_used: list[str] = []
    critic_flags: list[str] = []
    disclaimers: list[str] = []


class ErrorItem(BaseModel):
    code: str
    message: str


class TurnState(BaseModel):
    # Inputs
    correlation_id: str
    user_id: str
    user_input: str

    # Long-term snapshot (read-only in a turn)
    profile: ProfileSnapshot

    # Intermediate artifacts
    intent: str = "deduction"
    category_hint: str | None = None
    retrieval_query: str = ""
    questions: list[ClarifyingQuestion] = []
    rule_hits: list[RuleHit] = []
    answer_draft: str = ""
    critic_flags: list[str] = []
    disclaimer: str = ""

    # Final outputs for the UI
    answer_revised: str = ""
    proposed_actions: list[ActionProposal] = []
    trace: DecisionTrace = DecisionTrace()
    errors: list[ErrorItem] = []
