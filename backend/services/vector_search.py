"""GPU-Accelerated Vector Search Service.

High-performance vector similarity search with:
- NumPy vectorized operations (CPU baseline)
- Optional FAISS GPU acceleration
- Pre-built index for fast retrieval
- Batch processing for efficiency

Applies to: research papers, chat logs, P2RE traces
"""

import logging
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import struct
import os

logger = logging.getLogger(__name__)

# Optional FAISS import for GPU acceleration
try:
    import faiss
    FAISS_AVAILABLE = True
    try:
        faiss.get_num_gpus()
        FAISS_GPU_AVAILABLE = faiss.get_num_gpus() > 0
    except:
        FAISS_GPU_AVAILABLE = False
except ImportError:
    FAISS_AVAILABLE = False
    FAISS_GPU_AVAILABLE = False
    logger.info("FAISS not available - using NumPy for vector search")


@dataclass
class VectorSearchResult:
    """Vector search result."""
    id: int | str
    score: float
    distance: float
    metadata: dict | None = None


class VectorIndex:
    """High-performance vector index with optional GPU acceleration."""
    
    def __init__(
        self,
        dimension: int = 384,  # all-MiniLM-L6-v2 default
        use_gpu: bool = True,
        index_type: str = "flat",  # flat, ivf, hnsw
        metric: str = "cosine",  # cosine, l2, ip
    ):
        self.dimension = dimension
        self.use_gpu = use_gpu and FAISS_GPU_AVAILABLE
        self.index_type = index_type
        self.metric = metric
        
        self.index = None
        self.id_map: dict[int, Any] = {}  # FAISS index -> original ID
        self._vectors: list[np.ndarray] = []
        self._built = False
        
        logger.info(f"VectorIndex: dim={dimension}, gpu={self.use_gpu}, type={index_type}")
    
    def add(self, id: Any, vector: list[float] | np.ndarray) -> None:
        """Add vector to index (batch build later)."""
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)
        
        self.id_map[len(self._vectors)] = id
        self._vectors.append(vector)
        self._built = False
    
    def add_batch(self, ids: list[Any], vectors: np.ndarray) -> None:
        """Add batch of vectors."""
        for i, (id_, vec) in enumerate(zip(ids, vectors)):
            self.id_map[len(self._vectors)] = id_
            self._vectors.append(vec.astype(np.float32))
        self._built = False
    
    def build(self) -> None:
        """Build the search index."""
        if not self._vectors:
            logger.warning("No vectors to build index from")
            return
        
        vectors = np.vstack(self._vectors).astype(np.float32)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            vectors = vectors / norms
        
        if FAISS_AVAILABLE:
            self._build_faiss(vectors)
        else:
            self._build_numpy(vectors)
        
        self._built = True
        logger.info(f"Built index with {len(self._vectors)} vectors")
    
    def _build_faiss(self, vectors: np.ndarray) -> None:
        """Build FAISS index."""
        n = len(vectors)
        
        if self.index_type == "flat":
            if self.metric == "cosine" or self.metric == "ip":
                self.index = faiss.IndexFlatIP(self.dimension)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
        
        elif self.index_type == "ivf":
            nlist = min(int(np.sqrt(n)), 100)  # Number of clusters
            if self.metric == "cosine" or self.metric == "ip":
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            else:
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            self.index.train(vectors)
        
        elif self.index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            if self.metric == "cosine" or self.metric == "ip":
                self.index.metric_type = faiss.METRIC_INNER_PRODUCT
        
        # Move to GPU if available
        if self.use_gpu and FAISS_GPU_AVAILABLE:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS index moved to GPU")
            except Exception as e:
                logger.warning(f"Failed to move index to GPU: {e}")
        
        self.index.add(vectors)
    
    def _build_numpy(self, vectors: np.ndarray) -> None:
        """Build NumPy-based index (CPU fallback)."""
        self._numpy_vectors = vectors
    
    def search(
        self,
        query: list[float] | np.ndarray,
        k: int = 10,
        min_score: float = 0.0,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors."""
        if not self._built:
            self.build()
        
        if isinstance(query, list):
            query = np.array(query, dtype=np.float32)
        
        # Normalize query for cosine
        if self.metric == "cosine":
            norm = np.linalg.norm(query)
            if norm > 0:
                query = query / norm
        
        if FAISS_AVAILABLE and self.index is not None:
            return self._search_faiss(query, k, min_score)
        else:
            return self._search_numpy(query, k, min_score)
    
    def _search_faiss(
        self,
        query: np.ndarray,
        k: int,
        min_score: float,
    ) -> list[VectorSearchResult]:
        """Search using FAISS."""
        query = query.reshape(1, -1)
        distances, indices = self.index.search(query, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            
            score = float(dist) if self.metric in ("cosine", "ip") else 1 / (1 + float(dist))
            
            if score >= min_score:
                results.append(VectorSearchResult(
                    id=self.id_map.get(idx, idx),
                    score=score,
                    distance=float(dist),
                ))
        
        return results
    
    def _search_numpy(
        self,
        query: np.ndarray,
        k: int,
        min_score: float,
    ) -> list[VectorSearchResult]:
        """Search using NumPy (CPU fallback)."""
        if not hasattr(self, '_numpy_vectors'):
            return []
        
        # Batch cosine similarity (vectorized)
        similarities = self._numpy_vectors @ query
        
        # Get top-k indices
        top_k_idx = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_k_idx:
            score = float(similarities[idx])
            if score >= min_score:
                results.append(VectorSearchResult(
                    id=self.id_map.get(idx, idx),
                    score=score,
                    distance=1 - score,
                ))
        
        return results
    
    def save(self, path: Path) -> None:
        """Save index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save id_map
        import json
        with open(path.with_suffix('.json'), 'w') as f:
            json.dump({str(k): v for k, v in self.id_map.items()}, f)
        
        if FAISS_AVAILABLE and self.index is not None:
            # Convert GPU index to CPU for saving
            if self.use_gpu:
                cpu_index = faiss.index_gpu_to_cpu(self.index)
                faiss.write_index(cpu_index, str(path))
            else:
                faiss.write_index(self.index, str(path))
        else:
            np.save(path.with_suffix('.npy'), self._numpy_vectors)
        
        logger.info(f"Saved index to {path}")
    
    def load(self, path: Path) -> bool:
        """Load index from disk."""
        path = Path(path)
        
        # Load id_map
        import json
        map_path = path.with_suffix('.json')
        if map_path.exists():
            with open(map_path) as f:
                self.id_map = {int(k): v for k, v in json.load(f).items()}
        
        if FAISS_AVAILABLE:
            faiss_path = path
            if faiss_path.exists():
                self.index = faiss.read_index(str(faiss_path))
                
                if self.use_gpu and FAISS_GPU_AVAILABLE:
                    try:
                        res = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                    except:
                        pass
                
                self._built = True
                logger.info(f"Loaded FAISS index from {path}")
                return True
        
        npy_path = path.with_suffix('.npy')
        if npy_path.exists():
            self._numpy_vectors = np.load(npy_path)
            self._built = True
            logger.info(f"Loaded NumPy index from {npy_path}")
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear the index."""
        self.index = None
        self.id_map.clear()
        self._vectors.clear()
        self._built = False
        if hasattr(self, '_numpy_vectors'):
            del self._numpy_vectors


class VectorSearchService:
    """Unified vector search service managing multiple indices."""
    
    def __init__(self, index_dir: Optional[Path] = None):
        if index_dir is None:
            aikh_dir = Path(os.getenv("AIKH_DIR", Path.home() / ".aikh"))
            index_dir = aikh_dir / "indices"
        
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.indices: dict[str, VectorIndex] = {}
    
    def get_or_create_index(
        self,
        name: str,
        dimension: int = 384,
        use_gpu: bool = True,
    ) -> VectorIndex:
        """Get existing index or create new one."""
        if name not in self.indices:
            index = VectorIndex(dimension=dimension, use_gpu=use_gpu)
            
            # Try to load from disk
            index_path = self.index_dir / f"{name}.index"
            if index_path.exists():
                index.load(index_path)
            
            self.indices[name] = index
        
        return self.indices[name]
    
    def save_all(self) -> None:
        """Save all indices to disk."""
        for name, index in self.indices.items():
            if index._built:
                index.save(self.index_dir / f"{name}.index")
    
    def stats(self) -> dict:
        """Get stats for all indices."""
        return {
            "faiss_available": FAISS_AVAILABLE,
            "gpu_available": FAISS_GPU_AVAILABLE,
            "indices": {
                name: {
                    "vectors": len(idx._vectors) if hasattr(idx, '_vectors') else 0,
                    "built": idx._built,
                    "gpu": idx.use_gpu,
                }
                for name, idx in self.indices.items()
            }
        }


# Global instance
vector_service = VectorSearchService()


def blob_to_vector(blob: bytes) -> np.ndarray:
    """Convert SQLite BLOB to numpy vector."""
    return np.frombuffer(blob, dtype=np.float32)


def vector_to_blob(vector: np.ndarray | list) -> bytes:
    """Convert numpy vector to SQLite BLOB."""
    if isinstance(vector, list):
        vector = np.array(vector, dtype=np.float32)
    return vector.astype(np.float32).tobytes()
