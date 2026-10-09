"""
TXT Adapter implementing DocumentAdapterInterface.
Decodes text files with robust charset detection and normalization.
"""

import logging
from typing import Any, Dict, Tuple

from ..interfaces import DocumentAdapterInterface
from ..validators import DocumentValidationError

logger = logging.getLogger(__name__)


class TXTAdapter(DocumentAdapterInterface):
    """
    Adapter for raw text files with multiple encoding fallbacks.
    """

    def extract(self, file_bytes: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        metadata: Dict[str, Any] = {
            "format": "txt",
            "encoding": "utf-8",
            "extraction_method": "text_decoder",
        }

        encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        decoded_text = ""

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                metadata["encoding"] = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if not decoded_text:
            raise DocumentValidationError(
                f"Failed to decode text file '{filename}'. Unsupported character encoding.",
                "ENCODING_ERROR",
            )

        cleaned_text = decoded_text.strip()
        if not cleaned_text:
            raise DocumentValidationError(
                f"Text file '{filename}' contains no readable text.",
                "EMPTY_TXT",
            )

        metadata["line_count"] = len(cleaned_text.splitlines())
        return cleaned_text, metadata

