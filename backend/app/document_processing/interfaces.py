"""
Adapter Pattern: Common interface for document processors.
All file-type adapters (PDF, DOCX, TXT) implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class DocumentAdapterInterface(ABC):
    """
    Target interface for the Adapter Pattern.
    Unifies disparate document libraries (pypdf, python-docx, built-in text decoders)
    into a standardized extraction protocol.
    """

    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts plain text and extraction metadata from document bytes.

        Args:
            file_bytes: Raw binary content of the file.
            filename: Name of the uploaded file.

        Returns:
            Tuple[str, Dict[str, Any]]: (extracted_text, metadata_dict)

        Raises:
            DocumentValidationError: If content is corrupted or unreadable.
        """
        pass

