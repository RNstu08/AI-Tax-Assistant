from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable
from datetime import date, datetime
from hashlib import sha256
from typing import Any
from venv import logger

from app.i18n.microcopy import CopyKey, resolve_language, t
from app.infra.config import AppSettings
from app.knowledge.retriever import InMemoryRetriever
from app.llm.groq_adapter import GroqAdapter
from app.memory.store import ProfileStore, _deep_merge
from app.nlu.context import EntityMemory
from app.nlu.quantities import parse_line_items
from app.orchestrator.prompts import REASONER_PROMPT, ROUTER_PROMPT
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
    ClarifyingQuestion,
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
    prompt = ROUTER_PROMPT.format(user_input=state.user_input)
    messages = [{"role": "user", "content": prompt}]

    res = groq.json(model="llama-3.1-8b-instant", messages=messages)

    allowed = {"commuting", "home_office", "equipment", "donations"}
    raw = res.get("category_hint")
    cat = (raw or "").strip().lower()
    state.category_hint = cat if cat in allowed else None

    # Fallback: simple keyword matching if router didn’t give a valid category
    if state.category_hint is None:
        text = state.user_input.lower()
        if any(
            w in text
            for w in [
                "equipment",
                "laptop",
                "notebook",
                "computer",
                "pc",
                "monitor",
                "bildschirm",
                "tastatur",
                "maus",
                "arbeitsmittel",
                "software",
            ]
        ):
            state.category_hint = "equipment"
        elif any(w in text for w in ["commute", "pendler", "arbeitsweg"]):
            state.category_hint = "commuting"
        elif any(w in text for w in ["home office", "homeoffice", "arbeitszimmer"]):
            state.category_hint = "home_office"
        elif any(w in text for w in ["spende", "spenden", "gemeinnützig"]):
            state.category_hint = "donations"
        # DO NOT set `state.category_hint = "equipment"` unconditionally!
        logger.warning(
            "Fallback keyword routing used for input: %s as %s",
            state.user_input,
            state.category_hint,
        )

    state.intent = res.get("intent", "question")
    state.retrieval_query = res.get("retrieval_query", state.user_input)
    return state


def node_extractor(state: TurnState, policy: SafetyPolicy, nlu_memory: EntityMemory) -> TurnState:
    state.trace.nodes_run.append("extractor")
    text = state.user_input.lower()
    patch: dict[str, Any] = {}

    # --- Ask for tax year if ambiguous/missing ---
    has_year_in_text = re.search(r"\b(2024|2025)\b", text)
    filing_set = state.filing_year_override or state.profile.data.get("filing", {}).get(
        "filing_year"
    )
    if ("year" in text or "jahr" in text) and not has_year_in_text and not filing_set:
        q_text = "For which tax year would you like to claim this deduction?"
        state.questions.append(q_text)
        if not getattr(state, "answer_draft", None):
            state.answer_draft = q_text
        return state
    # ------

    year_match = re.search(r"\b(2024|2025)\b", text)
    if year_match:
        state.filing_year_override = int(year_match.group(1))

    # Standard extractions
    # Home office (multiple phrasings and languages)
    if m := re.search(
        r"(?:worked\s+from\s+home|home\s*office|homeoffice|remote|wfh|im homeoffice)"
        r"[\s\w\-]*?(\d+)\s*(?:days|tage)?",
        text,
    ):
        patch.setdefault("deductions", {})["home_office_days"] = int(m.group(1))

    # Commute distance (multiple cases)
    if m := re.search(r"(commute|pendeln|entfernung|weg zur arbeit)[^\d]{0,20}(\d+)\s*km", text):
        patch.setdefault("deductions", {})["commute_km_per_day"] = int(m.group(2))
    elif m := re.search(r"(\d+)\s*km", text):
        if "commute_km_per_day" not in patch.get("deductions", {}):
            patch.setdefault("deductions", {})["commute_km_per_day"] = int(m.group(1))

    # Work days (in EN/DE, explicit or implicit)
    if m := re.search(r"(\d+)\s*(?:work\s*days|days|tage|arbeitstage)", text):
        patch.setdefault("deductions", {})["work_days_per_year"] = int(m.group(1))

    # Year
    if m := re.search(r"\b(2024|2025)\b", text):
        state.filing_year_override = int(m.group(1))
    if "this year" in text:
        state.filing_year_override = datetime.now().year

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
            item_data = {
                "amount_gross_eur": item["unit_price_eur"],
                "description": item["description"],
                "purchase_date": date(filing_year, 6, 15).isoformat(),
                "has_receipt": True,
            }
            # Remember the entire parsed item, which has the correct structure
            nlu_memory.remember({"kind": "equipment_item", "data": item})

            # This loop now correctly processes items from both the parser and the memory
            for _ in range(item.get("quantity", 1)):
                equipment_list.append(item_data)

    # print("DEBUG: node_extractor patch_proposal:", patch)
    # print("DEBUG: node_question_generator missing_keys:", missing_keys)

    if patch:
        state.patch_proposal = PatchProposal(patch=patch, rationale="Extracted from user input.")
    return state


