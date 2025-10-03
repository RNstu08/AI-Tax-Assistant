from __future__ import annotations

from pathlib import Path

import yaml

from app.orchestrator.models import TurnState


def load_scenarios(dir_path: str | Path) -> list[dict]:
    """Loads all YAML scenario files from a directory."""
    scenarios = []
    for p in sorted(Path(dir_path).glob("*.yml")):
        with open(p, encoding="utf-8") as f:
            scenarios.append(yaml.safe_load(f))
    return scenarios


def assert_expectations(result: TurnState, expect: dict):
    """Runs assertions against a TurnState based on expectations from a YAML file."""
    if "rule_ids_any" in expect:
        hit_ids = {h.rule_id for h in result.rule_hits}
        assert any(rid in hit_ids for rid in expect["rule_ids_any"])

    if "actions_include" in expect:
        action_kinds = {p.kind for p in result.proposed_actions}
        assert all(kind in action_kinds for kind in expect["actions_include"])

    if "category_hint" in expect:
        actual = result.category_hint or ""
        expected = expect["category_hint"] or ""
        print("category_hint actual:", repr(actual), "expected:", repr(expected))  # TEMP debug
        assert actual.strip().lower() == expected.strip().lower()

    if "is_out_of_scope" in expect:
        assert any(e.code == "out_of_scope" for e in result.errors)
