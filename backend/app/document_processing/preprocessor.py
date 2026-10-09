"""
Preprocessing and Document Structuring module (Member 1).
Cleans whitespace, splits text into paragraphs, identifies sections,
and generates standardized StructuredDocument objects.
"""

import re
from typing import Any, Dict, List, Optional
from ..models.schemas import DocumentParagraph, DocumentSection, StructuredDocument


class DocumentPreprocessor:
    """
    Cleans raw document text, parses paragraphs and sections,
    and produces a standardized StructuredDocument model.
    """

    def __init__(self, min_paragraph_len: int = 1):
        self.min_paragraph_len = min_paragraph_len

    def is_section_header(self, line: str) -> bool:
        """Determines if a single line represents a section title."""
        line = line.strip()
        if not line or len(line) > 120:
            return False

        # 1. Markdown heading
        if re.match(r"^#{1,4}\s+", line):
            return True

        # 2. Numbered or titled heading
        if re.match(
            r"^(?:\d+[\.\)]|\d+\.\d+|Section\s+\d+|Article\s+[IVXLCDM\d]+)[\s:\.\-]",
            line,
            re.IGNORECASE,
        ):
            return True

        # 3. All uppercase short title
        letters_only = re.sub(r"[^A-Za-z]", "", line)
        if len(letters_only) >= 4 and line.isupper() and len(line.split()) <= 8:
            return True

        return False

    def clean_header_title(self, raw_header: str) -> str:
        """Strips leading markdown symbols and extra punctuation from headers."""
        return re.sub(r"^#{1,4}\s*", "", raw_header).strip()

    def process(
        self,
        raw_text: str,
        filename: str,
        file_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StructuredDocument:
        """
        Processes raw extracted text into a structured document.
        Detects section headers and groups text blocks into paragraphs.
        """
        if metadata is None:
            metadata = {}

        # Standardize line breaks and strip leading/trailing whitespace per line
        raw_lines = [l.strip() for l in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]

        # Group lines into paragraphs or section headers
        paragraphs: List[DocumentParagraph] = []
        sections: List[DocumentSection] = []

        current_section_title = "General"
        current_section_id = "sec_0"

        sections.append(
            DocumentSection(
                id=current_section_id,
                title=current_section_title,
                level=1,
                paragraph_ids=[],
            )
        )

        current_para_lines: List[str] = []
        p_counter = 0
        approx_line = 1

        def flush_paragraph():
            nonlocal p_counter, current_para_lines, approx_line
            if current_para_lines:
                para_text = " ".join(current_para_lines).strip()
                if para_text:
                    p_id = f"p_{p_counter}"
                    paragraph = DocumentParagraph(
                        id=p_id,
                        text=para_text,
                        section_title=current_section_title,
                        paragraph_index=p_counter,
                        location_meta={
                            "approx_line": approx_line,
                            "word_count": len(para_text.split()),
                        },
                    )
                    paragraphs.append(paragraph)
                    sections[-1].paragraph_ids.append(p_id)
                    p_counter += 1
                current_para_lines = []

        for line_num, line in enumerate(raw_lines, 1):
            if not line:
                # Blank line triggers paragraph boundary
                flush_paragraph()
                approx_line = line_num + 1
                continue

            if self.is_section_header(line):
                # Flush current paragraph before starting section
                flush_paragraph()
                current_section_title = self.clean_header_title(line)
                current_section_id = f"sec_{len(sections)}"
                sections.append(
                    DocumentSection(
                        id=current_section_id,
                        title=current_section_title,
                        level=1,
                        paragraph_ids=[],
                    )
                )
                approx_line = line_num + 1
                continue

            # Accumulate lines within paragraph
            if not current_para_lines:
                approx_line = line_num
            current_para_lines.append(line)

        # Flush any trailing paragraph
        flush_paragraph()

        # Build full clean text
        cleaned_full_text = "\n\n".join(p.text for p in paragraphs)

        doc_metadata = {
            **metadata,
            "total_characters": len(cleaned_full_text),
            "total_words": len(cleaned_full_text.split()),
            "total_paragraphs": len(paragraphs),
            "total_sections": len(sections),
        }

        return StructuredDocument(
            filename=filename,
            file_type=file_type,
            full_text=cleaned_full_text,
            paragraphs=paragraphs,
            sections=sections,
            metadata=doc_metadata,
        )

