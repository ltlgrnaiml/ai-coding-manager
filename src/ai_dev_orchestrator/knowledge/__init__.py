"""Knowledge module - RAG system with SQLite-backed storage.

This module provides:
- SQLite database for document and chunk storage
- Full-text search with FTS5
- Vector similarity search
- Hybrid search with Reciprocal Rank Fusion (RRF)
- Embedding generation with sentence-transformers
- Enhanced RAG with query enhancement and LLM re-ranking
"""

from ai_dev_orchestrator.knowledge.database import (
    init_database,
    get_connection,
    DB_PATH,
)
from ai_dev_orchestrator.knowledge.search_service import (
    SearchService,
    SearchHit,
)
from ai_dev_orchestrator.knowledge.embedding_service import (
    EmbeddingService,
    EmbeddingResult,
)
from ai_dev_orchestrator.knowledge.context_builder import (
    ContextBuilder,
    ContextResult,
    ContextChunk,
    get_context_builder,
)
from ai_dev_orchestrator.knowledge.enhanced_rag import (
    EnhancedRAGBuilder,
    EnhancedRAGConfig,
    EnhancedRAGResult,
    get_enhanced_rag_builder,
    get_enhanced_context,
)

__all__ = [
    # Database
    "init_database",
    "get_connection",
    "DB_PATH",
    # Search
    "SearchService",
    "SearchHit",
    # Embeddings
    "EmbeddingService",
    "EmbeddingResult",
    # Context
    "ContextBuilder",
    "ContextResult",
    "ContextChunk",
    "get_context_builder",
    # Enhanced RAG
    "EnhancedRAGBuilder",
    "EnhancedRAGConfig",
    "EnhancedRAGResult",
    "get_enhanced_rag_builder",
    "get_enhanced_context",
]
