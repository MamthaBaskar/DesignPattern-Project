"""
OCR fallback service for scanned documents and images.
Gracefully handles environments where Tesseract OCR is not installed or fails.
"""

import io
import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

# Check if pytesseract is usable
_PYTESSERACT_AVAILABLE = False
try:
    import pytesseract

    # Test if tesseract executable can be found
    try:
        pytesseract.get_tesseract_version()
        _PYTESSERACT_AVAILABLE = True
    except Exception:
        _PYTESSERACT_AVAILABLE = False
except ImportError:
    _PYTESSERACT_AVAILABLE = False


def is_ocr_available() -> bool:
    """Returns True if Tesseract OCR engine is available and functional."""
    return _PYTESSERACT_AVAILABLE


def perform_ocr_on_image(image_bytes: bytes) -> Tuple[bool, str, Optional[str]]:
    """
    Attempts OCR on image bytes.
    Returns (success, extracted_text, error_message).
    Never raises an unhandled exception.
    """
    if not _PYTESSERACT_AVAILABLE:
        return False, "", "Tesseract OCR engine is not installed or not in PATH."

    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return True, text.strip(), None
    except Exception as e:
        logger.warning(f"OCR processing failed: {e}")
        return False, "", f"OCR failed: {str(e)}"


def perform_ocr_fallback_for_pdf(pdf_reader) -> Tuple[bool, str, Optional[str]]:
    """
    Attempts to extract embedded images from PDF pages and run OCR on them.
    If OCR engine is missing or fails, gracefully returns (False, "", message).
    """
    if not _PYTESSERACT_AVAILABLE:
        return (
            False,
            "",
            "OCR engine (Tesseract) is not configured on the server. Scanned PDF fallback skipped safely.",
        )

    extracted_chunks = []
    try:
        for page_idx, page in enumerate(pdf_reader.pages):
            for img_name, img_obj in page.images.items():
                success, text, _ = perform_ocr_on_image(img_obj.data)
                if success and text:
                    extracted_chunks.append(f"[Page {page_idx + 1} Image OCR]\n{text}")

        full_ocr_text = "\n\n".join(extracted_chunks)
        if full_ocr_text:
            return True, full_ocr_text, None
        return False, "", "No extractable text found via OCR on PDF images."
    except Exception as e:
        logger.warning(f"PDF OCR fallback encountered error: {e}")
        return False, "", f"OCR fallback error: {str(e)}"

