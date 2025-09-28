from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SafetyPolicy:
    """Typed representation of the safety policy."""

    scope_country: str
    scope_years: list[int]
    scope_persona: str
    claims_require_citation: bool
    questions_max_per_turn: int
    pii_disallow: list[str]


def load_policy(path: str | Path = "app/safety/policy.yaml") -> SafetyPolicy:
    """Loads and validates the safety policy from a YAML file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Safety policy not found: {p}")
    with open(p, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return SafetyPolicy(
        scope_country=(raw.get("scope") or {}).get("country", "DE"),
        scope_years=(raw.get("scope") or {}).get("years", [2024, 2025]),
        scope_persona=(raw.get("scope") or {}).get("persona", "employee"),
        claims_require_citation=(raw.get("claims") or {}).get("require_citation", True),
        questions_max_per_turn=(raw.get("questions") or {}).get("max_per_turn", 2),
        pii_disallow=(raw.get("pii") or {}).get("disallow", []),
    )
