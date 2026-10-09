"""
Document Processing Service (Member 1 facade).
Coordinates validation, factory resolution, adapter extraction, and structuring.
"""

import logging
from typing import Optional
from ..models.schemas import StructuredDocument
from .factory import DocumentProcessorFactory
from .preprocessor import DocumentPreprocessor
from .validators import validate_extracted_content, validate_file_metadata

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Facade service orchestrating validation, adapter extraction, and preprocessing.
    """

    def __init__(self, preprocessor: Optional[DocumentPreprocessor] = None):
        self.preprocessor = preprocessor or DocumentPreprocessor()

    def process_file(self, filename: str, file_bytes: bytes) -> StructuredDocument:
        """
        Executes Member 1 pipeline for a file:
        Validate -> Factory -> Adapter Extraction (with OCR fallback) -> Preprocessing & Structuring.
        """
        # Step 1: Validate metadata
        file_size = len(file_bytes)
        ext = validate_file_metadata(filename, file_size)

        # Step 2: Factory creates the matching Adapter
        adapter = DocumentProcessorFactory.create_adapter(filename)

        # Step 3: Adapter extracts raw text and extraction metadata
        raw_text, extraction_meta = adapter.extract(file_bytes, filename)

        # Step 4: Validate extracted content
        validate_extracted_content(raw_text, filename)

        # Step 5: Preprocessing and Structuring
        structured_doc = self.preprocessor.process(
            raw_text=raw_text,
            filename=filename,
            file_type=ext.lstrip("."),
            metadata=extraction_meta,
        )

        logger.info(
            f"Successfully processed '{filename}': {len(structured_doc.paragraphs)} paragraphs, "
            f"{len(structured_doc.sections)} sections."
        )

        return structured_doc

