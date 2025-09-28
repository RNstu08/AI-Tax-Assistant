from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import yaml

from .models import Rule


def load_rules_from_dir(root: str | Path) -> list[Rule]:
    """
    Load and validate all YAML rule files under a directory tree.
    Expects structure: knowledge/rules/de/{2024,2025}/*.yml
    """
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"Rules directory not found: {root}")

    rules: list[Rule] = []
    for path in root.rglob("*.yml"):
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        try:
            rule = Rule(**raw)
        except Exception as e:
            raise ValueError(f"Invalid rule at {path}: {e}") from e
        rules.append(rule)

    # Validate uniqueness of rule_id
    seen_ids = set()
    for r in rules:
        if r.rule_id in seen_ids:
            raise ValueError(f"Duplicate rule_id detected: {r.rule_id}")
        seen_ids.add(r.rule_id)

    return rules


def ensure_data_dir(path: str | Path = ".data") -> None:
    """Create the .data directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def write_rules_index_json(rules: Iterable[Rule], out_path: str | Path) -> None:
    """Write a normalized JSON index that the retriever can load quickly."""
    ensure_data_dir(Path(out_path).parent)
    payload = [r.model_dump() for r in rules]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
