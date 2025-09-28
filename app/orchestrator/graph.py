from __future__ import annotations

import json
import re
import uuid
from datetime import date
from hashlib import sha256
from typing import Any

from app.knowledge.retriever import InMemoryRetriever
from app.llm.groq_adapter import GroqAdapter
from app.memory.store import ProfileStore
from app.orchestrator.safety import patch_allowed_by_policy
from app.safety.policy import SafetyPolicy, load_policy
from tools.calculators import calc_commute, calc_equipment_item, calc_home_office
from tools.money import D, fmt_eur, parse_eur_amounts

from .models import (
    ActionProposal,
    CommitResult,
    ErrorItem,
    FieldDiff,
    PatchProposal,
    TurnState,
    UIAction,
)


def _hash_payload(obj: dict) -> str:
    """Creates a deterministic hash for a payload dictionary."""
    return sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def _deep_merge(source: dict, destination: dict) -> dict:
    """Helper to deeply merge dictionaries for temporary state calculation."""
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            _deep_merge(value, node)
        else:
            destination[key] = value
    return destination


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
    """Extracts data from user input and creates a PatchProposal if data is found."""
    state.trace.nodes_run.append("extractor")
    text = state.user_input.lower()
    patch: dict[str, Any] = {}
    amounts = parse_eur_amounts(state.user_input)

    km_match = re.search(r"(\d+)\s*km", text)
    if km_match:
        patch.setdefault("deductions", {})["commute_km_per_day"] = int(km_match.group(1))

    days_match = re.search(r"(\d+)\s*(?:work\s*days|days|tage)", text)
    if days_match:
        patch.setdefault("deductions", {})["work_days_per_year"] = int(days_match.group(1))

    ho_match = re.search(r"(?:home\s*office|homeoffice)[\s\w]*?(\d+)", text)
    if ho_match:
        patch.setdefault("deductions", {})["home_office_days"] = int(ho_match.group(1))

    if "laptop" in text or "equipment" in text or amounts:
        if amounts:
            items = patch.setdefault("deductions", {}).setdefault("equipment_items", [])
            fy = state.profile.data.get("filing", {}).get("filing_year", date.today().year)
            items.append(
                {
                    "amount_gross_eur": str(amounts[0]),
                    "purchase_date": date(fy, 6, 15).isoformat(),
                    "has_receipt": True,
                }
            )

    if patch:
        state.patch_proposal = PatchProposal(patch=patch, rationale="Extracted from user input.")
    return state


def node_knowledge_agent(state: TurnState, retriever: InMemoryRetriever) -> TurnState:
    state.trace.nodes_run.append("knowledge_agent")
    filing_year = state.profile.data.get("filing", {}).get("filing_year", 2025)
    state.rule_hits = retriever.search(query=state.retrieval_query, year=filing_year)
    state.trace.rules_used = [{"rule_id": h.rule_id, "year": h.year} for h in state.rule_hits]
    return state


