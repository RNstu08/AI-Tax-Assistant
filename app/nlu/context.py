from __future__ import annotations

import time


class EntityMemory:
    def __init__(self, entities: list[dict] | None = None):
        self.entities = sorted(entities or [], key=lambda x: x.get("ts", 0), reverse=True)
        self.now_ms = int(time.time() * 1000)

    @staticmethod
    def from_profile(data: dict) -> EntityMemory:
        return EntityMemory((data or {}).get("nlu_memory", {}).get("entities", []))

    def to_dict(self) -> dict:
        return {"entities": self.entities[:20]}  # Persist the last 20 entities

    def remember(self, entity: dict) -> None:
        entity["ts"] = self.now_ms
        self.entities.insert(0, entity)
        self.entities = self.entities[:50]

    def resolve(self, text: str, kind_hint: str) -> dict | None:
        if any(p in text.lower() for p in ["it", "them", "same one", "dasselbe"]):
            for entity in self.entities:
                if entity.get("kind") == kind_hint:
                    return entity
        return None
