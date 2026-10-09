"""
SemanticComparisonStrategy: Implements ComparisonStrategy using RAG context retrieval
and Prompt Chaining AI analysis.
"""

from typing import Any, Dict, List, Optional
from .base import ComparisonStrategy
from ...models.schemas import ChangeResult, StructuredDocument


class SemanticComparisonStrategy(ComparisonStrategy):
    """
    Intelligent semantic comparison strategy.
    Combines local RAG retrieval with Prompt Chaining reasoning to detect
    meaningful policy/requirement changes versus cosmetic rephrasing.
    """

    def __init__(self, ai_client: Optional[Any] = None):
        if ai_client is None:
            from ...ai.client import AIClient
            ai_client = AIClient()
        self.ai_client = ai_client
        from ...ai.prompt_chain import PromptChainPipeline
        self.pipeline = PromptChainPipeline(self.ai_client)

    @property
    def name(self) -> str:
        return "SemanticComparisonStrategy"

    def compare(
        self,
        matches: List[Dict[str, Any]],
        old_doc: StructuredDocument,
        new_doc: StructuredDocument,
    ) -> List[ChangeResult]:
        """
        Executes semantic comparison using the RAG and Prompt Chaining pipeline.
        """
        return self.pipeline.process_changes(matches, old_doc, new_doc)

