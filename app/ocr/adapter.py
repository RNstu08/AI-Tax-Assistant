from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

# Optional imports for the Tesseract adapter
# The mypy config now prevents errors about missing stubs.
try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
except ImportError as e:
    # Capture the error for a user-friendly message at runtime, but allow mypy to pass.
    _optional_import_error = e


@dataclass(frozen=True)
class OCRResult:
    text: str
    engine: str


class OCRAdapter(ABC):
    @abstractmethod
    def ocr_bytes(self, data: bytes, content_type: str) -> OCRResult: ...


class MockOCRAdapter(OCRAdapter):
    """A deterministic mock OCR engine for testing."""

    def ocr_bytes(self, data: bytes, content_type: str) -> OCRResult:
        text = "Vendor: Mock Store\nDate: 2025-01-15\n1x Mock Laptop 950,00 €\nTotal 950,00 €"
        return OCRResult(text=text, engine="mock")


class TesseractAdapter(OCRAdapter):
    """An adapter for the real Tesseract OCR engine that can handle PDFs using PyMuPDF."""

    def __init__(self) -> None:
        # Check for libraries at runtime during initialization.
        if "fitz" not in globals() or "pytesseract" not in globals():
            error_message = (
                "OCR libraries not installed. Run 'pip install -r requirements-ocr.txt' "
                "and ensure Tesseract engine is installed and in your PATH."
            )
            raise RuntimeError(error_message) from _optional_import_error

    def ocr_bytes(self, data: bytes, content_type: str) -> OCRResult:
        if content_type == "application/pdf":
            pdf_doc = fitz.open(stream=data, filetype="pdf")
            page = pdf_doc.load_page(0)
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
        else:
            img = Image.open(BytesIO(data))

        text = pytesseract.image_to_string(img, lang="deu+eng")
        return OCRResult(text=text, engine="tesseract")
