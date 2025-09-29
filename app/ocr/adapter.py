from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

# Optional imports for the Tesseract adapter
try:
    import pytesseract
    from PIL import Image
except ImportError as e:
    # Set to None if optional libraries are not installed
    Image = None
    pytesseract = None
    _optional_import_error = e


@dataclass(frozen=True)
class OCRResult:
    text: str
    engine: str


class OCRAdapter(ABC):
    @abstractmethod
    def ocr_bytes(self, data: bytes) -> OCRResult: ...


class MockOCRAdapter(OCRAdapter):
    """A deterministic mock OCR engine for testing."""

    def ocr_bytes(self, data: bytes) -> OCRResult:
        text = "Vendor: DemoShop\nDate: 2024-05-12\n1x Laptop 899,00 €\nTotal 899,00 €"
        return OCRResult(text=text, engine="mock")


class TesseractAdapter(OCRAdapter):
    """An adapter for the real Tesseract OCR engine."""

    def __init__(self):
        if pytesseract is None or Image is None:
            # FIX: Break the long error message into multiple lines
            error_message = (
                "Pillow and/or Pytesseract not installed. "
                "Please run 'pip install -r requirements-ocr.txt'"
            )
            # FIX: Chain the original ImportError for better debugging
            raise RuntimeError(error_message) from _optional_import_error

    def ocr_bytes(self, data: bytes) -> OCRResult:
        img = self.Image.open(BytesIO(data))
        text = self.pytesseract.image_to_string(img)
        return OCRResult(text=text, engine="tesseract")
