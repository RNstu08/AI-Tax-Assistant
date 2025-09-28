from decimal import Decimal

from tools.money import D, quantize_eur


def test_decimal_conversion_and_quantize():
    assert quantize_eur(D("1.005")) == Decimal("1.01")
    assert quantize_eur(D(2)) == Decimal("2.00")
    assert quantize_eur(D(2.1)) == Decimal("2.10")
