#!/usr/bin/env python3
"""GPU-Accelerated Batch Embedder for Research Papers.

Leverages NVIDIA GPU (5090) for high-throughput embedding generation.
Uses large batch sizes and parallel processing to maximize GPU utilization.

Safe to run alongside other operations - uses separate embedding table
and read-only queries for source data.

Usage:
    python scripts/gpu_batch_embedder.py [--batch-size 128] [--model all-mpnet-base-v2]
"""

import argparse
import sqlite3
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

# Check for GPU availability
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        GPU_NAME = torch.cuda.get_device_name(0)
        GPU_MEMORY = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    else:
        GPU_NAME = "N/A"
        GPU_MEMORY = 0
except ImportError:
    CUDA_AVAILABLE = False
    GPU_NAME = "N/A"
    GPU_MEMORY = 0

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False


# Database paths - use AIKH centralized location
import os
def _get_aikh_db() -> Path:
    # Docker mount
    if Path("/aikh/research.db").exists():
        return Path("/aikh/research.db")
    # Environment variable
    if aikh_home := os.getenv("AIKH_HOME"):
        return Path(aikh_home) / "research.db"
    # Default
    return Path.home() / ".aikh" / "research.db"

DB_PATH = _get_aikh_db()

# Embedding table schema (separate from main embeddings to avoid conflicts)
GPU_EMBEDDINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_embeddings_gpu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    chunk_id INTEGER,
    embedding_type TEXT DEFAULT 'paper',  -- 'paper' or 'chunk'
    model_name TEXT NOT NULL,
    embedding BLOB NOT NULL,
    embedding_dim INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, chunk_id, embedding_type)
);

