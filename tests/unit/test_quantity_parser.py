from app.nlu.quantities import parse_line_items


def test_parse_line_items():
    text = "I bought 2x Monitor 220,50€ and a Keyboard for 75.00 EUR"
    items = parse_line_items(text)
    assert len(items) == 2

    monitor_item = next(i for i in items if "Monitor" in i["description"])
    keyboard_item = next(i for i in items if "Keyboard" in i["description"])

    assert monitor_item["quantity"] == 2
    assert monitor_item["unit_price_eur"] == "220.50"

    assert keyboard_item["quantity"] == 1
    assert keyboard_item["unit_price_eur"] == "75.00"
