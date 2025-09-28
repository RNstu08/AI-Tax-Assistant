from tools.calculators import calc_commute
from tools.money import D


def test_commute_basic():
    res = calc_commute(2025, D(30), 220, 100)
    assert res["amount_eur"] == D("1176.00")  # 9.80/day * 120 days


def test_commute_no_home_office():
    res = calc_commute(2024, D(15), 230, 0)
    assert res["amount_eur"] == D("1035.00")  # 4.50/day * 230 days
