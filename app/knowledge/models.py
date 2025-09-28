from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Category = Literal["commuting", "home_office", "equipment", "donations"]


class Rule(BaseModel):
    """
    Canonical rule record loaded from YAML, strictly validated.
    - rule_id must be stable and unique per year.
    - required_data_points lists keys needed by calculators.
    - snippet is a 1-3 sentence summary for retrieval.
    """

    rule_id: str = Field(..., pattern=r"^de_(2024|2025)_[a-z0-9_]+$")
    year: int = Field(..., ge=2024, le=2025)
    country: Literal["DE"]
    title: str
    category: Category
    summary: str
    snippet: str
    required_data_points: list[str] = Field(default_factory=list)
    calculator_binding: str = Field(
        ..., pattern=r"^calc_(commute|home_office|equipment_item|donations)$"
    )

    @field_validator("year")
    @classmethod
    def year_matches_rule_id(cls, v: int, info):
        rid: str = info.data.get("rule_id", "")
        if str(v) not in rid:
            raise ValueError(f"year {v} does not appear in rule_id {rid}")
        return v


class RuleHit(BaseModel):
    """Retrieval hit, safe to surface to the Reasoner and UI."""

    rule_id: str
    year: int
    title: str
    category: Category
    snippet: str
    required_data_points: list[str]
    calculator_binding: str
    score: float
