"""
Unit tests for RAG and Prompt Chaining AI pipeline.
Validates chunking, retrieval, prompt chaining, and missing API key fallback.
"""

from app.ai.client import AIClient
from app.ai.prompt_chain import PromptChainPipeline
from app.ai.rag import LocalRAGRetriever
from app.comparison.matcher import DocumentMatcher
from app.document_processing.preprocessor import DocumentPreprocessor
from app.models.schemas import ChangeType, ConfidenceLevel, ImportanceLevel


def test_rag_chunking_and_retrieval():
    preprocessor = DocumentPreprocessor()
    old_doc = preprocessor.process(
        "Academic Policy: Attendance must be maintained. Minimum attendance is 75%.",
        "old.txt",
        "txt",
    )
    new_doc = preprocessor.process(
        "Academic Policy: Attendance must be maintained. Minimum attendance is 80%.",
        "new.txt",
        "txt",
    )

    retriever = LocalRAGRetriever(old_doc, new_doc)
    assert len(retriever.chunks) >= 2

    # Query for attendance
    contexts = retriever.retrieve_context("attendance threshold percentage")
    assert "old_context" in contexts
    assert "new_context" in contexts

    prompt_section = retriever.format_rag_prompt_section("attendance")
    assert "RETRIEVED CONTEXT" in prompt_section


def test_ai_fallback_when_credentials_missing():
    # Instantiate client without API key
    client = AIClient()
    pipeline = PromptChainPipeline(client)

    preprocessor = DocumentPreprocessor()
    old_doc = preprocessor.process("Minimum attendance is 75%.", "old.txt", "txt")
    new_doc = preprocessor.process("Minimum attendance is 80%.", "new.txt", "txt")

    matcher = DocumentMatcher()
    matches = matcher.match(old_doc, new_doc)

    results = pipeline.process_changes(matches, old_doc, new_doc)
    assert len(results) == 1
    res = results[0]

    # Verify fallback generated accurate classification and impact without error
    assert res.change_type == ChangeType.MODIFIED
    assert res.importance == ImportanceLevel.HIGH
    assert "75%" in res.explanation and "80%" in res.explanation
    assert res.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)

