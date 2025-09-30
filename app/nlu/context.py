from __future__ import annotations

import time
from typing import Any


class EntityMemory:
    """A simple, recency-based memory for entities mentioned in a conversation."""

    def __init__(self, entities: list[dict[str, Any]] | None = None) -> None:
        # Sort entities by timestamp on load, most recent first
        self.entities = sorted(entities or [], key=lambda x: x.get("ts", 0), reverse=True)
        self.now_ms = int(time.time() * 1000)

    @staticmethod
    def from_profile(data: dict) -> EntityMemory:
        """Loads the memory from a user profile dictionary."""
        return EntityMemory((data or {}).get("nlu_memory", {}).get("entities", []))

    def to_dict(self) -> dict:
        """Serializes the memory to a dictionary for saving to the profile."""
        return {"entities": self.entities[:20]}  # Persist the 20 most recent entities

    def remember(self, entity: dict[str, Any]) -> None:
        """Adds a new entity to the top of the memory stack."""
        entity["ts"] = self.now_ms
        self.entities.insert(0, entity)
        # Prune the memory to keep it from growing indefinitely
        self.entities = self.entities[:20]

    def resolve(self, text: str, kind_hint: str) -> dict[str, Any] | None:
        """
        Resolves simple pronouns ('it', 'one', 'same') to the most recent
        entity of a compatible kind.
        """
        text_lower = text.lower()
        # Check for common pronouns and references
        if any(p in text_lower for p in [" it", " them", " another one", "the same", "dasselbe"]):
            for entity in self.entities:
                if entity.get("kind") == kind_hint:
                    return entity
        return None
