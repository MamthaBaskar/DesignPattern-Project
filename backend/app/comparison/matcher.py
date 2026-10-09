"""
Document Matcher: Matches sections and paragraphs between old and new documents.
Detects ADDED, DELETED, MODIFIED, and UNCHANGED units.
"""

from difflib import SequenceMatcher
import re
from typing import Any, Dict, List, Set, Tuple
from ..models.schemas import ChangeType, DocumentParagraph, StructuredDocument


def tokenize(text: str) -> Set[str]:
    """Extracts lowercase alphanumeric words for token-level similarity."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Computes a hybrid similarity score combining character SequenceMatcher
    and token Jaccard overlap.
    """
    if text_a.strip() == text_b.strip():
        return 1.0

    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    jaccard = intersection / union if union > 0 else 0.0

    seq_ratio = SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio()

    # Blend: 40% Jaccard + 60% SequenceMatcher
    return 0.4 * jaccard + 0.6 * seq_ratio


class DocumentMatcher:
    """
    Matches paragraphs between old and new StructuredDocument instances.
    Produces matched candidate pairs with initial change_type assignments.
    """

    def __init__(self, match_threshold: float = 0.40):
        self.match_threshold = match_threshold

    def match(
        self, old_doc: StructuredDocument, new_doc: StructuredDocument
    ) -> List[Dict[str, Any]]:
        """
        Matches paragraphs between old and new documents.
        Returns a list of candidate change dictionaries containing:
        - change_type: ADDED, DELETED, MODIFIED, or UNCHANGED
        - old_paragraph: DocumentParagraph or None
        - new_paragraph: DocumentParagraph or None
        - similarity: float
        - section: str
        - location: str
        """
        old_paragraphs = old_doc.paragraphs
        new_paragraphs = new_doc.paragraphs

        # Phase 1: Score all pairwise combinations
        pair_scores: List[Tuple[float, int, int]] = []
        for i, old_p in enumerate(old_paragraphs):
            for j, new_p in enumerate(new_paragraphs):
                raw_sim = compute_similarity(old_p.text, new_p.text)
                # Apply section bonus only if there is already meaningful similarity
                bonus = 0.05 if (raw_sim >= 0.40 and old_p.section_title and old_p.section_title == new_p.section_title) else 0.0
                pair_scores.append((raw_sim + bonus, i, j))

        # Sort pairs in descending order of similarity
        pair_scores.sort(key=lambda x: x[0], reverse=True)

        matched_old: Set[int] = set()
        matched_new: Set[int] = set()
        matches: List[Dict[str, Any]] = []

        # Greedy maximum similarity pairing
        for sim, i, j in pair_scores:
            if i in matched_old or j in matched_new:
                continue

            raw_sim = compute_similarity(old_paragraphs[i].text, new_paragraphs[j].text)

            if raw_sim >= self.match_threshold:
                matched_old.add(i)
                matched_new.add(j)

                is_identical = old_paragraphs[i].text.strip() == new_paragraphs[j].text.strip()
                change_type = ChangeType.UNCHANGED if is_identical else ChangeType.MODIFIED

                matches.append(
                    {
                        "change_type": change_type,
                        "old_paragraph": old_paragraphs[i],
                        "new_paragraph": new_paragraphs[j],
                        "similarity": raw_sim,
                        "section": new_paragraphs[j].section_title or old_paragraphs[i].section_title or "General",
                        "location": f"Old Line {old_paragraphs[i].location_meta.get('approx_line', '?')} → New Line {new_paragraphs[j].location_meta.get('approx_line', '?')}",
                        "order_key": j,
                    }
                )

        # Unmatched old paragraphs -> DELETED
        for i, old_p in enumerate(old_paragraphs):
            if i not in matched_old:
                matches.append(
                    {
                        "change_type": ChangeType.DELETED,
                        "old_paragraph": old_p,
                        "new_paragraph": None,
                        "similarity": 0.0,
                        "section": old_p.section_title or "General",
                        "location": f"Old Line {old_p.location_meta.get('approx_line', '?')}",
                        "order_key": 9999 + i,
                    }
                )

        # Unmatched new paragraphs -> ADDED
        for j, new_p in enumerate(new_paragraphs):
            if j not in matched_new:
                matches.append(
                    {
                        "change_type": ChangeType.ADDED,
                        "old_paragraph": None,
                        "new_paragraph": new_p,
                        "similarity": 0.0,
                        "section": new_p.section_title or "General",
                        "location": f"New Line {new_p.location_meta.get('approx_line', '?')}",
                        "order_key": j,
                    }
                )

        # Sort matches to preserve chronological document order
        matches.sort(key=lambda m: m["order_key"])
        return matches

