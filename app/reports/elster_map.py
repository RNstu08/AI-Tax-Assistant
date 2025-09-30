from __future__ import annotations

# These codes are placeholders representative of Anlage N concepts.
ELSTER_FIELD_MAP: dict[str, str] = {
    "commuting": "anlagen.n.entfernungspauschale",
    "home_office": "anlagen.n.homeofficepauschale",
    "equipment_item_total": "anlagen.n.arbeitsmittel.pauschbetrag",
}


def get_field_code(category: str) -> str | None:
    """Gets the ELSTER-style field code for a given internal category."""
    return ELSTER_FIELD_MAP.get(category)
