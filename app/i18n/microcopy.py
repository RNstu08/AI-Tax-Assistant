from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.orchestrator.models import TurnState


def lang_detect(text: str) -> str:
    """A simple heuristic to detect German based on common words or characters."""
    t = (text or "").lower()
    if re.search(r"[äöüß]|(der|die|das|und|ist|nicht|steuer|tage|kilometer)\b", t):
        return "de"
    return "en"


def resolve_language(state: TurnState) -> str:
    """Determines the language for the turn, prioritizing user preference."""
    pref = state.profile.data.get("preferences", {}).get("language", "auto")
    if pref in ("en", "de"):
        return pref
    return lang_detect(state.user_input)


class CopyKey(str, Enum):
    # General App
    DISCLAIMER = "disclaimer"
    ESTIMATED_AMOUNTS = "estimated_amounts"
    # PDF Report
    PDF_TITLE = "pdf_title"
    PDF_TOTAL = "pdf_total"
    PDF_CHECKLIST = "pdf_checklist"
    # Adding missing table keys
    TABLE_CATEGORY = "table_category"
    TABLE_AMOUNT = "table_amount"
    TABLE_CAPS = "table_caps"
    TABLE_YEAR = "table_year"
    # UI Components
    SETTINGS_TITLE = "settings_title"
    LANGUAGE = "language"
    SAVE_SETTINGS = "save_settings"
    SETTINGS_SAVED = "settings_saved"
    RULES_BROWSER_TITLE = "rules_browser_title"
    SEARCH_RULES = "search_rules"
    YEAR_FILTER = "year_filter"
    # Checklist Items
    CHECKLIST_COMMUTING = "checklist_commuting"
    CHECKLIST_HOME_OFFICE = "checklist_home_office"
    CHECKLIST_EQUIPMENT = "checklist_equipment"
    CHECKLIST_GENERAL = "checklist_general"
    DISTANCE_UNIT = "distance_unit"
    CONSENT_OCR = "consent_ocr"
    RETENTION_TITLE = "retention_title"
    RETENTION_ATTACHMENTS_DAYS = "retention_attachments_days"
    RETENTION_EVIDENCE_DAYS = "retention_evidence_days"
    MAINTENANCE_TITLE = "maintenance_title"
    RUN_CLEANUP = "run_cleanup"


