"""GPU-Accelerated Services for AIKH.

Provides GPU-accelerated operations:
- Semantic search using GPU embeddings
- Real-time embedding generation
- Batch embedding on demand

Leverages RTX 5090 (31.8GB VRAM) for maximum throughput.
"""

import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

import numpy as np

# Check for GPU availability
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        GPU_NAME = torch.cuda.get_device_name(0)
        GPU_MEMORY = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        DEVICE = "cuda"
    else:
        GPU_NAME = "CPU"
        GPU_MEMORY = 0
        DEVICE = "cpu"
except ImportError:
    CUDA_AVAILABLE = False
    GPU_NAME = "CPU"
    GPU_MEMORY = 0
    DEVICE = "cpu"

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

# Database path
DB_PATH = Path(".workspace/research_papers.db")

# Optimal batch sizes by VRAM
BATCH_SIZE_BY_VRAM = {
    24: 256,  # RTX 4090, 5090
    16: 128,  # RTX 4080
    12: 64,   # RTX 4070
    8: 32,    # RTX 4060
}


def get_optimal_batch_size() -> int:
    """Get optimal batch size based on GPU VRAM."""
    for vram, bs in sorted(BATCH_SIZE_BY_VRAM.items(), reverse=True):
        if GPU_MEMORY >= vram:
            return bs
    return 32


@dataclass
class SearchResult:
    """Semantic search result."""
    paper_id: str
    title: Optional[str]
    abstract: Optional[str]
    similarity: float
    chunk_id: Optional[int] = None
    chunk_content: Optional[str] = None


