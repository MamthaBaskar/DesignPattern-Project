"""
Prompt Chaining Pipeline.
Coordinates RAG context retrieval with the multi-stage AI reasoning chain.
"""

import logging
from typing import Any, Dict, List
from .client import AIClient
from .rag import LocalRAGRetriever
from ..models.schemas import (
    ChangeResult,
    ChangeType,
    ConfidenceLevel,
    StructuredDocument,
)

logger = logging.getLogger(__name__)


class PromptChainPipeline:
    """
    Executes the Prompt Chaining sequence for all detected document changes.
    Integrates RAG context retrieval and formats final ChangeResults.
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def process_changes(
        self,
        matches: List[Dict[str, Any]],
        old_doc: StructuredDocument,
        new_doc: StructuredDocument,
    ) -> List[ChangeResult]:
        """
        Executes Prompt Chaining and RAG on matched paragraphs.
        """
        rag_retriever = LocalRAGRetriever(old_doc, new_doc)
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

            # Retrieve RAG context using change text as query
            query = f"{old_text} {new_text}".strip()
            rag_context_str = rag_retriever.format_rag_prompt_section(query)

            # Run Prompt Chaining AI analysis
            analysis = self.ai_client.analyze_change_prompt_chain(
                change_type=c_type,
                old_text=old_text,
                new_text=new_text,
                section=section,
                rag_context=rag_context_str,
            )

            results.append(
                ChangeResult(
                    id=f"change_{idx + 1}",
                    change_type=c_type,
                    category=analysis["category"],
                    old_text=old_text,
                    new_text=new_text,
                    section=section,
                    location=location,
                    importance=analysis["importance"],
                    impact=analysis["impact"],
                    explanation=analysis["explanation"],
                    confidence=analysis["confidence"],
                    is_meaningful=analysis["is_meaningful"],
                    similarity_score=round(similarity, 3),
                )
            )

        return results