MC: dict[str, dict[CopyKey, str]] = {
    "en": {
        CopyKey.DISCLAIMER: (
            "Informational only; not tax advice. Please verify with official guidance."
        ),
        CopyKey.ESTIMATED_AMOUNTS: "Estimated Amounts",
        CopyKey.PDF_TITLE: ("DE Tax Assistant — Itemized Summary"),
        CopyKey.PDF_TOTAL: "Total: {amount}",
        CopyKey.PDF_CHECKLIST: "Receipts & Evidence Checklist",
        # Add missing table translations
        CopyKey.TABLE_CATEGORY: "Category",
        CopyKey.TABLE_AMOUNT: "Amount",
        CopyKey.TABLE_CAPS: "Caps",
        CopyKey.TABLE_YEAR: "Year",
        CopyKey.SETTINGS_TITLE: "Settings",
        CopyKey.LANGUAGE: "Language",
        CopyKey.SAVE_SETTINGS: "Save Settings",
        CopyKey.SETTINGS_SAVED: "Settings saved.",
        CopyKey.RULES_BROWSER_TITLE: "Rule Browser",
        CopyKey.SEARCH_RULES: "Search rules...",
        CopyKey.YEAR_FILTER: "Filter by year",
        CopyKey.CHECKLIST_COMMUTING: ("Commuting documents (tickets, logbook)"),
        CopyKey.CHECKLIST_HOME_OFFICE: "Home office days log",
        CopyKey.CHECKLIST_EQUIPMENT: "Equipment invoices/receipts",
        CopyKey.CHECKLIST_GENERAL: ("Keep all records for your final tax declaration."),
        CopyKey.DISTANCE_UNIT: "Distance Unit",
        CopyKey.CONSENT_OCR: ("Allow processing of uploaded receipts (OCR)"),
        CopyKey.RETENTION_TITLE: ("Data Retention (in days, 0 = keep forever)"),
        CopyKey.RETENTION_ATTACHMENTS_DAYS: "Attachments",
        CopyKey.RETENTION_EVIDENCE_DAYS: "Audit Logs",
        CopyKey.MAINTENANCE_TITLE: "Maintenance",
        CopyKey.RUN_CLEANUP: "Run Retention Cleanup",
    },
    "de": {
        CopyKey.DISCLAIMER: (
            "Nur zu Informationszwecken; keine Steuerberatung. "
            "Bitte mit offiziellen Quellen prüfen."
        ),
        CopyKey.ESTIMATED_AMOUNTS: "Geschätzte Beträge",
        CopyKey.PDF_TITLE: ("DE Steuer-Assistent — Aufgliederte Zusammenfassung"),
        CopyKey.PDF_TOTAL: "Summe: {amount}",
        CopyKey.PDF_CHECKLIST: "Beleg- und Nachweisliste",
        # Add missing table translations
        CopyKey.TABLE_CATEGORY: "Kategorie",
        CopyKey.TABLE_AMOUNT: "Betrag",
        CopyKey.TABLE_CAPS: "Kappungen",
        CopyKey.TABLE_YEAR: "Jahr",
        CopyKey.SETTINGS_TITLE: "Einstellungen",
        CopyKey.LANGUAGE: "Sprache",
        CopyKey.SAVE_SETTINGS: "Einstellungen speichern",
        CopyKey.SETTINGS_SAVED: "Einstellungen gespeichert.",
        CopyKey.RULES_BROWSER_TITLE: "Regel-Browser",
        CopyKey.SEARCH_RULES: "Regeln durchsuchen...",
        CopyKey.YEAR_FILTER: "Nach Jahr filtern",
        CopyKey.CHECKLIST_COMMUTING: ("Pauschale für Fahrtkosten (Fahrkarten, Fahrtenbuch)"),
        CopyKey.CHECKLIST_HOME_OFFICE: "Nachweis der Home-Office-Tage",
        CopyKey.CHECKLIST_EQUIPMENT: "Rechnungen/Belege für Arbeitsmittel",
        CopyKey.CHECKLIST_GENERAL: ("Bewahren Sie alle Unterlagen für Ihre Steuererklärung auf."),
        CopyKey.DISTANCE_UNIT: "Entfernungseinheit",
        CopyKey.CONSENT_OCR: ("Verarbeitung von Belegen erlauben (OCR)"),
        CopyKey.RETENTION_TITLE: ("Aufbewahrungsfristen (in Tagen, 0 = unbegrenzt)"),
        CopyKey.RETENTION_ATTACHMENTS_DAYS: "Anhänge",
        CopyKey.RETENTION_EVIDENCE_DAYS: "Prüfprotokolle",
        CopyKey.MAINTENANCE_TITLE: "Wartung",
        CopyKey.RUN_CLEANUP: "Aufbewahrungsbereinigung ausführen",
    },
}

