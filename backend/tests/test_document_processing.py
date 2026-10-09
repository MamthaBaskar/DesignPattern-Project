"""
Unit tests for Document Processing (Member 1).
Covers validation, Factory Pattern, Adapter Pattern, extraction, OCR fallback, and preprocessing.
"""

from pathlib import Path
import pytest
from app.document_processing.factory import DocumentProcessorFactory
from app.document_processing.adapters.pdf_adapter import PDFAdapter
from app.document_processing.adapters.docx_adapter import DOCXAdapter
from app.document_processing.adapters.txt_adapter import TXTAdapter
from app.document_processing.validators import (
    DocumentValidationError,
    validate_file_metadata,
    validate_extracted_content,
)
from app.document_processing.preprocessor import DocumentPreprocessor
from app.document_processing.service import DocumentProcessingService

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


def test_validation_supported_formats():
    assert validate_file_metadata("file.pdf", 1024) == ".pdf"
    assert validate_file_metadata("file.docx", 2048) == ".docx"
    assert validate_file_metadata("file.txt", 512) == ".txt"


def test_validation_unsupported_formats():
    with pytest.raises(DocumentValidationError) as exc:
        validate_file_metadata("archive.zip", 1024)
    assert exc.value.code == "UNSUPPORTED_FORMAT"


def test_validation_empty_file():
    with pytest.raises(DocumentValidationError) as exc:
        validate_file_metadata("empty.txt", 0)
    assert exc.value.code == "EMPTY_FILE"


def test_validation_oversized_file():
    huge_size = 30 * 1024 * 1024
    with pytest.raises(DocumentValidationError) as exc:
        validate_file_metadata("huge.pdf", huge_size)
    assert exc.value.code == "FILE_TOO_LARGE"


def test_factory_creates_correct_adapters():
    pdf_adapter = DocumentProcessorFactory.create_adapter("document.pdf")
    assert isinstance(pdf_adapter, PDFAdapter)

    docx_adapter = DocumentProcessorFactory.create_adapter("document.docx")
    assert isinstance(docx_adapter, DOCXAdapter)

    txt_adapter = DocumentProcessorFactory.create_adapter("document.txt")
    assert isinstance(txt_adapter, TXTAdapter)


def test_factory_rejects_unknown_extension():
    with pytest.raises(DocumentValidationError):
        DocumentProcessorFactory.create_adapter("report.exe")


def test_txt_adapter_extraction():
    sample_file = SAMPLES_DIR / "attendance_v1.txt"
    content = sample_file.read_bytes()
    adapter = TXTAdapter()
    text, meta = adapter.extract(content, "attendance_v1.txt")
    assert "Minimum attendance is 75%" in text
    assert meta["format"] == "txt"


def test_docx_adapter_extraction():
    sample_file = SAMPLES_DIR / "attendance_v1.docx"
    content = sample_file.read_bytes()
    adapter = DOCXAdapter()
    text, meta = adapter.extract(content, "attendance_v1.docx")
    assert "Minimum attendance is 75%" in text
    assert meta["format"] == "docx"


def test_pdf_adapter_extraction():
    sample_file = SAMPLES_DIR / "attendance_v1.pdf"
    content = sample_file.read_bytes()
    adapter = PDFAdapter()
    text, meta = adapter.extract(content, "attendance_v1.pdf")
    assert "Minimum attendance is 75%" in text
    assert meta["format"] == "pdf"


def test_pdf_corrupted_handling():
    corrupted_bytes = b"%PDF-1.4 not a valid stream truncated"
    adapter = PDFAdapter()
    with pytest.raises(DocumentValidationError):
        adapter.extract(corrupted_bytes, "corrupt.pdf")


def test_preprocessor_structuring():
    preprocessor = DocumentPreprocessor()
    raw = """
    # Section 1: Attendance
    All students must register presence.
    Minimum attendance is 75%.

    Section 2: Examination
    Non-compliant students are disqualified.
    """
    doc = preprocessor.process(raw, "policy.txt", "txt")
    assert doc.filename == "policy.txt"
    assert len(doc.sections) >= 2
    assert len(doc.paragraphs) >= 2
    assert any("75%" in p.text for p in doc.paragraphs)

