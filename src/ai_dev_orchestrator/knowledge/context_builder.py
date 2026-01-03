"""Context Builder - Build RAG context from knowledge archive.

Provides context building for LLM prompts with:
- Token budget management
- Source tracking
- Chunk aggregation
"""

import logging
from dataclasses import dataclass, field

from ai_dev_orchestrator.knowledge.database import get_connection
from ai_dev_orchestrator.knowledge.search_service import SearchService, SearchHit

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """A chunk of context from the knowledge archive.
    
    Attributes:
        doc_id: Source document ID.
        title: Document title.
        content: Chunk content.
        doc_type: Document type.
        score: Relevance score.
    """
    doc_id: str
    title: str
    content: str
    doc_type: str
    score: float


@dataclass
class ContextResult:
    """Result from context building.
    
    Attributes:
        context: Formatted context string for LLM.
        chunks: List of source chunks.
        token_estimate: Estimated token count.
    """
    context: str
    chunks: list[ContextChunk] = field(default_factory=list)
    token_estimate: int = 0


class ContextBuilder:
    """Build context from knowledge archive for RAG.
    
    Retrieves relevant documents and formats them for LLM consumption
    while respecting token budgets.
    """
    
    CHARS_PER_TOKEN = 4  # Rough estimate
    
    def __init__(self, conn=None):
        """Initialize context builder.
        
        Args:
            conn: Database connection. Creates new if not provided.
        """
        self._conn = conn
        self._search = None
    
    def _get_services(self):
        """Lazy-load services."""
        if self._conn is None:
            self._conn = get_connection()
            self._search = SearchService(self._conn)
        return self._conn, self._search
    
    def build_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 5,
    ) -> ContextResult:
        """Build context for a query.
        
        Args:
            query: User query.
            max_tokens: Maximum tokens for context.
            top_k: Maximum number of documents to include.
            
        Returns:
            ContextResult with formatted context and metadata.
        """
        conn, search = self._get_services()
        
        # Search for relevant documents
        hits = search.hybrid_search(query, top_k=top_k)
        
        if not hits:
            return ContextResult(
                context="No relevant context found in knowledge archive.",
                chunks=[],
                token_estimate=10,
            )
        
        # Build context string
        context_parts = ["## PROJECT CONTEXT (from Knowledge Archive)\n"]
        chunks = []
        total_chars = 0
        max_chars = max_tokens * self.CHARS_PER_TOKEN
        
        for hit in hits:
            chunk_text = f"### {hit.title} [{hit.doc_type.upper()}]\n{hit.snippet}\n\n"
            
            if total_chars + len(chunk_text) > max_chars:
                break
            
            context_parts.append(chunk_text)
            chunks.append(ContextChunk(
                doc_id=hit.doc_id,
                title=hit.title,
                content=hit.snippet,
                doc_type=hit.doc_type,
                score=hit.score,
            ))
            total_chars += len(chunk_text)
        
        return ContextResult(
            context="".join(context_parts),
            chunks=chunks,
            token_estimate=total_chars // self.CHARS_PER_TOKEN,
        )


# Global instance
_default_builder: ContextBuilder | None = None


def get_context_builder() -> ContextBuilder:
    """Get or create the default context builder."""
    global _default_builder
    if _default_builder is None:
        _default_builder = ContextBuilder()
    return _default_builder
