from datetime import date

from tools.calculators import calc_equipment_item
from tools.money import D


def test_equipment_immediate_expense():
    res = calc_equipment_item(2024, D(899), date(2024, 5, 10), True)
    assert res["amount_eur"] == D("899.00")
    assert res["breakdown"]["method"] == "immediate_expense"


def test_equipment_depreciation():
    # 1500€ item bought in October -> 3 months of depreciation in first year
    # 1500 / 3 years = 500/year. 500 * (3/12) = 125
    res = calc_equipment_item(2025, D(1500), date(2025, 10, 1), True)
    assert res["amount_eur"] == D("125.00")
    assert res["breakdown"]["method"] == "straight_line_afa"
