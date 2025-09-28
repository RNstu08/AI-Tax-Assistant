from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from typing import Any


class GroqAdapter:
    """
    Groq client wrapper with an offline deterministic stub for CI and dev.
    The live API calls are stubbed out but structured for future implementation.
    """

    def __init__(self, api_key: str | None, timeout_s: float = 8.0) -> None:
        self.api_key = api_key
        self.offline = not api_key
        self.timeout_s = timeout_s

    def _hash(self, text: str) -> str:
        """Creates a short, deterministic hash of an input string."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]

    def chat(self, model: str, messages: list[dict], temperature: float = 0.0) -> str:
        """Offline: return deterministic canned text with a hash of the input."""
        if self.offline:
            last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            h = self._hash(last_user)
            return f"[stub:{model}] Response for: '{last_user[:50]}...' :: {h}"
        raise NotImplementedError("Live Groq chat not implemented in PR3.")

    def json(self, model: str, messages: list[dict], temperature: float = 0.0) -> dict[str, Any]:
        """Offline: return deterministic JSON for routing/extraction tasks."""
        if self.offline:
            last_user = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
            ).lower()
            # Simple, deterministic intent classification for our stubs
            intent = "deduction"
            category_hint = None
            if any(w in last_user for w in ["commute", "pendler"]):
                category_hint = "commuting"
            elif any(w in last_user for w in ["home office", "homeoffice"]):
                category_hint = "home_office"
            return {
                "intent": intent,
                "category_hint": category_hint,
                "retrieval_query": last_user,
            }
        raise NotImplementedError("Live Groq json not implemented in PR3.")

    def stream(
        self,
        model: str,
        messages: list[dict],
        on_token: Callable[[str], None],
        temperature: float = 0.2,
    ):
        """Offline: stream out the stub chat response in chunks."""
        if self.offline:
            text = self.chat(model, messages, temperature)
            for i in range(0, len(text), 10):
                on_token(text[i : i + 10])
                time.sleep(0.01)  # Simulate network latency
            return
        raise NotImplementedError("Live Groq stream not implemented in PR3.")
