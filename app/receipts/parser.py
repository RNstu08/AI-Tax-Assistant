from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from tools.money import D


@dataclass(frozen=True)
class ParsedItem:
    description: str
    quantity: int
    unit_price_eur: Decimal
    total_eur: Decimal


@dataclass(frozen=True)
class ParsedReceipt:
    vendor: str | None
    purchase_date: str | None
    items: list[ParsedItem]
    total_eur: Decimal | None


_ITEM_PATTERN = re.compile(
    r"(?P<qty>\d+)?\s*x?\s*(?P<desc>[\w\s.-]+?)\s+(?P<price>\d[\d.,]*)\s*€?", re.I
)
_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_receipt_text(text: str) -> ParsedReceipt:
    items: list[ParsedItem] = []
    for m in _ITEM_PATTERN.finditer(text):
        desc = m.group("desc").strip()
        # FIX: Explicitly ignore anything that looks like a date
        if _DATE_PATTERN.match(desc):
            continue

        try:
            qty = int(m.group("qty") or 1)
            price = D(m.group("price").replace(",", "."))
            items.append(
                ParsedItem(
                    description=desc,
                    quantity=qty,
                    unit_price_eur=price,
                    total_eur=qty * price,
                )
            )
        except (ValueError, TypeError):
            continue

    date_match = _DATE_PATTERN.search(text)
    vendor_match = re.search(r"Vendor:\s*(.*)", text)

    return ParsedReceipt(
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        purchase_date=date_match.group(1) if date_match else None,
        items=items,
        total_eur=sum((i.total_eur for i in items), D(0)),
    )
