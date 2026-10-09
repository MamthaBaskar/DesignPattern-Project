"""
TextComparisonStrategy: Implements ComparisonStrategy using deterministic text diffs
and rule-based heuristics.
"""

from typing import Any, Dict, List
from .base import ComparisonStrategy
from ..classifier import classify_change
from ...models.schemas import ChangeResult, StructuredDocument


class TextComparisonStrategy(ComparisonStrategy):
    """
    Syntactic and rule-based text comparison strategy.
    Does not require external AI services; executes rapid, deterministic diffing.
    """

    @property
    def name(self) -> str:
        return "TextComparisonStrategy"

    def compare(
        self,
        matches: List[Dict[str, Any]],
        old_doc: StructuredDocument,
        new_doc: StructuredDocument,
    ) -> List[ChangeResult]:
        results: List[ChangeResult] = []

        for idx, match in enumerate(matches):
            c_type = match["change_type"]
            old_p = match.get("old_paragraph")
            new_p = match.get("new_paragraph")
            old_text = old_p.text if old_p else ""
            new_text = new_p.text if new_p else ""
            section = match.get("section", "General")
            location = match.get("location", "")
            similarity = match.get("similarity", 0.0)

            category, importance, impact, explanation, confidence, is_meaningful = classify_change(
                change_type=c_type,
                old_text=old_text,
                new_text=new_text,
            )

            results.append(
                ChangeResult(
                    id=f"text_change_{idx + 1}",
                    change_type=c_type,
                    category=category,
                    old_text=old_text,
                    new_text=new_text,
                    section=section,
                    location=location,
                    importance=importance,
                    impact=impact,
                    explanation=f"[Text Diff] {explanation}",
                    confidence=confidence,
                    is_meaningful=is_meaningful,
                    similarity_score=round(similarity, 3),
                )
            )

        return results

