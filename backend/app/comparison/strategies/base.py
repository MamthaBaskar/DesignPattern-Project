"""
Strategy Pattern: Common interface for Comparison Strategies.
Decouples comparison algorithms from the ComparisonService context.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ...models.schemas import ChangeResult, StructuredDocument


class ComparisonStrategy(ABC):
    """
    Abstract Strategy defining the algorithm contract for comparing documents.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the strategy."""
        pass

    @abstractmethod
    def compare(
        self,
        matches: List[Dict[str, Any]],
        old_doc: StructuredDocument,
        new_doc: StructuredDocument,
    ) -> List[ChangeResult]:
        """
        Executes comparison on matched candidates.
        """
        pass