def node_knowledge_agent(state: TurnState, retriever: InMemoryRetriever) -> TurnState:
    state.trace.nodes_run.append("knowledge_agent")
    filing_year = state.filing_year_override or state.profile.data.get("filing", {}).get(
        "filing_year", 2025
    )
    state.rule_hits = retriever.search(query=state.retrieval_query, year=filing_year)
    state.trace.rules_used = [{"rule_id": h.rule_id, "year": h.year} for h in state.rule_hits]
    return state


def node_question_generator(state: TurnState, policy: SafetyPolicy) -> TurnState:
    """Checks if any required data for relevant, calculable rules is missing."""
    state.trace.nodes_run.append("question_generator")
    if not state.rule_hits:
        return state

    temp_profile_data = json.loads(json.dumps(state.profile.data))
    if state.patch_proposal:
        _deep_merge(state.patch_proposal.patch, temp_profile_data)

    # Only consider rules that are directly relevant to the user's query
    triggered_categories = (
        {state.category_hint} if state.category_hint else {h.category for h in state.rule_hits}
    )
    calculable_categories = {"commuting", "home_office", "equipment"}
    relevant_categories = triggered_categories.intersection(calculable_categories)

    if not relevant_categories:
        return state

    required_keys: set[str] = set()
    for hit in state.rule_hits:
        if hit.category in relevant_categories:
            required_keys.update(hit.required_data_points)

    if not required_keys:
        return state

    missing_keys: set[str] = set()
    for key in required_keys:
        parts, current_level, is_missing = key.split("."), temp_profile_data, False
        for part in parts:
            if not isinstance(current_level, dict) or part not in current_level:
                is_missing = True
                break
            current_level = current_level.get(part, {})
        if is_missing:
            missing_keys.add(key)

    if missing_keys:
        first_missing = sorted(list(missing_keys))[0]
        q_text = (
            f"To help calculate this, I need some more information. "
            f"What is the value for '{first_missing}'?"
        )
        state.questions.append(
            ClarifyingQuestion(
                id=f"q_{uuid.uuid4().hex[:8]}",
                text=q_text,
                field_key=first_missing,
                why_it_matters="Needed for calculation.",
            )
        )
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
            amount = D(item["amount_gross_eur"])
            # --- depreciation warning fix ---
            if amount > 952:
                msg = (
                    f"Equipment item {i} ('{item['description']}') "
                    f"costs {fmt_eur(amount)}, which is above the instant deduction limit. "
                    "Consult a tax advisor for depreciation period."
                )
                state.errors.append(ErrorItem(code="depreciation_needed", message=msg))
            # ------
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


def node_reasoner(
    state: TurnState, groq: GroqAdapter, on_token: Callable[[str], None]
) -> TurnState:
    """Uses an LLM to synthesize a final answer from all available context."""
    state.trace.nodes_run.append("reasoner")
    lang = resolve_language(state)
    state.disclaimer = t(lang, CopyKey.DISCLAIMER)

    # Build the context for the LLM
    rules_context = "\n".join([f"- {h.title}: {h.snippet}" for h in state.rule_hits])

    # Make the calculation context intent-aware
    calc_context = ""
    # ONLY show calculations if the user's intent was to discuss a deduction.
    if state.intent == "deduction" and state.calc_results:
        calc_lines = []
        # If new information was just extracted, only talk about that new information.
        if state.patch_proposal:
            new_cats = state.patch_proposal.patch.get("deductions", {}).keys()
            for cat_name in new_cats:
                for result_key, result_data in state.calc_results.items():
                    if cat_name.startswith(result_key.split("_")[0]):
                        amount_str = fmt_eur(result_data["amount_eur"])
                        calc_lines.append(f"- {result_key.replace('_', ' ').title()}: {amount_str}")
        else:  # Otherwise, if it's a general deduction query, summarize all known calculations.
            for key, res in state.calc_results.items():
                if "total" not in key and "amount_eur" in res:
                    calc_lines.append(
                        f"- {key.replace('_', ' ').title()}: {fmt_eur(res['amount_eur'])}"
                    )

        if calc_lines:
            calc_context = "\n".join(calc_lines)

    # If the intent is not a deduction or no relevant calculations were made,
    # use a more generic message.
    if not calc_context:
        calc_context = "No relevant calculations were performed for this specific query."

    system_prompt = REASONER_PROMPT.format(
        language="German" if lang == "de" else "English",
        filing_year=state.profile.data.get("filing", {}).get("filing_year", 2025),
        rules_context=rules_context or "No specific rules found.",
        calculations_context=calc_context,
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state.user_input},
    ]

    full_response = ""

    def collect_and_stream(token: str):
        nonlocal full_response
        full_response += token
        on_token(token)

    groq.stream(model="llama-3.1-8b-instant", messages=messages, on_token=collect_and_stream)
    state.answer_draft = full_response

    # The final node_critic will add the disclaimer
    state.answer_revised = state.answer_draft
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


