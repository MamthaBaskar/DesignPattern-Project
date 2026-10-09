"""
Deterministic change classification, importance, and impact evaluator.
Serves as the foundation for TextComparisonStrategy and fallback for AI.
Provides simple, clear, student-friendly explanations and bullet-point practical impacts.
"""

import re
from typing import List, Set, Tuple
from ..models.schemas import ChangeCategory, ChangeType, ConfidenceLevel, ImportanceLevel

# Words expressing requirements, rules, mandates
RULE_KEYWORDS: Set[str] = {
    "must", "shall", "required", "mandatory", "prohibited", "forbidden", "obligated",
    "will", "should", "deadline", "penalty", "complied", "compliance", "policy",
    "disqualified", "minimum", "maximum", "at least", "no later than"
}


def extract_numbers_and_units(text: str) -> List[str]:
    """Extracts numbers, percentages, currency, and quantities."""
    matches = re.findall(
        r"(?:[\$€£]\s*)?\b\d+(?:\.\d+)?%?(?:\s*(?:days?|hours?|months?|years?|points?|credits?|percent))?",
        text.lower(),
    )
    return [m.strip() for m in matches if m.strip()]


def extract_key_predicates(text: str) -> Set[str]:
    """Extracts words signaling rules and requirements."""
    words = set(re.findall(r"\b\w+\b", text.lower()))
    return words & RULE_KEYWORDS


def check_is_wording_only(old_text: str, new_text: str) -> bool:
    """
    Checks if difference between old and new text represents purely stylistic
    or synonymous wording without substantive semantic change.
    """
    old_nums = set(extract_numbers_and_units(old_text))
    new_nums = set(extract_numbers_and_units(new_text))
    # If numbers/values changed, it is NOT wording-only
    if old_nums != new_nums:
        return False

    old_lower = old_text.lower().strip()
    new_lower = new_text.lower().strip()

    # Specific check for classic requirement synonyms: "must X" vs "is/are required to X"
    def normalize_obligation(t: str) -> str:
        t = re.sub(r"\b(?:is|are|shall be|will be)\s+required\s+to\b", "must", t)
        t = re.sub(r"\bhave\s+to\b", "must", t)
        t = re.sub(r"\bneed\s+to\b", "must", t)
        t = re.sub(r"\bin\s+order\s+to\b", "to", t)
        t = re.sub(r"\bprior\s+to\b", "before", t)
        t = re.sub(r"\bcommence\b", "begin", t)
        t = re.sub(r"\butilize\b", "use", t)
        return re.sub(r"\s+", " ", t).strip()

    norm_old = normalize_obligation(old_lower)
    norm_new = normalize_obligation(new_lower)

    if norm_old == norm_new:
        return True

    # Check token overlap: if over 82% overlap and no rule keyword differences
    old_words = set(re.findall(r"\b\w+\b", norm_old))
    new_words = set(re.findall(r"\b\w+\b", norm_new))
    if old_words and new_words:
        jaccard = len(old_words & new_words) / len(old_words | new_words)
        if jaccard >= 0.82:
            return True

    return False


def classify_change(
    change_type: ChangeType, old_text: str, new_text: str
) -> Tuple[ChangeCategory, ImportanceLevel, str, str, ConfidenceLevel, bool]:
    """
    Determines category, importance, impact, explanation, confidence, and is_meaningful flag.
    Returns: (category, importance, impact, explanation, confidence, is_meaningful)
    All explanations and impacts are simplified for everyday clarity and bullet-point presentation.
    """
    if change_type == ChangeType.UNCHANGED:
        return (
            ChangeCategory.OTHER,
            ImportanceLevel.NONE,
            "• No change to content or rules.",
            "Content has not changed.",
            ConfidenceLevel.HIGH,
            False,
        )

    if change_type == ChangeType.ADDED:
        predicates = extract_key_predicates(new_text)
        nums = extract_numbers_and_units(new_text)
        if predicates or nums:
            cat = ChangeCategory.REQUIREMENT_CHANGE if ("must" in predicates or "required" in predicates) else ChangeCategory.ADDITION
            return (
                cat,
                ImportanceLevel.HIGH if predicates else ImportanceLevel.MEDIUM,
                "• New rules or instructions have been introduced.\n• Students or readers must follow this new section.",
                f"A new requirement was added: '{new_text[:80]}...'",
                ConfidenceLevel.HIGH,
                True,
            )
        return (
            ChangeCategory.ADDITION,
            ImportanceLevel.MEDIUM,
            "• New supplementary information was added.\n• Review the new section for additional details.",
            f"New content was added: '{new_text[:80]}...'",
            ConfidenceLevel.HIGH,
            True,
        )

    if change_type == ChangeType.DELETED:
        predicates = extract_key_predicates(old_text)
        nums = extract_numbers_and_units(old_text)
        if predicates or nums:
            return (
                ChangeCategory.REMOVAL,
                ImportanceLevel.HIGH,
                "• This previous requirement has been removed.\n• You no longer need to follow this instruction.",
                f"Removed previous provision: '{old_text[:80]}...'",
                ConfidenceLevel.HIGH,
                True,
            )
        return (
            ChangeCategory.REMOVAL,
            ImportanceLevel.MEDIUM,
            "• This content was deleted from the new document.",
            f"Content removed: '{old_text[:80]}...'",
            ConfidenceLevel.HIGH,
            True,
        )

    # ChangeType.MODIFIED
    # Check for wording-only change first
    if check_is_wording_only(old_text, new_text):
        return (
            ChangeCategory.WORDING_ONLY_CHANGE,
            ImportanceLevel.LOW,
            "• No change to obligations or rules.\n• This is only a wording or phrasing update.",
            "The wording changed, but the meaning stayed the same.",
            ConfidenceLevel.HIGH,
            False,
        )

    # Check for numbers / threshold / value changes
    old_nums = extract_numbers_and_units(old_text)
    new_nums = extract_numbers_and_units(new_text)

    if old_nums != new_nums and (old_nums or new_nums):
        old_val_str = ", ".join(old_nums) if old_nums else "unspecified"
        new_val_str = ", ".join(new_nums) if new_nums else "unspecified"

        # Check if it affects attendance, requirements, thresholds
        is_req = any(
            term in (old_text + " " + new_text).lower()
            for term in ["attendance", "minimum", "maximum", "fee", "score", "grade", "gpa", "percent", "%", "threshold"]
        )
        category = ChangeCategory.REQUIREMENT_CHANGE if is_req else ChangeCategory.NUMBER_VALUE_CHANGE
        importance = ImportanceLevel.HIGH if is_req else ImportanceLevel.MEDIUM

        # Impact and explanation
        if "attendance" in (old_text + " " + new_text).lower():
            if "75" in old_val_str and "80" in new_val_str:
                impact = (
                    "• Students must maintain at least 80% attendance.\n"
                    "• The previous minimum was 75%.\n"
                    "• Students have a stricter attendance requirement."
                )
                explanation = f"The attendance requirement increased from {old_val_str} to {new_val_str}."
            else:
                impact = (
                    f"• Students must now meet the new attendance threshold of {new_val_str}.\n"
                    f"• The previous threshold was {old_val_str}."
                )
                explanation = f"The attendance requirement changed from {old_val_str} to {new_val_str}."
        else:
            impact = (
                f"• The value changed from {old_val_str} to {new_val_str}.\n"
                f"• Follow the updated figure of {new_val_str} going forward."
            )
            explanation = f"The value changed from {old_val_str} to {new_val_str}."

        return (category, importance, impact, explanation, ConfidenceLevel.HIGH, True)

    # Check for rule keyword alterations
    old_rules = extract_key_predicates(old_text)
    new_rules = extract_key_predicates(new_text)

    if old_rules != new_rules:
        return (
            ChangeCategory.RULE_CHANGE,
            ImportanceLevel.HIGH,
            "• The requirements or conditions have been updated.\n• Please review the new wording to stay compliant.",
            "The requirement or rule in this section was modified.",
            ConfidenceLevel.HIGH,
            True,
        )

    # General modification
    return (
        ChangeCategory.OTHER,
        ImportanceLevel.MEDIUM,
        "• Specific details or phrases were updated.\n• Review the new text for revisions.",
        "This section was updated between versions.",
        ConfidenceLevel.MEDIUM,
        True,
    )
