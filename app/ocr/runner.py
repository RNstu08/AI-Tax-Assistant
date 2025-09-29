from __future__ import annotations

from app.memory.store import ProfileStore
from app.receipts.parser import parse_receipt_text

from .adapter import MockOCRAdapter, TesseractAdapter


def run_ocr_on_attachment(store: ProfileStore, attachment_id: int) -> dict:
    """Orchestrates the OCR and parsing process for a given attachment."""
    attachment = store.get_attachment(attachment_id)
    if not attachment:
        raise ValueError("Attachment not found")

    with open(attachment["path"], "rb") as f:
        data = f.read()

    try:
        adapter = TesseractAdapter()
    except RuntimeError:
        adapter = MockOCRAdapter()

    ocr_result = adapter.ocr_bytes(data)
    parsed_receipt = parse_receipt_text(ocr_result.text)

    # Store the parse result in the database
    parse_id = store.save_receipt_parse(
        user_id=attachment["user_id"],
        attachment_id=attachment_id,
        text=ocr_result.text,
        parsed_data=parsed_receipt,
    )
    return store.get_receipt_parse(parse_id)
