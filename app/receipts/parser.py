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


_EXCLUSION_KEYWORDS = [
    "subtotal",
    "total",
    "vat",
    "invoice",
    "date",
    "qty",
    "thank",
    "id:",
    "rechnung",
    "steuer",
    "gmbh",
    "straße",
]
_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def euro_str_to_float(val: str) -> Decimal:
    val = val.replace("€", "").replace(" ", "").strip()
    if "," in val and "." in val:
        val = val.replace(".", "").replace(",", ".")
    elif "," in val:
        val = val.replace(",", ".")
    return D(val)


def parse_receipt_text(text: str) -> ParsedReceipt:
    items: list[ParsedItem] = []
    lines = text.splitlines()

    print("======== OCR LINES ========")
    for i, line in enumerate(lines):
        print(f"{i}: {repr(line)}")
    print("===========================")

    descriptions = []
    pricing_block = []
    capture_desc = False
    for _, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.lower() == "description":
            capture_desc = True
            continue
        if stripped_line.lower() == "qty":
            break
        if capture_desc and stripped_line and stripped_line.lower() not in ["description", "qty"]:
            descriptions.append(stripped_line)

    capture_unit = False
    for _, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.lower() == "unit price":
            capture_unit = True
            continue
        if capture_unit:
            if stripped_line and stripped_line.startswith("€"):
                pricing_block.append(euro_str_to_float(stripped_line))
            elif not stripped_line:
                continue
            else:
                break

    # Assemble line items, mapping each desc to one price, qty=1
    for desc, price in zip(descriptions, pricing_block, strict=False):
        if len(desc) > 6 and not any(word in desc.lower() for word in _EXCLUSION_KEYWORDS):
            items.append(
                ParsedItem(
                    description=desc,
                    quantity=1,
                    unit_price_eur=price,
                    total_eur=price,
                )
            )
            print(f"BLOCK PARSE: {desc}, qty=1, unit={price}, total={price}")

    # Fallback: Look for lines like "DESC €X.XX" if the above matching failed
    if not items:
        exp = re.compile(r"^(?P<desc>[A-Za-z\s\-'\"().]+)\s+€?(?P<price>[\d.,]+)\s*$")
        for _, line in enumerate(lines):
            stripped_line = line.strip()
            # FIX 1: Wrapped long condition in parentheses to allow a line break.
            if not stripped_line or any(
                word in stripped_line.lower() for word in _EXCLUSION_KEYWORDS
            ):
                continue
            m = exp.match(stripped_line)
            if m and len(m.group("desc")) > 6:
                try:
                    desc = m.group("desc").strip()
                    price = euro_str_to_float(m.group("price"))
                    items.append(
                        # FIX 2: Broke the long object creation into multiple lines.
                        ParsedItem(
                            description=desc,
                            quantity=1,
                            unit_price_eur=price,
                            total_eur=price,
                        )
                    )
                except Exception as e:
                    print(f"FALLBACK PARSE FAIL: {e}")

    date_match = _DATE_PATTERN.search(text)
    vendor_match = lines[0] if lines else None

    print(f"========= FINAL ITEMS ({len(items)}) =========")
    for item in items:
        print(item)
    print("=============================================")

    return ParsedReceipt(
        vendor=vendor_match.strip() if vendor_match else None,
        purchase_date=date_match.group(1) if date_match else None,
        items=items,
        total_eur=sum((i.total_eur for i in items), D(0)),
    )
    # for m in _ITEM_PATTERN.finditer(text):
    #     try:
    #         desc = m.group("desc").strip()
    #         # Skip lines that are likely just dates or junk
    #         if _DATE_PATTERN.match(desc) or len(desc) < 2:
    #             continue

    #         price_str = m.group("price").replace(",", ".")
    #         price = D(price_str)
    #         items.append(
    #             ParsedItem(description=desc, quantity=1, unit_price_eur=price, total_eur=price)
    #         )
    #     except (ValueError, TypeError, AttributeError, InvalidOperation):
    #         # Gracefully skip any line that fails to parse
    #         continue

    # date_match = _DATE_PATTERN.search(text)
    # vendor_match = re.search(r"Vendor:\s*(.*)", text, re.I)
    # return ParsedReceipt(
    #     vendor=vendor_match.group(1).strip() if vendor_match else None,
    #     purchase_date=date_match.group(1) if date_match else None,
    #     items=items,
    #     total_eur=sum((i.total_eur for i in items), D(0)),
    # )
