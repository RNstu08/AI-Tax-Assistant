from __future__ import annotations

import re
from enum import Enum
from typing import Any


def lang_detect(text: str) -> str:
    """A simple heuristic to detect German based on common words or characters."""
    t = (text or "").lower()
    if re.search(r"[äöüß]|(der|die|das|und|ist|nicht|steuer|tage|kilometer)\b", t):
        return "de"
    return "en"


# Define all valid keys in one place using an Enum
class CopyKey(str, Enum):
    PDF_TITLE = "pdf_title"
    PDF_TOTAL = "pdf_total"
    PDF_CHECKLIST = "pdf_checklist"
    PDF_DISCLAIMER = "pdf_disclaimer"
    TABLE_CATEGORY = "table_category"
    TABLE_AMOUNT = "table_amount"
    TABLE_CAPS = "table_caps"
    CHECKLIST_COMMUTING = "checklist_commuting"
    CHECKLIST_HOME_OFFICE = "checklist_home_office"
    CHECKLIST_EQUIPMENT = "checklist_equipment"
    CHECKLIST_GENERAL = "checklist_general"
    SETTINGS_TITLE = "settings_title"
    LANGUAGE = "language"
    RULES_BROWSER_TITLE = "rules_browser_title"
    SEARCH = "search"
    YEAR_FILTER = "year_filter"


# Use the Enum members as keys for type safety and to avoid repetition
MC: dict[str, dict[CopyKey, str]] = {
    "en": {
        CopyKey.PDF_TITLE: "DE Tax Assistant — Itemized Summary",
        CopyKey.PDF_TOTAL: "Total: {amount}",
        CopyKey.PDF_CHECKLIST: "Receipts & Evidence Checklist",
        CopyKey.PDF_DISCLAIMER: "Disclaimer",
        CopyKey.TABLE_CATEGORY: "Category",
        CopyKey.TABLE_AMOUNT: "Amount",
        CopyKey.TABLE_CAPS: "Caps",
        CopyKey.CHECKLIST_COMMUTING: "Commuting documents (tickets, logbook)",
        CopyKey.CHECKLIST_HOME_OFFICE: "Home office days log",
        CopyKey.CHECKLIST_EQUIPMENT: "Equipment invoices/receipts",
        CopyKey.CHECKLIST_GENERAL: "Keep all records for your final tax declaration.",
        CopyKey.SETTINGS_TITLE: "Settings",
        CopyKey.LANGUAGE: "Language",
        CopyKey.RULES_BROWSER_TITLE: "Rule Browser",
        CopyKey.SEARCH: "Search",
        CopyKey.YEAR_FILTER: "Year filter (optional)",
    },
    "de": {
        CopyKey.PDF_TITLE: "DE Steuer-Assistent — Aufgliederte Zusammenfassung",
        CopyKey.PDF_TOTAL: "Summe: {amount}",
        CopyKey.PDF_CHECKLIST: "Beleg- und Nachweisliste",
        CopyKey.PDF_DISCLAIMER: "Hinweis",
        CopyKey.TABLE_CATEGORY: "Kategorie",
        CopyKey.TABLE_AMOUNT: "Betrag",
        CopyKey.TABLE_CAPS: "Kappungen",
        CopyKey.CHECKLIST_COMMUTING: "Pauschale für Fahrtkosten (Fahrkarten, Fahrtenbuch)",
        CopyKey.CHECKLIST_HOME_OFFICE: "Nachweis der Home-Office-Tage",
        CopyKey.CHECKLIST_EQUIPMENT: "Rechnungen/Belege für Arbeitsmittel",
        CopyKey.CHECKLIST_GENERAL: "Bewahren Sie alle Unterlagen für Ihre Steuererklärung auf.",
        CopyKey.SETTINGS_TITLE: "Einstellungen",
        CopyKey.LANGUAGE: "Sprache",
        CopyKey.RULES_BROWSER_TITLE: "Regel-Browser",
        CopyKey.SEARCH: "Suche",
        CopyKey.YEAR_FILTER: "Jahr filtern (optional)",
    },
}


# Update the function to accept a CopyKey enum member
def t(lang: str, key: CopyKey, default: str | None = None, **kwargs: Any) -> str:
    """A simple, type-safe translation function."""
    table = MC.get(lang, MC["en"])
    # The default is now the enum's value itself (e.g., "pdf_title")
    s = table.get(key, default or key.value)
    try:
        return s.format(**kwargs)
    except KeyError:
        return s