CREATE INDEX IF NOT EXISTS idx_gpu_emb_paper ON paper_embeddings_gpu(paper_id);
CREATE INDEX IF NOT EXISTS idx_gpu_emb_type ON paper_embeddings_gpu(embedding_type);
"""


@dataclass
class EmbeddingTask:
    """Single embedding task."""
    id: str
    text: str
    task_type: str  # 'paper' or 'chunk'
    chunk_id: Optional[int] = None


class GPUBatchEmbedder:
    """GPU-accelerated batch embedding generator."""
    
    # Optimal batch sizes for different GPUs (based on VRAM)
    BATCH_SIZE_BY_VRAM = {
        24: 256,   # RTX 4090, 5090
        16: 128,   # RTX 4080
        12: 64,    # RTX 4070
        8: 32,     # RTX 4060
    }
    
    def __init__(
        self,
        db_path: Path = DB_PATH,
        model_name: str = "all-mpnet-base-v2",
        batch_size: Optional[int] = None,
        device: Optional[str] = None
    ):
        self.db_path = db_path
        self.model_name = model_name
        
        # Auto-detect optimal batch size based on GPU VRAM
        if batch_size is None:
            for vram, bs in sorted(self.BATCH_SIZE_BY_VRAM.items(), reverse=True):
                if GPU_MEMORY >= vram:
                    batch_size = bs
                    break
            batch_size = batch_size or 32
        
        self.batch_size = batch_size
        self.device = device or ("cuda" if CUDA_AVAILABLE else "cpu")
        self.model = None
        self.embedding_dim = None
        
        self._init_db()
    
    def _init_db(self):
        """Initialize GPU embeddings table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(GPU_EMBEDDINGS_SCHEMA)
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_model(self):
        """Load embedding model on GPU."""
        if self.model is None:
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers not installed")
            
            print(f"📦 Loading model: {self.model_name}")
            print(f"   Device: {self.device}")
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Get embedding dimension
            test_emb = self.model.encode(["test"], convert_to_numpy=True)
            self.embedding_dim = test_emb.shape[1]
            print(f"   Embedding dim: {self.embedding_dim}")
        
        return self.model
    
    @staticmethod
    def vector_to_blob(vector: np.ndarray) -> bytes:
        """Convert numpy vector to SQLite BLOB."""
        return vector.astype(np.float32).tobytes()
    
    @staticmethod
    def blob_to_vector(blob: bytes) -> np.ndarray:
        """Convert SQLite BLOB to numpy vector."""
        return np.frombuffer(blob, dtype=np.float32)
    
    def get_papers_without_embeddings(self) -> List[EmbeddingTask]:
        """Get papers that need embeddings."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT p.id, p.title, p.abstract
                FROM research_papers p
                LEFT JOIN paper_embeddings_gpu e 
                    ON p.id = e.paper_id AND e.embedding_type = 'paper'
                WHERE e.id IS NULL
            """)
            
            tasks = []
            for row in cursor.fetchall():
                text_parts = [row["title"] or ""]
                if row["abstract"]:
                    text_parts.append(row["abstract"])
                # Get first chunk content if available
                chunk_row = conn.execute(
                    "SELECT content FROM paper_chunks WHERE paper_id = ? ORDER BY chunk_index LIMIT 1",
                    (row["id"],)
                ).fetchone()
                if chunk_row:
                    text_parts.append(chunk_row["content"][:2000])
                
                text = " ".join(text_parts)
                if text.strip():
                    tasks.append(EmbeddingTask(
                        id=row["id"],
                        text=text,
                        task_type="paper"
                    ))
            
            return tasks
    
    def get_chunks_without_embeddings(self) -> List[EmbeddingTask]:
        """Get chunks that need embeddings."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT c.id as chunk_id, c.paper_id, c.content
                FROM paper_chunks c
                LEFT JOIN paper_embeddings_gpu e 
                    ON c.paper_id = e.paper_id 
                    AND c.id = e.chunk_id 
                    AND e.embedding_type = 'chunk'
                WHERE e.paper_id IS NULL
                  AND LENGTH(c.content) > 50
            """)
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append(EmbeddingTask(
                    id=row["paper_id"],
                    text=row["content"],
                    task_type="chunk",
                    chunk_id=row["chunk_id"]
                ))
            
            return tasks
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts using GPU."""
        model = self._load_model()
        
        # Use show_progress_bar=False for cleaner output in batches
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        return embeddings
    
    def process_papers(self) -> Tuple[int, float]:
        """Process all papers without embeddings.
        
        Returns:
            Tuple of (count, elapsed_time_seconds)
        """
        tasks = self.get_papers_without_embeddings()
        if not tasks:
            print("✅ All papers already have GPU embeddings")
            return 0, 0.0
        
        print(f"📊 Processing {len(tasks)} papers...")
        start_time = time.time()
        
        # Process in batches
        total_batches = (len(tasks) - 1) // self.batch_size + 1
        processed = 0
        
        for batch_idx in range(0, len(tasks), self.batch_size):
            batch_tasks = tasks[batch_idx:batch_idx + self.batch_size]
            batch_num = batch_idx // self.batch_size + 1
            
            # Generate embeddings
            texts = [t.text for t in batch_tasks]
            embeddings = self.embed_batch(texts)
            
            # Store embeddings
            with self._get_conn() as conn:
                for task, embedding in zip(batch_tasks, embeddings):
                    conn.execute("""
                        INSERT OR REPLACE INTO paper_embeddings_gpu
                        (paper_id, chunk_id, embedding_type, model_name, embedding, embedding_dim)
                        VALUES (?, NULL, 'paper', ?, ?, ?)
                    """, (task.id, self.model_name, self.vector_to_blob(embedding), self.embedding_dim))
                conn.commit()
            
            processed += len(batch_tasks)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            print(f"   Batch {batch_num}/{total_batches}: {processed}/{len(tasks)} "
                  f"({rate:.1f} papers/sec)")
        
        elapsed = time.time() - start_time
        print(f"✅ Processed {processed} papers in {elapsed:.1f}s "
              f"({processed/elapsed:.1f} papers/sec)")
        
        return processed, elapsed
    
    def process_chunks(self) -> Tuple[int, float]:
        """Process all chunks without embeddings.
        
        Returns:
            Tuple of (count, elapsed_time_seconds)
        """
        tasks = self.get_chunks_without_embeddings()
        if not tasks:
            print("✅ All chunks already have GPU embeddings")
            return 0, 0.0
        
        print(f"📊 Processing {len(tasks)} chunks...")
        start_time = time.time()
        
        # Process in larger batches for chunks (they're smaller)
        chunk_batch_size = self.batch_size * 2
        total_batches = (len(tasks) - 1) // chunk_batch_size + 1
        processed = 0
        
        for batch_idx in range(0, len(tasks), chunk_batch_size):
            batch_tasks = tasks[batch_idx:batch_idx + chunk_batch_size]
            batch_num = batch_idx // chunk_batch_size + 1
            
            # Generate embeddings
            texts = [t.text for t in batch_tasks]
            embeddings = self.embed_batch(texts)
            
            # Store embeddings
            with self._get_conn() as conn:
                for task, embedding in zip(batch_tasks, embeddings):
                    conn.execute("""
                        INSERT OR REPLACE INTO paper_embeddings_gpu
                        (paper_id, chunk_id, embedding_type, model_name, embedding, embedding_dim)
                        VALUES (?, ?, 'chunk', ?, ?, ?)
                    """, (task.id, task.chunk_id, self.model_name, 
                          self.vector_to_blob(embedding), self.embedding_dim))
                conn.commit()
            
            processed += len(batch_tasks)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            
            # Print less frequently for chunks
            if batch_num % 5 == 0 or batch_num == total_batches:
                print(f"   Batch {batch_num}/{total_batches}: {processed}/{len(tasks)} "
                      f"({rate:.1f} chunks/sec)")
        
        elapsed = time.time() - start_time
        print(f"✅ Processed {processed} chunks in {elapsed:.1f}s "
              f"({processed/elapsed:.1f} chunks/sec)")
        
        return processed, elapsed
    
    def get_stats(self) -> dict:
        """Get embedding statistics."""
        with self._get_conn() as conn:
            # Total papers
            total_papers = conn.execute(
                "SELECT COUNT(*) FROM research_papers"
            ).fetchone()[0]
            
            # Papers with GPU embeddings
            papers_with_emb = conn.execute(
                "SELECT COUNT(DISTINCT paper_id) FROM paper_embeddings_gpu WHERE embedding_type='paper'"
            ).fetchone()[0]
            
            # Total chunks
            total_chunks = conn.execute(
                "SELECT COUNT(*) FROM paper_chunks"
            ).fetchone()[0]
            
            # Chunks with GPU embeddings
            chunks_with_emb = conn.execute(
                "SELECT COUNT(*) FROM paper_embeddings_gpu WHERE embedding_type='chunk'"
            ).fetchone()[0]
            
            return {
                "total_papers": total_papers,
                "papers_with_embeddings": papers_with_emb,
                "papers_pending": total_papers - papers_with_emb,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_emb,
                "chunks_pending": total_chunks - chunks_with_emb,
            }


def print_gpu_info():
    """Print GPU information."""
    print("=" * 60)
    print("GPU BATCH EMBEDDER")
    print("=" * 60)
    
    if CUDA_AVAILABLE:
        print(f"🚀 GPU: {GPU_NAME}")
        print(f"   VRAM: {GPU_MEMORY:.1f} GB")
        print(f"   CUDA: {torch.version.cuda}")
    else:
        print("⚠️  No GPU detected - using CPU")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="GPU-accelerated batch embedder")
    parser.add_argument("--batch-size", "-b", type=int, default=None,
                        help="Batch size (auto-detected based on GPU VRAM)")
    parser.add_argument("--model", "-m", type=str, default="all-mpnet-base-v2",
                        help="Embedding model name")
    parser.add_argument("--papers-only", action="store_true",
                        help="Only embed papers, not chunks")
    parser.add_argument("--chunks-only", action="store_true",
                        help="Only embed chunks, not papers")
    parser.add_argument("--stats", action="store_true",
                        help="Show statistics only")
    
    args = parser.parse_args()
    
    print_gpu_info()
    
    if not SBERT_AVAILABLE:
        print("❌ sentence-transformers not installed")
        print("   Run: pip install sentence-transformers")
        sys.exit(1)
    
    embedder = GPUBatchEmbedder(
        batch_size=args.batch_size,
        model_name=args.model
    )
    
    print(f"📊 Batch size: {embedder.batch_size}")
    print(f"📦 Model: {embedder.model_name}")
    print()
    
    if args.stats:
        stats = embedder.get_stats()
        print("Current Statistics:")
        print(f"  Papers: {stats['papers_with_embeddings']}/{stats['total_papers']} "
              f"({stats['papers_pending']} pending)")
        print(f"  Chunks: {stats['chunks_with_embeddings']}/{stats['total_chunks']} "
              f"({stats['chunks_pending']} pending)")
        return
    
    total_time = 0
    
    if not args.chunks_only:
        count, elapsed = embedder.process_papers()
        total_time += elapsed
    
    if not args.papers_only:
        count, elapsed = embedder.process_chunks()
        total_time += elapsed
    
    print()
    print("=" * 60)
    stats = embedder.get_stats()
    print("Final Statistics:")
    print(f"  Papers: {stats['papers_with_embeddings']}/{stats['total_papers']}")
    print(f"  Chunks: {stats['chunks_with_embeddings']}/{stats['total_chunks']}")
    print(f"  Total time: {total_time:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
