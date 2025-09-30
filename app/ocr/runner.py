from __future__ import annotations

from app.memory.store import ProfileStore
from app.receipts.parser import parse_receipt_text

from .adapter import MockOCRAdapter, OCRAdapter, TesseractAdapter


def run_ocr_on_attachment(store: ProfileStore, attachment_id: int) -> dict | None:
    attachment = store.get_attachment(attachment_id)
    if not attachment:
        raise ValueError("Attachment not found")

    # Add consent check before processing
    profile = store.get_profile(attachment["user_id"])
    if not profile.data.get("preferences", {}).get("consent", {}).get("ocr", False):
        store.log_evidence(
            attachment["user_id"],
            attachment["turn_id"],
            "ocr_blocked",
            {"attachment_id": attachment_id},
            {"reason": "consent_not_given"},
        )
        raise PermissionError("OCR consent not provided by user.")

    with open(attachment["path"], "rb") as f:
        data = f.read()

    adapter: OCRAdapter  # Type the variable with the base class
    try:
        adapter = TesseractAdapter()
    except RuntimeError:
        adapter = MockOCRAdapter()

    ocr_result = adapter.ocr_bytes(data, attachment["content_type"])
    parsed_receipt = parse_receipt_text(ocr_result.text)

    parse_id = store.save_receipt_parse(
        attachment["user_id"], attachment_id, ocr_result.text, parsed_receipt, ocr_result.engine
    )

    # Log an evidence event for the OCR run
    store.log_evidence(
        user_id=attachment["user_id"],
        turn_id=attachment["turn_id"],
        kind="ocr_run",
        payload={"attachment_id": attachment_id, "engine": ocr_result.engine},
        result={"parse_id": parse_id, "items_found": len(parsed_receipt.items)},
    )
    return store.get_receipt_parse_by_attachment(attachment_id)
