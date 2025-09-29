from __future__ import annotations

import json
from pathlib import Path


class RulesService:
    def __init__(self, index_path: str = ".data/rules_index.json"):
        if not Path(index_path).exists():
            from app.knowledge.ingest import build_index

            build_index()
        with open(index_path, encoding="utf-8") as f:
            self._rules = json.load(f)

    def search(self, query: str = "", year: int | None = None) -> list[dict]:
        q = query.lower().strip()
        results = self._rules
        if year:
            results = [r for r in results if r.get("year") == year]
        if q:
            results = [
                r
                for r in results
                if q in r.get("title", "").lower() or q in r.get("summary", "").lower()
            ]
        return results
