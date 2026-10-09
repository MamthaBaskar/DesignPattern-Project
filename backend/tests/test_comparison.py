"""
Unit tests for Document Matching and Strategy Pattern (Member 2).
"""

from app.comparison.matcher import DocumentMatcher
from app.comparison.service import ComparisonService
from app.comparison.strategies.text_strategy import TextComparisonStrategy
from app.comparison.strategies.semantic_strategy import SemanticComparisonStrategy
from app.document_processing.preprocessor import DocumentPreprocessor
from app.models.schemas import ChangeType, ImportanceLevel


def test_matcher_detects_all_change_types():
    preprocessor = DocumentPreprocessor()
    old_raw = """
    First unchanged paragraph.

    Old paragraph to be modified.

    Paragraph that will be deleted.
    """
    new_raw = """
    First unchanged paragraph.

    New paragraph with modification.

    Brand new paragraph added here.
    """

    old_doc = preprocessor.process(old_raw, "old.txt", "txt")
    new_doc = preprocessor.process(new_raw, "new.txt", "txt")

    assert len(old_doc.paragraphs) == 3
    assert len(new_doc.paragraphs) == 3

    matcher = DocumentMatcher()
    matches = matcher.match(old_doc, new_doc)

    change_types = [m["change_type"] for m in matches]
    assert ChangeType.UNCHANGED in change_types
    assert ChangeType.MODIFIED in change_types
    assert ChangeType.DELETED in change_types
    assert ChangeType.ADDED in change_types


def test_strategy_pattern_execution_and_switching():
    preprocessor = DocumentPreprocessor()
    old_doc = preprocessor.process("Minimum attendance is 75%.", "v1.txt", "txt")
    new_doc = preprocessor.process("Minimum attendance is 80%.", "v2.txt", "txt")

    # Service with TextComparisonStrategy
    service = ComparisonService(strategy=TextComparisonStrategy())
    res_text = service.compare_documents(old_doc, new_doc)
    assert res_text.summary.strategy_used == "TextComparisonStrategy"
    assert len(res_text.changes) == 1
    assert res_text.changes[0].change_type == ChangeType.MODIFIED

    # Dynamic Strategy swap to SemanticComparisonStrategy
    service.set_strategy(SemanticComparisonStrategy())
    res_semantic = service.compare_documents(old_doc, new_doc)
    assert res_semantic.summary.strategy_used == "SemanticComparisonStrategy"
    assert len(res_semantic.changes) == 1
    assert res_semantic.changes[0].importance == ImportanceLevel.HIGH

