from __future__ import annotations

import re

from tools.money import D

# Pattern 1: Specifically for items with an explicit quantity (e.g., "2x Monitor 220.50€")
# This pattern is now more strict about the description.
_QTY_PATTERN = re.compile(
    r"(?P<qty>\d+)\s*x\s*(?P<desc>[\w\s.-]+?)\s+" r"(?P<price>\d[\d.,]*)\s*(?:€|eur)",
    re.IGNORECASE,
)

# Pattern 2: Specifically for single items using keywords like "for" or "at"
_SINGLE_PATTERN = re.compile(
    r"\b(?P<desc>[a-zA-Z\s]{3,})\s+(?:for|at|à)\s+(?P<price>\d[\d.,]*)\s*(?:€|eur)",
    re.IGNORECASE,
)

# A list of all patterns to try, in order of specificity
PATTERNS = [_QTY_PATTERN, _SINGLE_PATTERN]


def parse_line_items(text: str) -> list[dict]:
    """
    Extracts structured line items by trying multiple specific patterns and ensuring
    that parts of the string are not matched more than once.
    """
    all_matches = []
    # Find all possible matches from all patterns
    for pat in PATTERNS:
        for m in pat.finditer(text):
            all_matches.append(m)

    # Sort matches by their start position to process the string from left to right
    all_matches.sort(key=lambda m: m.start())

    items: list[dict] = []
    last_match_end = -1
    for match in all_matches:
        # This check is crucial: it prevents us from processing a sub-match
        # that is already part of a larger, previously processed match.
        if match.start() < last_match_end:
            continue

        try:
            quantity = int(match.groupdict().get("qty") or 1)
            description = match.group("desc").strip()
            price_str = match.group("price").replace(",", ".")
            unit_price = D(price_str)
            total_price = quantity * unit_price

            # Filter out common false positives
            if description.lower() in ("and a", "a", "bought"):
                continue

            items.append(
                {
                    "description": description,
                    "quantity": quantity,
                    "unit_price_eur": str(unit_price),
                    "total_eur": str(total_price),
                }
            )
            last_match_end = match.end()
        except (ValueError, TypeError, AttributeError):
            continue
    return items