def apply_ui_action(
    user_id: str, ui_action: UIAction, last_state: TurnState, store: ProfileStore
) -> TurnState:
    """Applies a UI-triggered action, handles database writes, and returns an updated state."""
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
    elif ui_action.kind == "import_parsed_items":
        if not (ui_action.payload and "items" in ui_action.payload):
            state.errors.append(
                ErrorItem(code="invalid_payload", message="Import action is missing item data.")
            )
            return state

        items_to_add = []
        filing_year = last_state.profile.data.get("filing", {}).get(
            "filing_year", date.today().year
        )

        for item in ui_action.payload["items"]:
            try:
                items_to_add.append(
                    {
                        "description": str(item["description"]),
                        "amount_gross_eur": str(D(item["total_eur"])),
                        "purchase_date": date(filing_year, 6, 15).isoformat(),
                        "has_receipt": True,
                    }
                )
            except (KeyError, TypeError):
                continue

        if items_to_add:
            current_profile = store.get_profile(user_id)
            existing_items = current_profile.data.get("deductions", {}).get("equipment_items", [])
            updated_items = existing_items + items_to_add
            patch = {"deductions": {"equipment_items": updated_items}}

            new_snapshot, diff = store.apply_patch(user_id, patch)
            action_id = f"import_items:{uuid.uuid4().hex[:8]}"
            store.commit_action(
                user_id, action_id, "import_parsed_items", ui_action.payload, "", diff, True
            )
            state.profile = new_snapshot
            state.committed_action = CommitResult(
                action_id=action_id, committed=True, version_after=new_snapshot.version
            )

    return state


def run_turn(
    user_id: str,
    user_text: str,
    store: ProfileStore | None = None,
    filing_year_override: int | None = None,
) -> TurnState:
    """Non-streaming version for tests."""

    def no_op_on_token(token: str):
        pass

    return run_turn_streaming(user_id, user_text, no_op_on_token, store, filing_year_override)


def run_turn_streaming(
    user_id: str,
    user_text: str,
    on_token: Callable[[str], None],
    store: ProfileStore | None = None,
    filing_year_override: int | None = None,
) -> TurnState:
    """
    Runs the full agent graph, handling questions and streaming the final response.
    """
    cfg = AppSettings()
    store = store or ProfileStore(sqlite_path=cfg.sqlite_path)
    policy = load_policy()
    groq = GroqAdapter(api_key=cfg.groq_api_key)
    retriever = InMemoryRetriever()

    profile = store.get_profile(user_id)
    nlu_memory = EntityMemory.from_profile(profile.data)
    if filing_year_override:
        profile.data["filing"] = {"filing_year": filing_year_override}

    state = TurnState(
        correlation_id=f"turn:{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        user_input=user_text,
        profile=profile,
    )

    # Graph Execution
    state = node_safety_gate(state, policy)
    state = node_router(state, groq)
    state = node_extractor(state, policy, nlu_memory)
    state = node_knowledge_agent(state, retriever)
    state = node_question_generator(state, policy)
    state = node_calculators(state, policy)
    state = node_reasoner(state, groq, on_token)  # Pass the callback to the reasoner
    state = node_critic(state, policy)
    state = node_action_planner(state, policy)
    state = node_trace_emitter(state)

    if state.errors:
        # Join all error messages for the user into the answer field
        lang = resolve_language(state)
        state.answer_draft = "\n".join([e.message for e in state.errors])
        # Optionally also add disclaimer as in normal flows
        state.answer_revised = f"{state.answer_draft}\n\n{t(lang, CopyKey.DISCLAIMER)}"
    elif (
        not getattr(state, "answer_draft", None) or not state.answer_draft.strip()
    ) and state.questions:
        # Surface the latest clarifying question to the user if no answer yet
        # and there's a question pending
        state.answer_draft = (
            state.questions[-1].text
            if isinstance(state.questions[-1], ClarifyingQuestion)
            else state.questions[-1]
        )
        state.answer_revised = state.answer_draft
    return state
