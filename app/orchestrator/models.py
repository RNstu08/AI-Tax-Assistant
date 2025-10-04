from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.knowledge.models import RuleHit
from app.memory.store import ProfileSnapshot


class PatchProposal(BaseModel):
    patch: dict[str, Any]
    rationale: str


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


class UIAction(BaseModel):
    kind: str
    ref_action: str | None = None
    payload: dict | None = None


class CommitResult(BaseModel):
    action_id: str
    committed: bool
    version_after: int


class FieldDiff(BaseModel):
    path: str
    old: Any
    new: Any


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
    profile: ProfileSnapshot

    # Intermediate artifacts
    intent: str = "deduction"
    category_hint: str | None = None
    retrieval_query: str = ""
    patch_proposal: PatchProposal | None = None
    filing_year_override: int | None = None
    questions: list[ClarifyingQuestion] = []
    rule_hits: list[RuleHit] = []
    answer_draft: str = ""
    critic_flags: list[str] = []
    disclaimer: str = ""
    calc_results: dict[str, Any] = Field(default_factory=dict)

    # Add the missing 'citations' field
    citations: list[str] = []

    # Final outputs for the UI
    answer_revised: str = ""
    proposed_actions: list[ActionProposal] = []
    trace: DecisionTrace = DecisionTrace()
    errors: list[ErrorItem] = []
    profile_diff: list[FieldDiff] | None = None
    committed_action: CommitResult | None = None
