from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

from app.i18n.microcopy import CopyKey, t
from app.orchestrator.models import TurnState
from tools.money import D, fmt_eur


@dataclass(frozen=True)
class ItemizedEntry:
    category: str
    amount_eur: str
    raw_amount: str
    details: dict[str, Any]
    caps_applied: list[str]


@dataclass(frozen=True)
class ReportSummary:
    user_id: str
    turn_id: str
    created_ms: int
    profile_version: int
    language: str
    disclaimer: str
    citations: list[str]
    rules_used: list[dict[str, Any]]
    itemization: list[ItemizedEntry]
    totals_eur: str
    checklist: list[str]
    hash: str


def build_receipts_checklist(itemization: list[ItemizedEntry], lang: str = "en") -> list[str]:
    """Generates a contextual checklist of required documents."""
    checklist_items: list[str] = []
    seen_categories = {entry.category for entry in itemization}

    # FIX: Use the CopyKey enum for all calls to the 't' function
    if "commuting" in seen_categories:
        checklist_items.append(t(lang, CopyKey.CHECKLIST_COMMUTING))
    if "home_office" in seen_categories:
        checklist_items.append(t(lang, CopyKey.CHECKLIST_HOME_OFFICE))
    if any("equipment" in cat for cat in seen_categories):
        checklist_items.append(t(lang, CopyKey.CHECKLIST_EQUIPMENT))

    checklist_items.append(t(lang, CopyKey.CHECKLIST_GENERAL))
    return list(dict.fromkeys(checklist_items))  # Deduplicate while preserving order


def build_summary(state: TurnState) -> ReportSummary:
    """Builds a structured summary object from the final turn state."""
    lang = state.profile.data.get("preferences", {}).get("language", "auto")
    if lang == "auto":
        from app.i18n.microcopy import lang_detect

        lang = lang_detect(state.user_input)

    entries: list[ItemizedEntry] = []
    total = D(0)
    for cat, res in (state.calc_results or {}).items():
        if amt := res.get("amount_eur"):
            total += amt
            entries.append(
                ItemizedEntry(
                    category=cat,
                    amount_eur=fmt_eur(amt),
                    raw_amount=str(amt),
                    details={"year": res.get("year")},
                    caps_applied=res.get("caps_applied", []),
                )
            )

    content_to_hash = f"{state.correlation_id}{total}{''.join(state.citations)}"
    content_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:12]

    return ReportSummary(
        user_id=state.user_id,
        turn_id=state.correlation_id,
        created_ms=int(time.time() * 1000),
        profile_version=state.profile.version,
        language=lang,
        disclaimer=state.disclaimer,
        citations=state.citations,
        rules_used=state.trace.rules_used,
        itemization=entries,
        totals_eur=fmt_eur(total),
        checklist=build_receipts_checklist(entries, lang),
        hash=content_hash,
    )