# MC: dict[str, dict[CopyKey, str]] = {
#     "en": {
#         CopyKey.DISCLAIMER: (
#         "Informational only; not tax advice. Please verify with official guidance."
#     ),
#         CopyKey.ESTIMATED_AMOUNTS: "Estimated Amounts",
#         CopyKey.PDF_TITLE: "DE Tax Assistant — Itemized Summary",
#         CopyKey.PDF_TOTAL: "Total: {amount}",
#         CopyKey.PDF_CHECKLIST: "Receipts & Evidence Checklist",
#         # Add missing table translations
#         CopyKey.TABLE_CATEGORY: "Category",
#         CopyKey.TABLE_AMOUNT: "Amount",
#         CopyKey.TABLE_CAPS: "Caps",
#         CopyKey.TABLE_YEAR: "Year",
#         CopyKey.SETTINGS_TITLE: "Settings",
#         CopyKey.LANGUAGE: "Language",
#         CopyKey.SAVE_SETTINGS: "Save Settings",
#         CopyKey.SETTINGS_SAVED: "Settings saved.",
#         CopyKey.RULES_BROWSER_TITLE: "Rule Browser",
#         CopyKey.SEARCH_RULES: "Search rules...",
#         CopyKey.YEAR_FILTER: "Filter by year",
#         CopyKey.CHECKLIST_COMMUTING: "Commuting documents (tickets, logbook)",
#         CopyKey.CHECKLIST_HOME_OFFICE: "Home office days log",
#         CopyKey.CHECKLIST_EQUIPMENT: "Equipment invoices/receipts",
#         CopyKey.CHECKLIST_GENERAL: "Keep all records for your final tax declaration.",
#         CopyKey.DISTANCE_UNIT: "Distance Unit",
#         CopyKey.CONSENT_OCR: "Allow processing of uploaded receipts (OCR)",
#         CopyKey.RETENTION_TITLE: "Data Retention (in days, 0 = keep forever)",
#         CopyKey.MAINTENANCE_TITLE: "Maintenance",
#         CopyKey.RUN_CLEANUP: "Run Retention Cleanup",
#     },
#     "de": {
#         CopyKey.DISCLAIMER: (
#         "Nur zu Informationszwecken; keine Steuerberatung. "
#         "Bitte mit offiziellen Quellen prüfen."
#     ),
#         CopyKey.ESTIMATED_AMOUNTS: "Geschätzte Beträge",
#         CopyKey.PDF_TITLE: "DE Steuer-Assistent — Aufgliederte Zusammenfassung",
#         CopyKey.PDF_TOTAL: "Summe: {amount}",
#         CopyKey.PDF_CHECKLIST: "Beleg- und Nachweisliste",
#         # Add missing table translations
#         CopyKey.TABLE_CATEGORY: "Kategorie",
#         CopyKey.TABLE_AMOUNT: "Betrag",
#         CopyKey.TABLE_CAPS: "Kappungen",
#         CopyKey.TABLE_YEAR: "Jahr",
#         CopyKey.SETTINGS_TITLE: "Einstellungen",
#         CopyKey.LANGUAGE: "Sprache",
#         CopyKey.SAVE_SETTINGS: "Einstellungen speichern",
#         CopyKey.SETTINGS_SAVED: "Einstellungen gespeichert.",
#         CopyKey.RULES_BROWSER_TITLE: "Regel-Browser",
#         CopyKey.SEARCH_RULES: "Regeln durchsuchen...",
#         CopyKey.YEAR_FILTER: "Nach Jahr filtern",
#         CopyKey.CHECKLIST_COMMUTING: "Pauschale für Fahrtkosten (Fahrkarten, Fahrtenbuch)",
#         CopyKey.CHECKLIST_HOME_OFFICE: "Nachweis der Home-Office-Tage",
#         CopyKey.CHECKLIST_EQUIPMENT: "Rechnungen/Belege für Arbeitsmittel",
#         CopyKey.CHECKLIST_GENERAL: "Bewahren Sie alle Unterlagen für Ihre Steuererklärung auf.",
#         CopyKey.DISTANCE_UNIT: "Entfernungseinheit",
#         CopyKey.CONSENT_OCR: "Verarbeitung von Belegen erlauben (OCR)",
#         CopyKey.RETENTION_TITLE: "Aufbewahrungsfristen (in Tagen, 0 = unbegrenzt)",
#         CopyKey.MAINTENANCE_TITLE: "Wartung",
#         CopyKey.RUN_CLEANUP: "Aufbewahrungsbereinigung ausführen",
#     },
# }


def t(lang: str, key: CopyKey, **kwargs: Any) -> str:
    """A simple, type-safe translation function."""
    table = MC.get(lang, MC["en"])
    s = table.get(key, key.value)
    try:
        return s.format(**kwargs)
    except KeyError:
        return s
