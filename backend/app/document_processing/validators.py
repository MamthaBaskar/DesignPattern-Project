"""
File and document validation module.
Enforces format, size, and readability checks.
"""

from pathlib import Path
from typing import Tuple

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class DocumentValidationError(Exception):
    """Raised when document validation fails."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


def validate_file_metadata(filename: str, file_size: int) -> str:
    """
    Validates file extension and size constraints.
    Returns normalized extension if valid.
    """
    if not filename or not filename.strip():
        raise DocumentValidationError("File name is missing or empty.", "EMPTY_FILENAME")

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file format '{ext}'. Supported formats: PDF (.pdf), DOCX (.docx), and TXT (.txt).",
            "UNSUPPORTED_FORMAT",
        )

    if file_size <= 0:
        raise DocumentValidationError(f"File '{filename}' is empty (0 bytes).", "EMPTY_FILE")

    if file_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise DocumentValidationError(
            f"File '{filename}' exceeds maximum allowed size of {max_mb} MB.",
            "FILE_TOO_LARGE",
        )

    return ext


def validate_extracted_content(content: str, filename: str) -> None:
    """
    Validates that extracted text is not blank or whitespace-only.
    """
    if not content or not content.strip():
        raise DocumentValidationError(
            f"No readable text could be extracted from '{filename}'. The file may be empty or corrupted.",
            "EMPTY_CONTENT",
        )

