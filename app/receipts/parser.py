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


def parse_receipt_text(text: str) -> ParsedReceipt:
    items: list[ParsedItem] = []
    # Simplified parsing for demo
    for m in _ITEM_PATTERN.finditer(text):
        qty = int(m.group("qty") or 1)
        price = D(m.group("price").replace(",", "."))
        items.append(
            ParsedItem(
                description=m.group("desc").strip(),
                quantity=qty,
                unit_price_eur=price,
                total_eur=qty * price,
            )
        )

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    vendor_match = re.search(r"Vendor:\s*(.*)", text)

    return ParsedReceipt(
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        purchase_date=date_match.group(1) if date_match else None,
        items=items,
        total_eur=sum((i.total_eur for i in items), D(0)),
    )
