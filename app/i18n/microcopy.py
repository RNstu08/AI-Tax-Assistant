from __future__ import annotations

import re


def lang_detect(text: str) -> str:
    """A simple heuristic to detect German based on common words or characters."""
    t = (text or "").lower()
    if re.search(r"[äöüß]|(der|die|das|und|ist|nicht|steuer|tage|kilometer)\b", t):
        return "de"
    return "en"


# Master dictionary for internationalization (i18n)
MC: dict[str, dict[str, str]] = {
    "en": {
        "pdf_title": "DE Tax Assistant — Itemized Summary",
        "pdf_total": "Total: {amount}",
        "pdf_checklist": "Receipts & Evidence Checklist",
        "pdf_disclaimer": "Disclaimer",
        "table_category": "Category",
        "table_amount": "Amount",
        "table_caps": "Caps",
        "checklist_commuting": "Commuting documents (tickets, logbook)",
        "checklist_home_office": "Home office days log",
        "checklist_equipment": "Equipment invoices/receipts",
        "checklist_general": "Keep all records for your final tax declaration.",
    },
    "de": {
        "pdf_title": "DE Steuer-Assistent — Aufgliederte Zusammenfassung",
        "pdf_total": "Summe: {amount}",
        "pdf_checklist": "Beleg- und Nachweisliste",
        "pdf_disclaimer": "Hinweis",
        "table_category": "Kategorie",
        "table_amount": "Betrag",
        "table_caps": "Kappungen",
        "checklist_commuting": "Pauschale für Fahrtkosten (Fahrkarten, Fahrtenbuch)",
        "checklist_home_office": "Nachweis der Home-Office-Tage",
        "checklist_equipment": "Rechnungen/Belege für Arbeitsmittel",
        "checklist_general": "Bewahren Sie alle Unterlagen für Ihre Steuererklärung auf.",
    },
}


def t(lang: str, key: str, default: str | None = None, **kwargs) -> str:
    """A simple translation function."""
    table = MC.get(lang, MC["en"])  # Default to English
    s = table.get(key, default or key)
    try:
        return s.format(**kwargs)
    except KeyError:
        return s
