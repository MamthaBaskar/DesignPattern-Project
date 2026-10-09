"""
Comparison Service (Member 2 context).
Orchestrates paragraph matching and invokes selected ComparisonStrategy.
"""

import logging
import time
from typing import Optional
from .matcher import DocumentMatcher
from .strategies.base import ComparisonStrategy
from .strategies.semantic_strategy import SemanticComparisonStrategy
from .strategies.text_strategy import TextComparisonStrategy
from ..models.schemas import (
    ChangeResult,
    ChangeType,
    ComparisonResponse,
    ComparisonSummary,
    ImportanceLevel,
    StructuredDocument,
)

logger = logging.getLogger(__name__)


class ComparisonService:
    """
    Context class for Strategy Pattern.
    Executes intelligent document comparison using the configured strategy.
    """

    def __init__(
        self,
        strategy: Optional[ComparisonStrategy] = None,
        matcher: Optional[DocumentMatcher] = None,
    ):
        self._strategy = strategy or SemanticComparisonStrategy()
        self._matcher = matcher or DocumentMatcher()

    @property
    def strategy(self) -> ComparisonStrategy:
        return self._strategy

    def set_strategy(self, strategy: ComparisonStrategy) -> None:
        """Dynamically swap comparison strategy at runtime."""
        self._strategy = strategy

    def compare_documents(
        self,
        old_doc: StructuredDocument,
        new_doc: StructuredDocument,
        strategy_name: Optional[str] = None,
    ) -> ComparisonResponse:
        """
        Executes end-to-end comparison:
        1. Match sections and paragraphs
        2. Apply selected ComparisonStrategy
        3. Compute aggregate metrics and summary
        """
        start_time = time.time()

        # Select strategy if requested
        if strategy_name:
            if strategy_name.lower() == "text":
                self.set_strategy(TextComparisonStrategy())
            elif strategy_name.lower() == "semantic":
                self.set_strategy(SemanticComparisonStrategy())

        logger.info(
            f"Comparing '{old_doc.filename}' vs '{new_doc.filename}' using {self._strategy.name}..."
        )

        # Step 1: Match paragraphs between documents
        matches = self._matcher.match(old_doc, new_doc)

        # Step 2: Execute Strategy Pattern
        changes = self._strategy.compare(matches, old_doc, new_doc)

        # Step 3: Compute Summary Metrics
        added = sum(1 for c in changes if c.change_type == ChangeType.ADDED)
        deleted = sum(1 for c in changes if c.change_type == ChangeType.DELETED)
        modified = sum(1 for c in changes if c.change_type == ChangeType.MODIFIED)
        unchanged = sum(1 for c in changes if c.change_type == ChangeType.UNCHANGED)

        high_imp = sum(1 for c in changes if c.importance == ImportanceLevel.HIGH)
        med_imp = sum(1 for c in changes if c.importance == ImportanceLevel.MEDIUM)
        low_imp = sum(1 for c in changes if c.importance == ImportanceLevel.LOW)

        # Total changes count (excluding UNCHANGED for clarity in user summary)
        total_changes = added + deleted + modified

        duration = round(time.time() - start_time, 2)

        # Filter out UNCHANGED from final change cards if desired, or keep only active changes
        active_changes = [c for c in changes if c.change_type != ChangeType.UNCHANGED]

        summary = ComparisonSummary(
            old_filename=old_doc.filename,
            new_filename=new_doc.filename,
            total_changes=total_changes,
            added_count=added,
            deleted_count=deleted,
            modified_count=modified,
            unchanged_count=unchanged,
            high_importance_count=high_imp,
            medium_importance_count=med_imp,
            low_importance_count=low_imp,
            strategy_used=self._strategy.name,
            ai_status="Active" if isinstance(self._strategy, SemanticComparisonStrategy) else "Bypassed (Text Mode)",
            processing_time_seconds=duration,
        )

        return ComparisonResponse(
            summary=summary,
            changes=active_changes,
            old_document_info=old_doc.metadata,
            new_document_info=new_doc.metadata,
        )

