"""
Local RAG (Retrieval-Augmented Generation) Module.
Chunks old and new documents, computes local vector embeddings (TF-IDF cosine similarity),
and retrieves relevant context for change analysis.
"""

import logging
from typing import Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models.schemas import DocumentParagraph, StructuredDocument

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a discrete semantic chunk within a document."""

    def __init__(
        self,
        chunk_id: str,
        doc_version: str,  # "old" or "new"
        text: str,
        section_title: str,
        paragraph_index: int,
    ):
        self.chunk_id = chunk_id
        self.doc_version = doc_version
        self.text = text
        self.section_title = section_title
        self.paragraph_index = paragraph_index


class LocalRAGRetriever:
    """
    Lightweight, embedded RAG retrieval engine.
    Indexes both old and new documents in-memory and retrieves relevant surrounding
    and semantic context for any given change.
    """

    def __init__(self, old_doc: StructuredDocument, new_doc: StructuredDocument):
        self.old_doc = old_doc
        self.new_doc = new_doc
        self.chunks: List[DocumentChunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self) -> None:
        """Chunks documents and computes TF-IDF vector space."""
        try:
            # Chunk old document
            for p in self.old_doc.paragraphs:
                if p.text.strip():
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=f"old_{p.id}",
                            doc_version="old",
                            text=p.text.strip(),
                            section_title=p.section_title or "General",
                            paragraph_index=p.paragraph_index,
                        )
                    )

            # Chunk new document
            for p in self.new_doc.paragraphs:
                if p.text.strip():
                    self.chunks.append(
                        DocumentChunk(
                            chunk_id=f"new_{p.id}",
                            doc_version="new",
                            text=p.text.strip(),
                            section_title=p.section_title or "General",
                            paragraph_index=p.paragraph_index,
                        )
                    )

            if not self.chunks:
                logger.warning("RAG: No chunks available to index.")
                return

            corpus = [c.text for c in self.chunks]
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                token_pattern=r"(?u)\b\w+\b",
                ngram_range=(1, 2),
                max_features=5000,
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            logger.info(f"RAG: Indexed {len(self.chunks)} chunks across old and new documents.")

        except Exception as e:
            logger.warning(f"RAG index creation encountered an issue: {e}")
            self.vectorizer = None
            self.tfidf_matrix = None

    def retrieve_context(self, query: str, top_k: int = 3) -> Dict[str, List[str]]:
        """
        Retrieves top_k context chunks from both old and new documents for the query.
        Returns a dictionary: {"old_context": [...], "new_context": [...]}
        """
        context_result: Dict[str, List[str]] = {"old_context": [], "new_context": []}

        if not query or not query.strip() or self.vectorizer is None or self.tfidf_matrix is None:
            return context_result

        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

            # Get indices sorted by similarity
            ranked_indices = np.argsort(similarities)[::-1]

            old_count = 0
            new_count = 0

            for idx in ranked_indices:
                score = similarities[idx]
                if score <= 0.05:  # minimal similarity floor
                    continue

                chunk = self.chunks[idx]
                snippet = f"[{chunk.section_title}] {chunk.text}"

                if chunk.doc_version == "old" and old_count < top_k:
                    context_result["old_context"].append(snippet)
                    old_count += 1
                elif chunk.doc_version == "new" and new_count < top_k:
                    context_result["new_context"].append(snippet)
                    new_count += 1

                if old_count >= top_k and new_count >= top_k:
                    break

        except Exception as e:
            logger.warning(f"RAG retrieval failed gracefully: {e}")

        return context_result

    def format_rag_prompt_section(self, query: str) -> str:
        """
        Formats retrieved context into a clear text section for Prompt Chaining.
        """
        contexts = self.retrieve_context(query)
        old_ctx = "\n".join(f"- {c}" for c in contexts.get("old_context", [])) or "None retrieved"
        new_ctx = "\n".join(f"- {c}" for c in contexts.get("new_context", [])) or "None retrieved"

        return (
            f"=== RETRIEVED CONTEXT (RAG Knowledge Source) ===\n"
            f"Relevant Old Document Context:\n{old_ctx}\n\n"
            f"Relevant New Document Context:\n{new_ctx}\n"
            f"================================================"
        )

