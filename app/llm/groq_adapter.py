from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any

from groq import Groq


class GroqAdapter:
    """
    Groq client wrapper with an offline deterministic stub for CI/dev
    and live API calls when an API key is provided.
    """

    def __init__(self, api_key: str | None, timeout_s: float = 8.0) -> None:
        self.api_key = api_key
        # self.offline = True
        self.offline = not api_key
        if not self.offline:
            self.client = Groq(api_key=self.api_key, timeout=timeout_s)

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]

    def chat(self, model: str, messages: list[dict], temperature: float = 0.2) -> str:
        if self.offline:
            last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            # FIX: The 'h' variable was created but never used, so it has been removed.
            return f"[STUBBED RESPONSE for: '{last_user[:50]}...']"

        chat_completion = self.client.chat.completions.create(
            messages=messages, model=model, temperature=temperature
        )
        return chat_completion.choices[0].message.content or ""

    def json(self, model: str, messages: list[dict], temperature: float = 0.0) -> dict[str, Any]:
        if self.offline:
            last_user = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
            ).lower()
            print("OFFLINE ROUTER INPUT:", repr(last_user))  # DEBUG
            # TEMP TEST: Force all router outputs to be equipment
            hint = "equipment"
            print(
                "OFFLINE ROUTER RETURNING:",
                {"intent": "deduction", "category_hint": hint, "retrieval_query": last_user},
            )  # DEBUG
            return {"intent": "deduction", "category_hint": hint, "retrieval_query": last_user}
            if any(w in last_user for w in ["commute", "pendler"]):
                hint = "commuting"
            elif any(w in last_user for w in ["home office", "homeoffice"]):
                hint = "home_office"
            elif any(w in last_user for w in ["equipment", "laptop", "arbeitsmittel", "gekauft"]):
                hint = "equipment"
                print("Offline router keywords test:", last_user, "| Hint?", hint)
            else:
                hint = None
            return {"intent": "deduction", "category_hint": hint, "retrieval_query": last_user}

        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        try:
            response_text = chat_completion.choices[0].message.content or "{}"
            return json.loads(response_text)
        except (json.JSONDecodeError, IndexError):
            return {"intent": "error", "category_hint": None, "retrieval_query": ""}

    def stream(
        self,
        model: str,
        messages: list[dict],
        on_token: Callable[[str], None],
        temperature: float = 0.2,
    ) -> None:
        if self.offline:
            text = self.chat(model, messages, temperature)
            for i in range(0, len(text), 5):
                on_token(text[i : i + 5])
            return

        stream = self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            if token := chunk.choices[0].delta.content:
                on_token(token)
