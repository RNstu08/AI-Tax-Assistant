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
    return {"amount_eur": quantize_eur(per_day * D(eligible_days))}


def calc_home_office(year: int, home_office_days: int) -> CalcResult:
    c = CONST[year]["home_office"]
    amount = quantize_eur(D(home_office_days) * c["per_day"])
    caps = []
    if amount > c["annual_cap"]:
        amount, caps = c["annual_cap"], ["annual_cap"]
    return {"amount_eur": amount, "caps_applied": caps}


def calc_equipment_item(
    year: int, amount_gross_eur: Decimal, purchase_date: date, has_receipt: bool
) -> CalcResult:
    c = CONST[year]["equipment"]
    if amount_gross_eur <= c["gwg_gross_threshold"]:
        return {
            "amount_eur": quantize_eur(amount_gross_eur),
            "breakdown": {"method": "immediate_expense"},
        }

    useful_life, months_owned = 3, 13 - purchase_date.month
    depreciation = quantize_eur((amount_gross_eur / D(useful_life)) * (D(months_owned) / D(12)))
    return {"amount_eur": depreciation, "breakdown": {"method": "straight_line_afa"}}
