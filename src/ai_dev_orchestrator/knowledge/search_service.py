"""Search Service - Full-text, vector, and hybrid search.

Provides:
- FTS5 full-text search
- Vector similarity search with cosine similarity
- Hybrid search with Reciprocal Rank Fusion (RRF)
"""

import sqlite3
from dataclasses import dataclass

from ai_dev_orchestrator.knowledge.database import get_connection


@dataclass
class SearchHit:
    """Search result.
    
    Attributes:
        doc_id: Document identifier.
        title: Document title.
        snippet: Content snippet.
        score: Relevance score.
        doc_type: Document type (adr, spec, discussion, etc.).
    """
    doc_id: str
    title: str
    snippet: str
    score: float
    doc_type: str


class SearchService:
    """Search service with FTS, vector, and hybrid modes."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        """Initialize search service.
        
        Args:
            conn: Database connection. Creates new if not provided.
        """
        self.conn = conn or get_connection()

    def fts_search(self, query: str, top_k: int = 10) -> list[SearchHit]:
        """Full-text search using FTS5.
        
        Args:
            query: Search query string.
            top_k: Maximum results to return.
            
        Returns:
            List of SearchHit results.
        """
        rows = self.conn.execute("""
            SELECT
                id as doc_id,
                title,
                substr(content, 1, 200) as snippet,
                type as doc_type
            FROM documents
            WHERE archived_at IS NULL
              AND (title LIKE ? OR content LIKE ?)
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', top_k)).fetchall()

        return [
            SearchHit(
                doc_id=r['doc_id'],
                title=r['title'],
                snippet=r['snippet'],
                score=1.0,
                doc_type=r['doc_type']
            )
            for r in rows
        ]

    def _blob_to_vector(self, blob: bytes) -> list[float]:
        """Deserialize vector from BLOB."""
        import struct
        count = len(blob) // 4
        return list(struct.unpack(f'{count}f', blob))

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def vector_search(self, query_vector: list[float], top_k: int = 10) -> list[SearchHit]:
        """Vector similarity search.
        
        Args:
            query_vector: Query embedding vector.
            top_k: Maximum results to return.
            
        Returns:
            List of SearchHit results sorted by similarity.
        """
        rows = self.conn.execute("""
            SELECT
                e.vector,
                c.doc_id,
                c.content as snippet,
                d.title,
                d.type as doc_type
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.doc_id = d.id
            WHERE d.archived_at IS NULL
        """).fetchall()

        scored = []
        for r in rows:
            vec = self._blob_to_vector(r['vector'])
            sim = self._cosine_similarity(query_vector, vec)
            scored.append(SearchHit(
                doc_id=r['doc_id'],
                title=r['title'],
                snippet=r['snippet'][:200],
                score=sim,
                doc_type=r['doc_type']
            ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def hybrid_search(
        self,
        query: str,
        query_vector: list[float] | None = None,
        top_k: int = 10,
        fts_weight: float = 0.5,
        vec_weight: float = 0.5
    ) -> list[SearchHit]:
        """Hybrid search with Reciprocal Rank Fusion (RRF).

        Combines FTS and vector search results using RRF formula:
        score = sum(1 / (k + rank)) where k=60
        
        Args:
            query: Text query for FTS.
            query_vector: Query embedding for vector search.
            top_k: Maximum results to return.
            fts_weight: Weight for FTS results.
            vec_weight: Weight for vector results.
            
        Returns:
            List of SearchHit results with combined scores.
        """
        k = 60  # RRF constant
        rrf_scores: dict[str, float] = {}
        doc_data: dict[str, SearchHit] = {}

        # FTS results
        fts_results = self.fts_search(query, top_k * 2)
        for rank, hit in enumerate(fts_results):
            rrf_scores[hit.doc_id] = rrf_scores.get(hit.doc_id, 0) + fts_weight / (k + rank + 1)
            doc_data[hit.doc_id] = hit

        # Vector results (if vector provided)
        if query_vector:
            vec_results = self.vector_search(query_vector, top_k * 2)
            for rank, hit in enumerate(vec_results):
                rrf_scores[hit.doc_id] = rrf_scores.get(hit.doc_id, 0) + vec_weight / (k + rank + 1)
                if hit.doc_id not in doc_data:
                    doc_data[hit.doc_id] = hit

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        return [
            SearchHit(
                doc_id=doc_data[doc_id].doc_id,
                title=doc_data[doc_id].title,
                snippet=doc_data[doc_id].snippet,
                score=rrf_scores[doc_id],
                doc_type=doc_data[doc_id].doc_type
            )
            for doc_id in sorted_ids[:top_k]
        ]
