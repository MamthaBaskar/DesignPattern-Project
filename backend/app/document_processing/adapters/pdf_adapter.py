"""
PDF Adapter implementing DocumentAdapterInterface.
Extracts text from PDF documents using pypdf with graceful OCR fallback for scanned pages.
"""

import io
import logging
from typing import Any, Dict, Tuple
import pypdf

from ..interfaces import DocumentAdapterInterface
from ..validators import DocumentValidationError
from ..ocr import perform_ocr_fallback_for_pdf

logger = logging.getLogger(__name__)


class PDFAdapter(DocumentAdapterInterface):
    """
    Adapter that adapts pypdf and OCR fallbacks to DocumentAdapterInterface.
    """

    def extract(self, file_bytes: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        metadata: Dict[str, Any] = {
            "format": "pdf",
            "page_count": 0,
            "extraction_method": "native_pdf",
            "ocr_applied": False,
            "ocr_note": None,
        }

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise DocumentValidationError(
                f"Failed to parse PDF file '{filename}'. The file may be corrupted or encrypted: {str(e)}",
                "CORRUPT_PDF",
            )

        page_count = len(reader.pages)
        metadata["page_count"] = page_count

        if page_count == 0:
            raise DocumentValidationError(f"PDF file '{filename}' contains 0 pages.", "EMPTY_PDF")

        text_parts = []
        for idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text.strip())
            except Exception as pe:
                logger.warning(f"Error extracting page {idx + 1} from {filename}: {pe}")

        extracted_text = "\n\n".join(text_parts).strip()

        # Check if insufficient extractable text (e.g. scanned PDF)
        insufficient_text = len(extracted_text) < 40

        if insufficient_text:
            logger.info(
                f"PDF '{filename}' has insufficient native text ({len(extracted_text)} chars). Attempting OCR fallback..."
            )
            ocr_success, ocr_text, ocr_err = perform_ocr_fallback_for_pdf(reader)
            if ocr_success and ocr_text:
                extracted_text = ocr_text
                metadata["extraction_method"] = "ocr_fallback"
                metadata["ocr_applied"] = True
            else:
                metadata["ocr_note"] = ocr_err or "OCR fallback yielded no additional text."

        if not extracted_text:
            raise DocumentValidationError(
                f"PDF '{filename}' contains no extractable text. It may be an image-only scan without accessible text.",
                "NO_TEXT_EXTRACTED",
            )

        return extracted_text, metadata

