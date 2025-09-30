from __future__ import annotations

import json
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from app.memory.store import ProfileStore
from app.orchestrator.models import TurnState
from app.reports.elster_map import get_field_code
from app.reports.summary import ReportSummary, build_summary


def _to_cents(amount_str: str) -> int:
    """Converts a string representation of a decimal to cents."""
    return int(Decimal(amount_str) * 100)


def build_elster_payload(
    summary: ReportSummary, include_categories: Iterable[str] | None = None
) -> dict[str, Any]:
    """Builds the ELSTER-style JSON payload from a report summary."""
    include = set(include_categories) if include_categories else None
    items = []
    for entry in summary.itemization:
        if include and entry.category not in include:
            continue
        if field_code := get_field_code(entry.category):
            items.append(
                {
                    "field_code": field_code,
                    "amount_cents": _to_cents(entry.raw_amount),
                    "year": entry.details.get("year"),
                }
            )
    return {
        "schema": "de.tax.assistant.elster.v1",
        "user_id": summary.user_id,
        "profile_version": summary.profile_version,
        "hash": summary.hash,
        "items": items,
    }


def export_json_and_log(
    user_id: str,
    state: TurnState,
    store: ProfileStore,
    include_categories: Iterable[str] | None = None,
) -> tuple[bytes, int]:
    """Generates the JSON file and logs an evidence event."""
    summary = build_summary(state)
    payload = build_elster_payload(summary, include_categories=include_categories)
    json_bytes = json.dumps(payload, indent=2).encode("utf-8")

    # In a future PR, we would log this action to the evidence table.
    return json_bytes, 0
