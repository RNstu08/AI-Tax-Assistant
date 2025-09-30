from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RulesService:
    """A simple, cached service to search the rules index."""

    _rules: list[dict[str, Any]]

    def __init__(self, index_path: str = ".data/rules_index.json"):
        if not Path(index_path).exists():
            from app.knowledge.ingest import build_index

            build_index()
        with open(index_path, encoding="utf-8") as f:
            self._rules = json.load(f)

    def search(self, query: str = "", year: int | None = None) -> list[dict[str, Any]]:
        query_lower = query.lower().strip()
        results = self._rules
        if year:
            results = [r for r in results if r.get("year") == year]
        if query_lower:
            results = [
                r
                for r in results
                if query_lower in r.get("title", "").lower()
                or query_lower in r.get("summary", "").lower()
            ]
        return results
