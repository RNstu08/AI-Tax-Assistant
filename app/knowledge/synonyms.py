from __future__ import annotations

# Curated bilingual synonyms for our four categories.
SYNONYMS: dict[str, list[str]] = {
    # Commuting
    "commute": [
        "commute",
        "commuting",
        "distance",
        "km",
        "pendeln",
        "pendler",
        "pendlerpauschale",
        "entfernungspauschale",
        "fahrtkosten",
        "weg zur arbeit",
    ],
    # Home office
    "home_office": [
        "home office",
        "home-office",
        "remote",
        "work from home",
        "wfh",
        "homeoffice",
        "homeoffice pauschale",
        "arbeitszimmer pauschale",
    ],
    # Equipment
    "equipment": [
        "equipment",
        "tools",
        "work equipment",
        "laptop",
        "computer",
        "monitor",
        "chair",
        "desk",
        "drucker",
        "arbeitsmittel",
        "beruflich",
    ],
    # Donations
    "donations": [
        "donation",
        "donations",
        "charity",
        "spende",
        "spenden",
        "gemeinnützig",
        "sonderausgaben",
        "verein",
    ],
}
