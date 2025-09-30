from __future__ import annotations

import json
import re
import uuid
from datetime import date
from hashlib import sha256
from typing import Any

from app.i18n.microcopy import CopyKey, resolve_language, t
from app.knowledge.retriever import InMemoryRetriever
from app.llm.groq_adapter import GroqAdapter
from app.memory.store import ProfileStore, _deep_merge
from app.nlu.context import EntityMemory
from app.nlu.quantities import parse_line_items
from app.orchestrator.safety import patch_allowed_by_policy
from app.safety.policy import SafetyPolicy, load_policy
from tools.calculators import (
    calc_commute,
    calc_equipment_item,
    calc_home_office,
)
from tools.money import D, fmt_eur

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


# --- Agent Nodes ---


def node_safety_gate(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("safety_gate")
    if any(w in state.user_input.lower() for w in ["freelancer", "austria"]):
        state.errors.append(ErrorItem(code="out_of_scope", message="Query is out of scope."))
    state.disclaimer = t("en", CopyKey.DISCLAIMER)
    return state


def node_router(state: TurnState, groq: GroqAdapter) -> TurnState:
    state.trace.nodes_run.append("router")
    messages = [{"role": "user", "content": state.user_input}]
    res = groq.json(model="stub-router", messages=messages)
    state.intent = res.get("intent", "deduction")
    state.category_hint = res.get("category_hint")
    state.retrieval_query = res.get("retrieval_query", state.user_input)
    return state


def node_extractor(state: TurnState, policy: SafetyPolicy, nlu_memory: EntityMemory) -> TurnState:
    state.trace.nodes_run.append("extractor")
    text = state.user_input.lower()
    patch: dict[str, Any] = {}

    # Standard extractions
    if m := re.search(r"(\d+)\s*km", text):
        patch.setdefault("deductions", {})["commute_km_per_day"] = int(m.group(1))
    if m := re.search(r"(\d+)\s*(?:work\s*days|days|tage)", text):
        patch.setdefault("deductions", {})["work_days_per_year"] = int(m.group(1))
    if m := re.search(r"(?:home\s*office|homeoffice)[\s\w]*?(\d+)", text):
        patch.setdefault("deductions", {})["home_office_days"] = int(m.group(1))

    # NLU Parsing for equipment, with pronoun resolution
    nlu_items = parse_line_items(state.user_input)
    resolved_entity = nlu_memory.resolve(text, kind_hint="equipment_item")

    # If a pronoun was used ("another one") and we didn't find a new item in the text
    if resolved_entity and not nlu_items:
        # The 'data' from the resolved entity has the same structure as a parsed item
        nlu_items.append(resolved_entity["data"])

    if nlu_items:
        equipment_list = patch.setdefault("deductions", {}).setdefault("equipment_items", [])
        filing_year = state.filing_year_override or state.profile.data.get("filing", {}).get(
            "filing_year", date.today().year
        )

        for item in nlu_items:
            # FIX: Remember the entire parsed item, which has the correct structure
            nlu_memory.remember({"kind": "equipment_item", "data": item})

            # This loop now correctly processes items from both the parser and the memory
            for _ in range(item.get("quantity", 1)):
                equipment_list.append(
                    {
                        "amount_gross_eur": item["unit_price_eur"],
                        "purchase_date": date(filing_year, 6, 15).isoformat(),
                        "has_receipt": True,
                        "description": item["description"],
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
    filing_year = state.filing_year_override or temp_profile_data.get("filing", {}).get(
        "filing_year", 2025
    )
    # filing_year = temp_profile_data.get("filing", {}).get("filing_year", 2025)
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
    """Generates a human-readable summary of the turn's findings."""
    state.trace.nodes_run.append("reasoner")
    lang = resolve_language(state)
    state.disclaimer = t(lang, CopyKey.DISCLAIMER)
    state.citations = [h.rule_id for h in state.rule_hits]

    lines = []

    # Add relevant rules if any were found
    if state.rule_hits:
        lines.append("Relevant rules found:")
        for hit in state.rule_hits:
            lines.append(f"- {hit.title} [{hit.rule_id}]")

    # FIX: Use simple, robust logic to display ALL calculations that were made.
    if state.calc_results:
        lines.append(f"\n**{t(lang, CopyKey.ESTIMATED_AMOUNTS)}:**")
        for key, res in sorted(state.calc_results.items()):
            if "total" not in key and "amount_eur" in res:
                amount_str = fmt_eur(res["amount_eur"])
                lines.append(f"- {key.replace('_', ' ').title()}: {amount_str}")

    state.answer_draft = "\n".join(lines)
    return state


def node_critic(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("critic")
    flags: list[str] = []
    euros_present = "€" in state.answer_draft
    calculators_used = bool(state.calc_results)
    if euros_present and calculators_used:
        flags.append("amounts_backed_by_calculators")
    state.critic_flags = flags
    state.answer_revised = f"{state.answer_draft}\n\n{state.disclaimer}"
    return state


def node_action_planner(state: TurnState, policy: SafetyPolicy) -> TurnState:
    state.trace.nodes_run.append("action_planner")
    if state.rule_hits:
        payload = {"rules": [h.rule_id for h in state.rule_hits]}
        # Add a UUID to ensure the action ID is always unique
        action_id = f"compute_estimate:{uuid.uuid4().hex[:8]}"
        state.proposed_actions.append(
            ActionProposal(
                action_id=action_id,
                kind="compute_estimate",
                payload=payload,
                payload_hash=_hash_payload(payload),
                rationale="Run calculators with the available data.",
                expected_effect="Shows an itemized estimate.",
                requires_confirmation=False,
            )
        )
    # Conditionally propose a profile patch if one was generated
    if state.patch_proposal:
        payload = state.patch_proposal.patch
        # Add a UUID to ensure the action ID is always unique
        action_id = f"confirm_profile_patch:{uuid.uuid4().hex[:8]}"
        state.proposed_actions.append(
            ActionProposal(
                action_id=action_id,
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


# def resolve_language(state: TurnState) -> str:
#     """Determines the language for the turn, prioritizing user preference."""
#     pref = state.profile.data.get("preferences", {}).get("language", "auto")
#     if pref in ("en", "de"):
#         return pref
#     return lang_detect(state.user_input)


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
        # Clear the proposed actions so they can't be clicked again.
        state.proposed_actions = []
    elif ui_action.kind == "undo":
        try:
            new_snapshot = store.undo_action(user_id, f"undo:{uuid.uuid4().hex[:8]}")
            state.profile = new_snapshot
        except ValueError as e:
            state.errors.append(ErrorItem(code="undo_failed", message=str(e)))

    elif ui_action.kind == "set_preferences":
        current_prefs = last_state.profile.data.get("preferences", {})
        new_prefs = ui_action.payload or {}
        patch = {"preferences": {**current_prefs, **new_prefs}}

        new_snapshot, diff = store.apply_patch(user_id, patch)
        action_id = f"set_preferences:{uuid.uuid4().hex[:8]}"
        store.commit_action(user_id, action_id, "set_preferences", patch, "", diff, True)
        state.profile = new_snapshot
    return state


def run_turn(
    user_id: str,
    user_text: str,
    store: ProfileStore | None = None,
    filing_year_override: int | None = None,
) -> TurnState:
    """Initializes and runs the full agent graph for a single turn."""
    store = store or ProfileStore()
    policy = load_policy()
    groq = GroqAdapter(api_key=None)
    retriever = InMemoryRetriever()

    profile = store.get_profile(user_id)

    # Initialize EntityMemory from the profile at the start of the turn
    nlu_memory = EntityMemory.from_profile(profile.data)
    if filing_year_override:
        profile.data["filing"] = {"filing_year": filing_year_override}
    state = TurnState(
        correlation_id=f"turn:{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        user_input=user_text,
        profile=profile,
    )

    state = node_safety_gate(state, policy)
    if state.errors:
        return state
    state = node_router(state, groq)
    if state.errors:
        return state
    state = node_extractor(state, policy, nlu_memory)
    if state.errors:
        return state
    state = node_knowledge_agent(state, retriever)
    if state.errors:
        return state
    state = node_calculators(state, policy)
    if state.errors:
        return state
    state = node_reasoner(state, groq)
    if state.errors:
        return state
    state = node_critic(state, policy)
    if state.errors:
        return state
    state = node_action_planner(state, policy)
    if state.errors:
        return state
    state = node_trace_emitter(state)

    if nlu_memory.entities:
        store.apply_patch(user_id, {"nlu_memory": nlu_memory.to_dict()})

    return state