class GPUSearchService:
    """GPU-accelerated semantic search service."""
    
    _instance = None
    _model = None
    _embedding_dim = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern for model reuse."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        db_path: Path = DB_PATH,
        model_name: str = "all-mpnet-base-v2",
        batch_size: Optional[int] = None
    ):
        self.db_path = db_path
        self.model_name = model_name
        self.batch_size = batch_size or get_optimal_batch_size()
        self.device = DEVICE
    
    @contextmanager
    def _get_conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_model(self):
        """Lazy-load model on GPU."""
        if GPUSearchService._model is None:
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers not installed")
            
            GPUSearchService._model = SentenceTransformer(
                self.model_name, 
                device=self.device
            )
            
            # Get embedding dimension
            test_emb = GPUSearchService._model.encode(["test"], convert_to_numpy=True)
            GPUSearchService._embedding_dim = test_emb.shape[1]
        
        return GPUSearchService._model
    
    @staticmethod
    def vector_to_blob(vector: np.ndarray) -> bytes:
        """Convert numpy vector to SQLite BLOB."""
        return vector.astype(np.float32).tobytes()
    
    @staticmethod
    def blob_to_vector(blob: bytes) -> np.ndarray:
        """Convert SQLite BLOB to numpy vector."""
        return np.frombuffer(blob, dtype=np.float32)
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query string to embedding vector using GPU."""
        model = self._load_model()
        embedding = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding[0]
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Encode multiple texts to embeddings using GPU batch processing."""
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings
    
    def semantic_search_papers(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[SearchResult]:
        """
        GPU-accelerated semantic search across papers.
        
        Uses paper_embeddings_gpu table for fast similarity computation.
        """
        query_embedding = self.encode_query(query)
        
        with self._get_conn() as conn:
            # Get all paper embeddings
            cursor = conn.execute("""
                SELECT e.paper_id, e.embedding, p.title, p.abstract
                FROM paper_embeddings_gpu e
                JOIN research_papers p ON e.paper_id = p.id
                WHERE e.embedding_type = 'paper'
            """)
            
            results = []
            for row in cursor.fetchall():
                paper_embedding = self.blob_to_vector(row["embedding"])
                similarity = float(np.dot(query_embedding, paper_embedding))
                
                if similarity >= min_similarity:
                    results.append(SearchResult(
                        paper_id=row["paper_id"],
                        title=row["title"],
                        abstract=row["abstract"],
                        similarity=similarity
                    ))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:top_k]
    
    def semantic_search_chunks(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.4
    ) -> List[SearchResult]:
        """
        GPU-accelerated semantic search across chunks.
        
        More granular search for specific passages.
        """
        query_embedding = self.encode_query(query)
        
        with self._get_conn() as conn:
            # Get all chunk embeddings
            cursor = conn.execute("""
                SELECT e.paper_id, e.chunk_id, e.embedding, 
                       p.title, c.content
                FROM paper_embeddings_gpu e
                JOIN research_papers p ON e.paper_id = p.id
                JOIN paper_chunks c ON e.chunk_id = c.id
                WHERE e.embedding_type = 'chunk'
            """)
            
            results = []
            for row in cursor.fetchall():
                chunk_embedding = self.blob_to_vector(row["embedding"])
                similarity = float(np.dot(query_embedding, chunk_embedding))
                
                if similarity >= min_similarity:
                    results.append(SearchResult(
                        paper_id=row["paper_id"],
                        title=row["title"],
                        abstract=None,
                        similarity=similarity,
                        chunk_id=row["chunk_id"],
                        chunk_content=row["content"][:500] if row["content"] else None
                    ))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        paper_weight: float = 0.4,
        chunk_weight: float = 0.6
    ) -> List[SearchResult]:
        """
        Hybrid search combining paper-level and chunk-level results.
        
        Uses GPU for all embedding operations.
        """
        # Get both paper and chunk results
        paper_results = self.semantic_search_papers(query, top_k=top_k * 2)
        chunk_results = self.semantic_search_chunks(query, top_k=top_k * 2)
        
        # Build paper score map
        paper_scores: Dict[str, float] = {}
        paper_data: Dict[str, SearchResult] = {}
        
        for r in paper_results:
            paper_scores[r.paper_id] = r.similarity * paper_weight
            paper_data[r.paper_id] = r
        
        # Add chunk scores (boost papers with relevant chunks)
        for r in chunk_results:
            chunk_contribution = r.similarity * chunk_weight
            if r.paper_id in paper_scores:
                paper_scores[r.paper_id] += chunk_contribution
            else:
                paper_scores[r.paper_id] = chunk_contribution
                paper_data[r.paper_id] = SearchResult(
                    paper_id=r.paper_id,
                    title=r.title,
                    abstract=None,
                    similarity=0,
                    chunk_content=r.chunk_content
                )
        
        # Create final results
        final_results = []
        for paper_id, score in paper_scores.items():
            result = paper_data[paper_id]
            result.similarity = score
            final_results.append(result)
        
        final_results.sort(key=lambda x: x.similarity, reverse=True)
        return final_results[:top_k]
    
    def embed_new_paper(self, paper_id: str) -> bool:
        """
        Generate and store GPU embedding for a new paper.
        
        Call this after ingesting a new paper.
        """
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT id, title, abstract, full_text
                FROM research_papers WHERE id = ?
            """, (paper_id,)).fetchone()
            
            if not row:
                return False
            
            # Build text for embedding
            text_parts = [row["title"] or ""]
            if row["abstract"]:
                text_parts.append(row["abstract"])
            if row["full_text"]:
                text_parts.append(row["full_text"][:2000])
            
            text = " ".join(text_parts)
            if not text.strip():
                return False
            
            # Generate embedding on GPU
            embedding = self.encode_query(text)
            
            # Store
            conn.execute("""
                INSERT OR REPLACE INTO paper_embeddings_gpu
                (paper_id, chunk_id, embedding_type, model_name, embedding, embedding_dim)
                VALUES (?, NULL, 'paper', ?, ?, ?)
            """, (paper_id, self.model_name, self.vector_to_blob(embedding), 
                  GPUSearchService._embedding_dim))
            conn.commit()
            
            return True
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get GPU and embedding statistics."""
        with self._get_conn() as conn:
            paper_emb_count = conn.execute(
                "SELECT COUNT(*) FROM paper_embeddings_gpu WHERE embedding_type='paper'"
            ).fetchone()[0]
            
            chunk_emb_count = conn.execute(
                "SELECT COUNT(*) FROM paper_embeddings_gpu WHERE embedding_type='chunk'"
            ).fetchone()[0]
            
            total_papers = conn.execute(
                "SELECT COUNT(*) FROM research_papers"
            ).fetchone()[0]
            
            total_chunks = conn.execute(
                "SELECT COUNT(*) FROM paper_chunks"
            ).fetchone()[0]
        
        return {
            "gpu_available": CUDA_AVAILABLE,
            "gpu_name": GPU_NAME,
            "gpu_memory_gb": round(GPU_MEMORY, 1),
            "device": self.device,
            "batch_size": self.batch_size,
            "model": self.model_name,
            "papers_embedded": paper_emb_count,
            "papers_total": total_papers,
            "chunks_embedded": chunk_emb_count,
            "chunks_total": total_chunks,
            "embedding_coverage": round(paper_emb_count / max(total_papers, 1) * 100, 1)
        }


# Singleton instance
_gpu_service: Optional[GPUSearchService] = None


def get_gpu_service() -> GPUSearchService:
    """Get or create GPU search service singleton."""
    global _gpu_service
    if _gpu_service is None:
        _gpu_service = GPUSearchService()
    return _gpu_service
