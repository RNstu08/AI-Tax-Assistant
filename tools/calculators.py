from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TypedDict

from tools.constants import CONST
from tools.money import D, quantize_eur


class CalcResult(TypedDict, total=False):
    amount_eur: Decimal
    breakdown: dict
    inputs_used: dict
    constants: dict
    caps_applied: list[str]
    assumptions: list[str]
    needs: list[str]
    year: int


def _require_present(needs: list[str]) -> CalcResult:
    """Helper to return a result indicating missing data."""
    return {"amount_eur": D(0), "needs": needs}


def calc_commute(
    year: int, km_one_way: Decimal, work_days: int, home_office_days: int
) -> CalcResult:
    c = CONST[year]["commute"]
    eligible_days = max(work_days - home_office_days, 0)
    per_day = (
        min(km_one_way, D(20)) * c["rate_first_20"]
        + max(km_one_way - D(20), D(0)) * c["rate_after_20"]
    )
    total = quantize_eur(per_day * D(eligible_days))
    return {
        "amount_eur": total,
        "breakdown": {"per_day": str(per_day), "eligible_days": eligible_days},
        "inputs_used": {
            "km_one_way": str(km_one_way),
            "work_days": work_days,
            "home_office_days": home_office_days,
        },
        "constants": {k: str(v) for k, v in c.items()},
    }


def calc_home_office(year: int, home_office_days: int) -> CalcResult:
    c = CONST[year]["home_office"]
    amount = quantize_eur(D(home_office_days) * c["per_day"])
    caps_applied = []
    if amount > c["annual_cap"]:
        amount = c["annual_cap"]
        caps_applied.append("annual_cap")
    return {
        "amount_eur": amount,
        "breakdown": {"days_used": home_office_days},
        "inputs_used": {"home_office_days": home_office_days},
        "constants": {k: str(v) for k, v in c.items()},
        "caps_applied": caps_applied,
    }


def calc_equipment_item(
    year: int, amount_gross_eur: Decimal, purchase_date: date, has_receipt: bool
) -> CalcResult:
    c = CONST[year]["equipment"]
    assumptions = [] if has_receipt else ["receipt_missing"]
    if amount_gross_eur <= c["gwg_gross_threshold"]:
        return {
            "amount_eur": quantize_eur(amount_gross_eur),
            "breakdown": {"method": "immediate_expense"},
            "inputs_used": {
                "amount_gross_eur": str(amount_gross_eur),
                "purchase_date": purchase_date.isoformat(),
            },
            "constants": {k: str(v) for k, v in c.items()},
            "assumptions": assumptions,
        }
    # Simplified depreciation for items over the threshold (pro-rata for first year)
    useful_life_years = 3  # Assume 3 years for IT equipment
    months_owned = 13 - purchase_date.month
    depreciation = quantize_eur(amount_gross_eur / useful_life_years * (months_owned / 12))
    return {
        "amount_eur": depreciation,
        "breakdown": {"method": "straight_line_afa", "months_owned": months_owned},
        "inputs_used": {
            "amount_gross_eur": str(amount_gross_eur),
            "purchase_date": purchase_date.isoformat(),
        },
        "constants": {k: str(v) for k, v in c.items()},
        "assumptions": assumptions + [f"assumed_{useful_life_years}_year_life"],
    }