def node_calculators(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("calculators")
    temp_profile_data = json.loads(json.dumps(state.profile.data))
    if state.patch_proposal:
        _deep_merge(state.patch_proposal.patch, temp_profile_data)

    deductions = temp_profile_data.get("deductions", {})
    filing_year = temp_profile_data.get("filing", {}).get("filing_year", 2025)
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
    state.trace.nodes_run.append("reasoner")
    lines = [f"This is a response about '{state.intent}'."]
    if state.rule_hits:
        lines.append("Relevant rules found:")
        for hit in state.rule_hits:
            lines.append(f"- {hit.title} [{hit.rule_id}]")

    if state.calc_results:
        lines.append("\n**Estimated Amounts:**")
        for key, res in state.calc_results.items():
            if "total" not in key and "amount_eur" in res:
                lines.append(f"- {key.replace('_', ' ').title()}: {fmt_eur(res['amount_eur'])}")
        if "equipment_total" in state.calc_results:
            total_str = fmt_eur(state.calc_results["equipment_total"]["amount_eur"])
            lines.append(f"- **Equipment Total**: {total_str}")

    state.answer_draft = "\n".join(lines)
    return state


def node_critic(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("critic")
    flags: list[str] = []
    hit_ids = {h.rule_id for h in state.rule_hits}
    cited_ids = set(re.findall(r"\[(de_\d{4}_\w+)\]", state.answer_draft))
    if not cited_ids.issubset(hit_ids):
        flags.append("citation_mismatch")

    euros_present = "€" in state.answer_draft
    calculators_used = bool(state.calc_results)
    if euros_present and calculators_used:
        flags.append("amounts_backed_by_calculators")
    elif euros_present and not calculators_used:
        flags.append("ungrounded_euro_amount_removed")
        state.answer_draft = re.sub(r"€\s?\d[\d.,]*", "[amount]", state.answer_draft)

    state.critic_flags = flags
    state.answer_revised = f"{state.answer_draft}\n\n{state.disclaimer}"
    return state


def node_action_planner(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("action_planner")
    if state.calc_results:
        payload = {"rules": [h.rule_id for h in state.rule_hits]}
        state.proposed_actions.append(
            ActionProposal(
                action_id=f"compute_estimate:{_hash_payload(payload)}",
                kind="compute_estimate",
                payload=payload,
                payload_hash=_hash_payload(payload),
                rationale="Run calculators with the provided data.",
                expected_effect="Shows an itemized estimate.",
                requires_confirmation=False,
            )
        )
    if state.patch_proposal:
        payload = state.patch_proposal.patch
        state.proposed_actions.append(
            ActionProposal(
                action_id=f"confirm_profile_patch:{_hash_payload(payload)}",
                kind="confirm_profile_patch",
                payload=payload,
                payload_hash=_hash_payload(payload),
                rationale="Save the details we discussed to your profile.",
                expected_effect="Updates your profile for future calculations.",
            )
        )
    return state


def node_trace_emitter(state: TurnState) -> TurnState:
    state.trace.nodes_run.append("trace_emitter")
    state.trace.disclaimers.append(state.disclaimer)
    return state


def apply_ui_action(
    user_id: str, ui_action: UIAction, last_state: TurnState, store: ProfileStore
) -> TurnState:
    policy = load_policy()
    state = last_state.model_copy(deep=True)
    proposals = {p.action_id: p for p in state.proposed_actions}
    if ui_action.kind == "confirm" and ui_action.ref_action in proposals:
        prop = proposals[ui_action.ref_action]
        allowed, why = patch_allowed_by_policy(prop.payload, policy)
        if not allowed:
            state.errors.append(ErrorItem(code="policy_violation", message=why))
            return state
        new_snapshot, diff = store.apply_patch(user_id, prop.payload)
        store.commit_action(
            user_id, prop.action_id, prop.kind, prop.payload, prop.payload_hash, diff, True
        )
        state.profile = new_snapshot
        state.profile_diff = [FieldDiff(**d) for d in diff]
        state.committed_action = CommitResult(
            action_id=prop.action_id, committed=True, version_after=new_snapshot.version
        )
    elif ui_action.kind == "undo":
        try:
            new_snapshot = store.undo_action(user_id, f"undo:{uuid.uuid4().hex[:8]}")
            state.profile = new_snapshot
        except ValueError as e:
            state.errors.append(ErrorItem(code="undo_failed", message=str(e)))
    return state


def run_turn(
    user_id: str,
    user_text: str,
    store: ProfileStore | None = None,
    filing_year_override: int | None = None,
) -> TurnState:
    if store is None:
        store = ProfileStore()

    policy = load_policy()
    groq = GroqAdapter(api_key=None)
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

    # A bit of reflection to pass the right dependencies to each node
    nodes = [
        (node_safety_gate, {"policy": policy}),
        (node_router, {"groq": groq}),
        (node_extractor, {"policy": policy}),
        (node_knowledge_agent, {"retriever": retriever}),
        (node_calculators, {"policy": policy}),
        (node_reasoner, {"groq": groq}),
        (node_critic, {"policy": policy}),
        (node_action_planner, {"policy": policy}),
        (node_trace_emitter, {}),
    ]

    for node_func, deps in nodes:
        if state.errors:
            break
        state = node_func(state, **deps)
    return state
