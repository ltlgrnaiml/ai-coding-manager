"""RAG Retrieval Service - Search and retrieve relevant context.

Provides semantic search and full-text search for knowledge injection into chat.
"""

import sqlite3
from dataclasses import dataclass

from .database import get_connection
from .embedding_service import EmbeddingService


@dataclass
class RetrievalResult:
    """Single retrieval result with score."""
    doc_id: str
    doc_type: str
    title: str
    content: str
    score: float
    chunk_index: int | None = None


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class KnowledgeRetriever:
    """Retrieve relevant context from knowledge base."""

    def __init__(self):
        self._embedding_service: EmbeddingService | None = None

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def search_semantic(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.3,
    ) -> list[RetrievalResult]:
        """Semantic search using embeddings."""
        try:
            query_embedding = self.embedding_service.embed(query)
            query_vec = query_embedding.vector
        except Exception:
            return []

        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT 
                    e.vector, e.chunk_id,
                    c.content as chunk_content, c.chunk_index,
                    d.id as doc_id, d.type as doc_type, d.title
                FROM embeddings e
                JOIN chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.doc_id
                WHERE d.archived_at IS NULL
            """).fetchall()

            results = []
            for row in rows:
                stored_vec = self.embedding_service.blob_to_vector(row['vector'])
                score = cosine_similarity(query_vec, stored_vec)
                if score >= min_score:
                    results.append(RetrievalResult(
                        doc_id=row['doc_id'],
                        doc_type=row['doc_type'],
                        title=row['title'],
                        content=row['chunk_content'],
                        score=score,
                        chunk_index=row['chunk_index'],
                    ))

            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
        finally:
            conn.close()

    def search_fulltext(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Full-text search using FTS5."""
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT 
                    d.id as doc_id, d.type as doc_type, d.title, 
                    d.content, bm25(content_fts) as score
                FROM content_fts f
                JOIN documents d ON d.id = f.doc_id
                WHERE content_fts MATCH ? AND d.archived_at IS NULL
                ORDER BY score
                LIMIT ?
            """, (query, limit)).fetchall()

            return [
                RetrievalResult(
                    doc_id=row['doc_id'],
                    doc_type=row['doc_type'],
                    title=row['title'],
                    content=row['content'][:1000],  # Truncate for context
                    score=abs(row['score']),  # BM25 returns negative
                )
                for row in rows
            ]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def search_hybrid(
        self,
        query: str,
        limit: int = 5,
        semantic_weight: float = 0.7,
    ) -> list[RetrievalResult]:
        """Hybrid search combining semantic and full-text."""
        semantic_results = self.search_semantic(query, limit=limit * 2)
        fts_results = self.search_fulltext(query, limit=limit * 2)

        # Merge and dedupe by doc_id
        seen: dict[str, RetrievalResult] = {}
        
        for r in semantic_results:
            key = f"{r.doc_id}:{r.chunk_index or 0}"
            if key not in seen:
                r.score *= semantic_weight
                seen[key] = r
            else:
                seen[key].score += r.score * semantic_weight

        for r in fts_results:
            key = f"{r.doc_id}:0"
            if key not in seen:
                r.score *= (1 - semantic_weight)
                seen[key] = r
            else:
                seen[key].score += r.score * (1 - semantic_weight)

        results = list(seen.values())
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]


def get_knowledge_context(query: str, max_tokens: int = 2000) -> str:
    """Get formatted knowledge context for chat injection.
    
    Args:
        query: User's query to find relevant context for
        max_tokens: Approximate max tokens for context (rough estimate)
    
    Returns:
        Formatted context string to inject into system prompt
    """
    retriever = KnowledgeRetriever()
    results = retriever.search_hybrid(query, limit=5)
    
    if not results:
        return ""
    
    context_parts = ["## Relevant Knowledge Context\n"]
    char_limit = max_tokens * 4  # Rough char-to-token ratio
    current_chars = len(context_parts[0])
    
    for r in results:
        entry = f"\n### {r.title} ({r.doc_type})\n{r.content}\n"
        if current_chars + len(entry) > char_limit:
            break
        context_parts.append(entry)
        current_chars += len(entry)
    
    if len(context_parts) == 1:
        return ""
    
    return "".join(context_parts)


# Singleton instance
_retriever: KnowledgeRetriever | None = None

def get_retriever() -> KnowledgeRetriever:
    """Get singleton retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever
