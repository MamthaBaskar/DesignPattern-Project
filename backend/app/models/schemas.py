"""
Data models and schemas for Document Comparison and Analysis.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    ADDED = "ADDED"
    DELETED = "DELETED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


class ChangeCategory(str, Enum):
    REQUIREMENT_CHANGE = "Requirement Change"
    RULE_CHANGE = "Rule Change"
    NUMBER_VALUE_CHANGE = "Number/Value Change"
    ADDITION = "Addition"
    REMOVAL = "Removal"
    WORDING_ONLY_CHANGE = "Wording-only Change"
    OTHER = "Other"


class ImportanceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "UNAVAILABLE"


class DocumentParagraph(BaseModel):
    id: str
    text: str
    section_title: Optional[str] = "General"
    paragraph_index: int
    location_meta: Dict[str, Any] = Field(default_factory=dict)


class DocumentSection(BaseModel):
    id: str
    title: str
    level: int = 1
    paragraph_ids: List[str] = Field(default_factory=list)


class StructuredDocument(BaseModel):
    filename: str
    file_type: str
    full_text: str
    paragraphs: List[DocumentParagraph]
    sections: List[DocumentSection]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChangeResult(BaseModel):
    id: str
    change_type: ChangeType
    category: ChangeCategory
    old_text: str = ""
    new_text: str = ""
    section: Optional[str] = "General"
    location: Optional[str] = None
    importance: ImportanceLevel = ImportanceLevel.LOW
    impact: str = ""
    explanation: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    is_meaningful: bool = True
    similarity_score: float = 0.0


class ComparisonSummary(BaseModel):
    old_filename: str
    new_filename: str
    total_changes: int
    added_count: int
    deleted_count: int
    modified_count: int
    unchanged_count: int
    high_importance_count: int
    medium_importance_count: int
    low_importance_count: int
    strategy_used: str
    ai_status: str
    processing_time_seconds: float = 0.0


class ComparisonResponse(BaseModel):
    summary: ComparisonSummary
    changes: List[ChangeResult]
    old_document_info: Dict[str, Any] = Field(default_factory=dict)
    new_document_info: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    ai_available: bool
    ai_provider: str
    ocr_available: bool
    supported_formats: List[str]

