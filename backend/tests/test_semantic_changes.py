"""
Unit tests for Semantic Comparison, Classification, Importance, and Impact.
Validates the required 75% -> 80% requirement change and wording-only change examples.
"""

from app.comparison.classifier import classify_change, check_is_wording_only
from app.models.schemas import ChangeCategory, ChangeType, ImportanceLevel


def test_meaningful_attendance_requirement_change():
    """
    Mandatory test case:
    Old: Minimum attendance is 75%.
    New: Minimum attendance is 80%.
    Expected: Requirement/Number change, HIGH importance, meaningful change.
    """
    old_text = "Minimum attendance is 75%."
    new_text = "Minimum attendance is 80%."

    category, importance, impact, explanation, confidence, is_meaningful = classify_change(
        change_type=ChangeType.MODIFIED,
        old_text=old_text,
        new_text=new_text,
    )

    assert is_meaningful is True
    assert category in (ChangeCategory.REQUIREMENT_CHANGE, ChangeCategory.NUMBER_VALUE_CHANGE)
    assert importance == ImportanceLevel.HIGH
    assert "75%" in explanation and "80%" in explanation
    assert "attendance" in impact.lower() or "attendance" in explanation.lower()


def test_wording_only_change():
    """
    Mandatory test case:
    Old: Students must submit the form.
    New: Students are required to submit the form.
    Expected: Wording-only change, LOW importance, not meaningful substantive change.
    """
    old_text = "Students must submit the form."
    new_text = "Students are required to submit the form."

    is_wording = check_is_wording_only(old_text, new_text)
    assert is_wording is True

    category, importance, impact, explanation, confidence, is_meaningful = classify_change(
        change_type=ChangeType.MODIFIED,
        old_text=old_text,
        new_text=new_text,
    )

    assert is_meaningful is False
    assert category == ChangeCategory.WORDING_ONLY_CHANGE
    assert importance == ImportanceLevel.LOW


def test_addition_and_removal_classification():
    cat_add, imp_add, _, _, _, meaningful_add = classify_change(
        change_type=ChangeType.ADDED,
        old_text="",
        new_text="Students must maintain satisfactory academic standing.",
    )
    assert meaningful_add is True
    assert imp_add in (ImportanceLevel.HIGH, ImportanceLevel.MEDIUM)

    cat_del, imp_del, _, _, _, meaningful_del = classify_change(
        change_type=ChangeType.DELETED,
        old_text="Late fee of $50 applies after Friday.",
        new_text="",
    )
    assert meaningful_del is True
    assert cat_del == ChangeCategory.REMOVAL

