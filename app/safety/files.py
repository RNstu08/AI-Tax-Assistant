from __future__ import annotations

import re
from hashlib import sha256

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_BYTES = 7 * 1024 * 1024  # 7 MB


def sanitize_filename(name: str) -> str:
    """Strips dangerous characters, replaces spaces, and provides a default if empty."""
    name = name.replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)

    # FIX: If sanitization results in an empty or dot-only name, provide a safe default.
    if not name or name.strip(" .") == "":
        return "uploaded_file"

    return name[:80]


def validate_file(content_type: str | None, size_bytes: int) -> tuple[bool, str]:
    """Checks if a file's type and size are within our policy limits."""
    if size_bytes > MAX_BYTES:
        return False, f"File too large (>{MAX_BYTES / 1024 / 1024:.0f} MB)"
    if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
        return False, f"Unsupported file type: {content_type}"
    return True, ""


def sha256_hex(data: bytes) -> str:
    """Computes the SHA-256 hash of a byte string."""
    return sha256(data).hexdigest()
