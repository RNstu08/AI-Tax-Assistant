from __future__ import annotations

import re

DANGEROUS_PATTERNS = [
    r"ignore (previous|all) instructions",
    r"system prompt",
    r"you must output",
]


def sanitize_snippet(text: str, max_len: int = 480) -> str:
    """Remove instruction-like phrases and truncate."""
    txt = text
    for pat in DANGEROUS_PATTERNS:
        txt = re.sub(pat, "[redacted]", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > max_len:
        txt = txt[: max_len - 3] + "..."
    return txt
