from __future__ import annotations

import re
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


def fmt_eur(amount: Decimal) -> str:
    """Format a Decimal as a currency string, e.g., '€1,234.56'."""
    q = quantize_eur(amount)
    return f"€{q:,.2f}"


# Regex to find monetary values like €899 or 899,00 EUR
_EUR_PATTERN = re.compile(
    r"(\d{1,3}(?:[.,\s]\d{3})*|\d+)(?:[.,](\d{1,2}))?\s*(?:€|eur\b)",
    re.IGNORECASE,
)


def parse_eur_amounts(text: str) -> list[Decimal]:
    """Parse all EUR-like amounts from a string and return them as Decimals."""
    amounts: list[Decimal] = []
    for match in _EUR_PATTERN.finditer(text):
        whole = match.group(1).replace(".", "").replace(",", "").replace(" ", "")
        cents = match.group(2) or "00"
        amounts.append(quantize_eur(D(f"{whole}.{cents}")))
    return amounts
