from __future__ import annotations

from decimal import Decimal
from typing import TypedDict


class CalcResult(TypedDict, total=False):
    amount_eur: Decimal
    # Other fields will be added in PR5


def calc_commute(year: int, km_one_way: Decimal, work_days: int) -> CalcResult:
    """Stub signature for Pendlerpauschale (to be implemented in PR5)."""
    raise NotImplementedError
