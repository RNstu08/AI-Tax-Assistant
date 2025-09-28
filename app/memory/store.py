from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProfileSnapshot:
    """Immutable snapshot of a user's profile at a specific version."""

    version: int
    data: dict[str, Any] = field(default_factory=dict)


class ProfileStore:
    """Interface for persistent user profile storage. Stubbed for PR1."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def get_profile(self, user_id: str) -> ProfileSnapshot:
        """Returns the current profile snapshot. For now, a dummy empty profile."""
        return ProfileSnapshot(version=1, data={})
