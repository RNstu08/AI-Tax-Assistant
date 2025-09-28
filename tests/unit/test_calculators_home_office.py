from tools.calculators import calc_home_office
from tools.money import D


def test_home_office_below_cap():
    res = calc_home_office(2024, 150)
    assert res["amount_eur"] == D("900.00")  # 150 * 6


def test_home_office_at_cap():
    res = calc_home_office(2025, 300)
    assert res["amount_eur"] == D("1260.00")  # Capped
    assert "annual_cap" in res["caps_applied"]
