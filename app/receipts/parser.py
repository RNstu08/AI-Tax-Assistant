from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

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


# A more robust pattern that looks for a description with letters, followed by a price.
_ITEM_PATTERN = re.compile(r"^(?P<desc>.*[a-zA-Z].*?)\s+(?P<price>\d[\d.,]*)\s*€?$", re.MULTILINE)
_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_receipt_text(text: str) -> ParsedReceipt:
    items: list[ParsedItem] = []
    for m in _ITEM_PATTERN.finditer(text):
        try:
            desc = m.group("desc").strip()
            # Skip lines that are likely just dates or junk
            if _DATE_PATTERN.match(desc) or len(desc) < 2:
                continue

            price_str = m.group("price").replace(",", ".")
            price = D(price_str)
            items.append(
                ParsedItem(description=desc, quantity=1, unit_price_eur=price, total_eur=price)
            )
        except (ValueError, TypeError, AttributeError, InvalidOperation):
            # Gracefully skip any line that fails to parse
            continue

    date_match = _DATE_PATTERN.search(text)
    vendor_match = re.search(r"Vendor:\s*(.*)", text, re.I)
    return ParsedReceipt(
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        purchase_date=date_match.group(1) if date_match else None,
        items=items,
        total_eur=sum((i.total_eur for i in items), D(0)),
    )
