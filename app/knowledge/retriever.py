from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

from .models import RuleHit
from .sanitize import sanitize_snippet
from .synonyms import SYNONYMS


@dataclass(frozen=True)
class IndexedRule:
    rule_id: str
    year: int
    title: str
    category: str  # Storing as generic str here
    snippet: str
    required_data_points: list[str]
    calculator_binding: str
    search_terms: frozenset[str]


class InMemoryRetriever:
    def __init__(self, index_path: str | Path = ".data/rules_index.json") -> None:
        path = Path(index_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules index not found at {path}. Run ingestion first.")
        with open(path, encoding="utf-8") as f:
            raw_rules = json.load(f)
        self._rules: list[IndexedRule] = []
        for r in raw_rules:
            terms = self._expand_terms(f'{r["title"]} {r["summary"]}')
            self._rules.append(
                IndexedRule(
                    rule_id=r["rule_id"],
                    year=int(r["year"]),
                    title=r["title"],
                    category=r["category"],
                    snippet=sanitize_snippet(r["snippet"]),
                    required_data_points=r["required_data_points"],
                    calculator_binding=r["calculator_binding"],
                    search_terms=frozenset(terms),
                )
            )

    def _expand_terms(self, text: str) -> set[str]:
        tokens = set(text.lower().split())
        expanded = set(tokens)
        for key, syns in SYNONYMS.items():
            if key in tokens or any(s in text.lower() for s in syns):
                expanded.update(syns)
        return expanded

    def search(self, query: str, year: int, k: int = 3) -> list[RuleHit]:
        q_tokens = self._expand_terms(query)
        candidates: list[tuple[float, IndexedRule]] = []
        for rule in self._rules:
            if rule.year != year:
                continue
            overlap = len(q_tokens.intersection(rule.search_terms))
            fuzz_boost = fuzz.partial_ratio(query.lower(), " ".join(rule.search_terms)) / 100.0
            score = (overlap * 1.0) + (fuzz_boost * 0.5)
            if score >= 1.0:
                candidates.append((score, rule))
            # if score > 0:
            #     candidates.append((score, rule))

        candidates.sort(key=lambda x: x[0], reverse=True)

        return [
            RuleHit(
                rule_id=rule.rule_id,
                year=rule.year,
                title=rule.title,
                # Ignore this line as we know the str is a valid Category
                category=rule.category,  # type: ignore
                snippet=rule.snippet,
                required_data_points=rule.required_data_points,
                calculator_binding=rule.calculator_binding,
                score=round(score, 4),
            )
            for score, rule in candidates[:k]
        ]
