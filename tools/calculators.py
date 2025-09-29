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
    return {"amount_eur": total}


def calc_home_office(year: int, home_office_days: int) -> CalcResult:
    c = CONST[year]["home_office"]
    amount = quantize_eur(D(home_office_days) * c["per_day"])
    caps_applied = []
    if amount > c["annual_cap"]:
        amount, caps_applied = c["annual_cap"], ["annual_cap"]
    return {"amount_eur": amount, "caps_applied": caps_applied}


def calc_equipment_item(
    year: int, amount_gross_eur: Decimal, purchase_date: date, has_receipt: bool
) -> CalcResult:
    c = CONST[year]["equipment"]
    assumptions = [] if has_receipt else ["receipt_missing"]
    if amount_gross_eur <= c["gwg_gross_threshold"]:
        return {
            "amount_eur": quantize_eur(amount_gross_eur),
            "breakdown": {"method": "immediate_expense"},  # FIX: Add breakdown key
            "inputs_used": {"amount_gross_eur": str(amount_gross_eur)},
        }

    useful_life_years = 3
    months_owned = 13 - purchase_date.month
    depreciation = quantize_eur(
        (amount_gross_eur / D(useful_life_years)) * (D(months_owned) / D(12))
    )
    return {
        "amount_eur": depreciation,
        "breakdown": {"method": "straight_line_afa"},  # FIX: Add breakdown key
        "inputs_used": {"amount_gross_eur": str(amount_gross_eur)},
        "assumptions": assumptions + [f"assumed_{useful_life_years}_year_life"],
    }
