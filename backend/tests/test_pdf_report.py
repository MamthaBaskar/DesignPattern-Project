"""
Unit tests for PDF Report Generation.
"""

from app.models.schemas import (
    ChangeCategory,
    ChangeResult,
    ChangeType,
    ComparisonResponse,
    ComparisonSummary,
    ConfidenceLevel,
    ImportanceLevel,
)
from app.reporting.pdf_generator import generate_comparison_pdf_report


def test_pdf_report_generation():
    change = ChangeResult(
        id="c1",
        change_type=ChangeType.MODIFIED,
        category=ChangeCategory.REQUIREMENT_CHANGE,
        old_text="Minimum attendance is 75%.",
        new_text="Minimum attendance is 80%.",
        section="Section 1: General Student Requirements",
        location="Line 4",
        importance=ImportanceLevel.HIGH,
        impact="Students must maintain a higher attendance percentage.",
        explanation="The attendance threshold increased from 75% to 80%.",
        confidence=ConfidenceLevel.HIGH,
        is_meaningful=True,
    )

    summary = ComparisonSummary(
        old_filename="attendance_v1.txt",
        new_filename="attendance_v2.txt",
        total_changes=1,
        added_count=0,
        deleted_count=0,
        modified_count=1,
        unchanged_count=2,
        high_importance_count=1,
        medium_importance_count=0,
        low_importance_count=0,
        strategy_used="SemanticComparisonStrategy",
        ai_status="Active",
        processing_time_seconds=0.45,
    )

    response = ComparisonResponse(
        summary=summary,
        changes=[change],
    )

    pdf_bytes = generate_comparison_pdf_report(response)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

