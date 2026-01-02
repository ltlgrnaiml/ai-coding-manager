"""Knowledge Archive Contracts.

Pydantic schemas for the knowledge archive, search, and RAG systems.
"""

from contracts.knowledge.archive import (
    Document,
    DocumentMetadata,
    DocumentType,
    SyncConfig,
    SyncMode,
    SyncStatus,
)
from contracts.knowledge.search import (
    HybridSearchConfig,
    Relationship,
    RelationshipType,
    SearchQuery,
    SearchResult,
)
from contracts.knowledge.rag import (
    Chunk,
    ChunkingStrategy,
    ContextRequest,
    RAGContext,
)

__all__ = [
    # Archive
    "Document",
    "DocumentMetadata",
    "DocumentType",
    "SyncConfig",
    "SyncMode",
    "SyncStatus",
    # Search
    "HybridSearchConfig",
    "Relationship",
    "RelationshipType",
    "SearchQuery",
    "SearchResult",
    # RAG
    "Chunk",
    "ChunkingStrategy",
    "ContextRequest",
    "RAGContext",
]

__version__ = "2025.12.01"
