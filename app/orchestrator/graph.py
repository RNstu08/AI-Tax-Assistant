from __future__ import annotations

import re
import uuid
from datetime import date
from hashlib import sha256

from app.knowledge.retriever import InMemoryRetriever
from app.llm.groq_adapter import GroqAdapter
from app.memory.store import ProfileStore
from app.safety.policy import SafetyPolicy, load_policy
from tools.calculators import (
    calc_commute,
    calc_equipment_item,
    calc_home_office,
)
from tools.money import D, fmt_eur, parse_eur_amounts

from .models import ActionProposal, ErrorItem, TurnState


def _hash_payload(obj: dict) -> str:
    """Creates a deterministic hash for a payload dictionary."""
    import json

    return sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


# --- Agent Nodes ---


def node_safety_gate(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("safety_gate")
    if any(w in state.user_input.lower() for w in ["freelancer", "austria"]):
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


def node_extractor(state: TurnState, policy: SafetyPolicy) -> TurnState:
    """Extracts structured data from user input using regex and keywords."""
    state.trace.nodes_run.append("extractor")
    text = state.user_input.lower()
    deductions = state.profile.data.setdefault("deductions", {})

    nums = [int(n) for n in re.findall(r"\b\d+\b", text)]
    amounts = parse_eur_amounts(state.user_input)

    # FIX: Use multi-line if statements
    if "commute" in text or "pendler" in text:
        state.category_hint = "commuting"
        if nums:
            deductions["commute_km_per_day"] = nums[0]
        if len(nums) > 1:
            deductions["work_days_per_year"] = nums[1]

    if "home office" in text or "homeoffice" in text:
        state.category_hint = "home_office"
        if nums:
            deductions["home_office_days"] = nums[0]

    if "laptop" in text or "equipment" in text or amounts:
        state.category_hint = "equipment"
        if amounts:
            items = deductions.setdefault("equipment_items", [])
            fy = state.profile.data.get("filing", {}).get("filing_year", date.today().year)
            items.append(
                {
                    "amount_gross_eur": str(amounts[0]),
                    "purchase_date": date(fy, 6, 15).isoformat(),
                    "has_receipt": True,
                }
            )

    return state


def node_knowledge_agent(state: TurnState, retriever: InMemoryRetriever) -> TurnState:
    # ... (This function is unchanged)
    state.trace.nodes_run.append("knowledge_agent")
    filing_year = state.profile.data.get("filing", {}).get("filing_year", 2025)
    state.rule_hits = retriever.search(query=state.retrieval_query, year=filing_year)
    state.trace.rules_used = [{"rule_id": h.rule_id, "year": h.year} for h in state.rule_hits]
    return state


def node_calculators(state: TurnState, policy: SafetyPolicy) -> TurnState:
    # ... (This function is unchanged)
    state.trace.nodes_run.append("calculators")
    deductions = state.profile.data.get("deductions", {})
    filing_year = state.profile.data.get("filing", {}).get("filing_year", 2025)
    state.calc_results = {}

    if "commute_km_per_day" in deductions and "work_days_per_year" in deductions:
        res = calc_commute(
            filing_year,
            D(deductions["commute_km_per_day"]),
            deductions["work_days_per_year"],
            deductions.get("home_office_days", 0),
        )
        if res.get("amount_eur"):
            state.calc_results["commuting"] = res

    if "home_office_days" in deductions:
        res = calc_home_office(filing_year, deductions["home_office_days"])
        if res.get("amount_eur"):
            state.calc_results["home_office"] = res

    if "equipment_items" in deductions:
        total_equip = D(0)
        for i, item in enumerate(deductions["equipment_items"]):
            res = calc_equipment_item(
                filing_year,
                D(item["amount_gross_eur"]),
                date.fromisoformat(item["purchase_date"]),
                item["has_receipt"],
            )
            if res.get("amount_eur"):
                state.calc_results[f"equipment_item_{i}"] = res
                total_equip += res["amount_eur"]
        if total_equip > 0:
            state.calc_results["equipment_total"] = {"amount_eur": total_equip}

    return state


def node_reasoner(state: TurnState, groq: GroqAdapter) -> TurnState:
    # ... (This function is unchanged, but the line-length fix is included)
    state.trace.nodes_run.append("reasoner")
    lines = [f"This is a response about '{state.intent}'."]
    if state.rule_hits:
        lines.append("Relevant rules found:")
        for hit in state.rule_hits:
            lines.append(f"- {hit.title} [{hit.rule_id}]")

    if state.calc_results:
        lines.append("\n**Estimated Amounts:**")
        for key, res in state.calc_results.items():
            if "total" not in key and res.get("amount_eur"):
                lines.append(f"- {key.replace('_', ' ').title()}: {fmt_eur(res['amount_eur'])}")
        if "equipment_total" in state.calc_results:
            total_str = fmt_eur(state.calc_results["equipment_total"]["amount_eur"])
            lines.append(f"- **Equipment Total**: {total_str}")

    state.answer_draft = "\n".join(lines)
    return state


def node_critic(state: TurnState, policy: SafetyPolicy) -> TurnState:
    # ... (This function is unchanged)
    state.trace.nodes_run.append("critic")
    hit_ids = {h.rule_id for h in state.rule_hits}
    cited_ids = set(re.findall(r"\[(de_\d{4}_\w+)\]", state.answer_draft))
    if not cited_ids.issubset(hit_ids):
        state.critic_flags.append("citation_mismatch")

    if "€" in state.answer_draft and not state.calc_results:
        state.critic_flags.append("ungrounded_euro_amount_removed")
        state.answer_draft = re.sub(r"€\s?\d[\d.,]*", "[amount]", state.answer_draft)

    state.answer_revised = f"{state.answer_draft}\n\n{state.disclaimer}"
    return state


def node_action_planner(state: TurnState, policy: SafetyPolicy) -> TurnState:
    # ... (This function is unchanged)
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
    # ... (This function is unchanged)
    state.trace.nodes_run.append("trace_emitter")
    state.trace.disclaimers.append(state.disclaimer)
    return state


# --- Orchestrator Entrypoint ---


def run_turn(user_id: str, user_text: str, filing_year_override: int | None = None) -> TurnState:
    # ... (This function is unchanged)
    policy = load_policy()
    groq = GroqAdapter(api_key=None)
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

    state = node_safety_gate(state, policy)
    state = node_router(state, groq)
    state = node_extractor(state, policy)
    state = node_knowledge_agent(state, retriever)
    state = node_calculators(state, policy)
    state = node_reasoner(state, groq)
    state = node_critic(state, policy)
    state = node_action_planner(state, policy)
    state = node_trace_emitter(state)

    return state
