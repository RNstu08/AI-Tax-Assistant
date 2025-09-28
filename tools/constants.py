from __future__ import annotations

from decimal import Decimal

CONST = {
    2024: {
        "commute": {
            "rate_first_20": Decimal("0.30"),
            "rate_after_20": Decimal("0.38"),
            "public_transport_cap": Decimal("4500"),
        },
        "home_office": {"per_day": Decimal("6.00"), "annual_cap": Decimal("1260")},
        "equipment": {"gwg_gross_threshold": Decimal("952.00")},
    },
    2025: {
        "commute": {
            "rate_first_20": Decimal("0.30"),
            "rate_after_20": Decimal("0.38"),
            "public_transport_cap": Decimal("4500"),
        },
        "home_office": {"per_day": Decimal("6.00"), "annual_cap": Decimal("1260")},
        "equipment": {"gwg_gross_threshold": Decimal("952.00")},
    },
}
