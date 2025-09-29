# tests/unit/test_receipt_parser.py
from app.receipts.parser import parse_receipt_text


def test_receipt_parser():
    text = "Vendor: DemoShop\nDate: 2024-05-12\n1x Laptop 899,00 €"
    receipt = parse_receipt_text(text)
    assert receipt.vendor == "DemoShop" and len(receipt.items) == 1
    assert receipt.items[0].description == "Laptop"
