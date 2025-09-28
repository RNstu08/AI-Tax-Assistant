from __future__ import annotations

import re
import uuid
from hashlib import sha256

from app.knowledge.retriever import InMemoryRetriever
from app.llm.groq_adapter import GroqAdapter
from app.memory.store import ProfileStore
from app.safety.policy import SafetyPolicy, load_policy

from .models import ActionProposal, ErrorItem, TurnState


def _hash_payload(obj: dict) -> str:
    """Creates a deterministic hash for a payload dictionary."""
    import json

    return sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


# --- Agent Nodes (Stubs for PR3) ---


def node_safety_gate(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("safety_gate")
    if any(w in state.user_input.lower() for w in ["freelancer", "austria"]):
        # FIX: Append an instance of ErrorItem, not a dict
        state.errors.append(ErrorItem(code="out_of_scope", message="Query is out of scope."))
    state.disclaimer = "Informational only; not tax advice. Please verify with official guidance."
    return state


def node_router(state: TurnState, groq: GroqAdapter) -> TurnState:
    state.trace.nodes_run.append("router")
    messages = [{"role": "user", "content": state.user_input}]
    res = groq.json(model="stub-router", messages=messages)
    state.intent = res.get("intent", "deduction")
    state.category_hint = res.get("category_hint")
    state.retrieval_query = res.get("retrieval_query", state.user_input)
    return state


def node_knowledge_agent(state: TurnState, retriever: InMemoryRetriever) -> TurnState:
    state.trace.nodes_run.append("knowledge_agent")
    filing_year = state.profile.data.get("filing", {}).get("filing_year", 2025)
    state.rule_hits = retriever.search(query=state.retrieval_query, year=filing_year)
    state.trace.rules_used = [{"rule_id": h.rule_id, "year": h.year} for h in state.rule_hits]
    return state


def node_reasoner(state: TurnState, groq: GroqAdapter) -> TurnState:
    state.trace.nodes_run.append("reasoner")
    lines = [f"This is a stubbed response about '{state.intent}'."]
    if state.rule_hits:
        lines.append("Relevant rules found:")
        for hit in state.rule_hits:
            lines.append(f"- {hit.title} [{hit.rule_id}]")
    state.answer_draft = "\n".join(lines)
    return state


def node_critic(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("critic")
    hit_ids = {h.rule_id for h in state.rule_hits}
    cited_ids = set(re.findall(r"\[(de_\d{4}_\w+)\]", state.answer_draft))
    if not cited_ids.issubset(hit_ids):
        state.critic_flags.append("citation_mismatch")
    state.answer_revised = f"{state.answer_draft}\n\n{state.disclaimer}"
    return state


def node_action_planner(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("action_planner")
    payload = {"example": True}
    state.proposed_actions.append(
        ActionProposal(
            action_id=f"compute_estimate:{uuid.uuid4().hex[:8]}",
            kind="compute_estimate",
            payload=payload,
            payload_hash=_hash_payload(payload),
            rationale="Run calculators with the provided data.",
            expected_effect="Shows an itemized estimate.",
            requires_confirmation=False,
        )
    )
    return state


def node_trace_emitter(state: TurnState) -> TurnState:
    state.trace.nodes_run.append("trace_emitter")
    state.trace.disclaimers.append(state.disclaimer)
    return state


# --- Orchestrator Entrypoint ---


def run_turn(user_id: str, user_text: str, filing_year_override: int | None = None) -> TurnState:
    """Deterministic per-turn orchestrator run (read-only and stubbed in PR3)."""
    policy = load_policy()
    groq = GroqAdapter(api_key=None)  # Force offline mode
    store = ProfileStore(db_path=".data/profile.db")
    retriever = InMemoryRetriever()

    profile = store.get_profile(user_id)
    if filing_year_override:
        profile.data["filing"] = {"filing_year": filing_year_override}

    state = TurnState(
        correlation_id=f"turn:{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        user_input=user_text,
        profile=profile,
    )

    if not state.errors:
        state = node_safety_gate(state, policy)
    if not state.errors:
        state = node_router(state, groq)
    if not state.errors:
        state = node_knowledge_agent(state, retriever)
    if not state.errors:
        state = node_reasoner(state, groq)
    if not state.errors:
        state = node_critic(state, policy)
    if not state.errors:
        state = node_action_planner(state, policy)
    if not state.errors:
        state = node_trace_emitter(state)

    return state
