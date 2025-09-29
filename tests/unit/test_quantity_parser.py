# tests/unit/test_quantity_parser.py
from app.nlu.quantities import parse_line_items


def test_parse_line_items():
    text = "I bought 2x Monitor 220,50€ and a Keyboard for 75.00 EUR"
    items = parse_line_items(text)
    assert len(items) == 2
    assert items[0]["description"] == "Monitor" and items[0]["quantity"] == 2
