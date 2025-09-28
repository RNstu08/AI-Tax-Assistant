from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext

# Set precision for Decimal operations
getcontext().prec = 28
CENT = Decimal("0.01")


def D(x: int | float | str | Decimal) -> Decimal:
    """Safely convert any numeric type to Decimal."""
    return Decimal(str(x)) if isinstance(x, float) else Decimal(x)


def quantize_eur(amount: Decimal) -> Decimal:
    """Quantize a Decimal value to two decimal places for euros."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
