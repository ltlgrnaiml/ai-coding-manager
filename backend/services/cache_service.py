"""Unified Caching Service.

Multi-tier caching system for research papers, chat logs, traces, and embeddings.
Supports:
- L1: In-memory LRU cache (hot data)
- L2: SQLite cache (warm data)
- L3: Optional Redis (distributed)

Cross-pollinates to: research papers, chat logs, P2RE traces
"""

import hashlib
import json
import logging
import sqlite3
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Generic, TypeVar, Optional
import os

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    key: str
    value: T
    created_at: float
    expires_at: Optional[float] = None
    hit_count: int = 0
    size_bytes: int = 0
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with size limits."""
    
    def __init__(
        self, 
        max_items: int = 1000, 
        max_size_mb: float = 100,
        ttl_seconds: Optional[float] = None
    ):
        self.max_items = max_items
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.ttl_seconds = ttl_seconds
        
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = Lock()
        self._current_size = 0
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[T]:
        """Get item from cache."""
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired:
                self._remove(key)
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hit_count += 1
            self.hits += 1
            
            return entry.value
    
    def set(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Set item in cache."""
        # Estimate size (rough)
        try:
            size_bytes = len(json.dumps(value, default=str))
        except:
            size_bytes = 1024  # Default 1KB
        
        expires_at = None
        if ttl or self.ttl_seconds:
            expires_at = time.time() + (ttl or self.ttl_seconds)
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
            size_bytes=size_bytes
        )
        
        with self._lock:
            # Remove old entry if exists
            if key in self._cache:
                self._remove(key)
            
            # Evict if needed
            while (
                len(self._cache) >= self.max_items or 
                self._current_size + size_bytes > self.max_size_bytes
            ):
                if not self._cache:
                    break
                self._evict_lru()
            
            self._cache[key] = entry
            self._current_size += size_bytes
    
    def invalidate(self, key: str) -> bool:
        """Remove item from cache."""
        with self._lock:
            if key in self._cache:
                self._remove(key)
                return True
            return False
    
    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all items with key prefix."""
        with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_remove:
                self._remove(key)
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._current_size = 0
    
    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total = self.hits + self.misses
            return {
                "items": len(self._cache),
                "size_mb": self._current_size / (1024 * 1024),
                "max_items": self.max_items,
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": self.hits / total if total > 0 else 0,
            }
    
    def _remove(self, key: str) -> None:
        """Remove entry (caller must hold lock)."""
        if key in self._cache:
            self._current_size -= self._cache[key].size_bytes
            del self._cache[key]
    
    def _evict_lru(self) -> None:
        """Evict least recently used (caller must hold lock)."""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self._current_size -= entry.size_bytes


class SQLiteCache:
    """SQLite-backed persistent cache for larger/warm data."""
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS cache_entries (
        key TEXT PRIMARY KEY,
        value BLOB NOT NULL,
        value_type TEXT NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL,
        hit_count INTEGER DEFAULT 0,
        size_bytes INTEGER DEFAULT 0,
        namespace TEXT DEFAULT 'default'
    );
    
    CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at);
    CREATE INDEX IF NOT EXISTS idx_cache_namespace ON cache_entries(namespace);
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            aikh_dir = Path(os.getenv("AIKH_DIR", Path.home() / ".aikh"))
            aikh_dir.mkdir(parents=True, exist_ok=True)
            db_path = aikh_dir / "cache.db"
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize cache database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.executescript(self.SCHEMA)
        conn.commit()
        conn.close()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get item from cache."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """
                SELECT value, value_type, expires_at 
                FROM cache_entries 
                WHERE key = ? AND namespace = ?
                """,
                (key, namespace)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Check expiration
            if row["expires_at"] and time.time() > row["expires_at"]:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return None
            
            # Update hit count
            conn.execute(
                "UPDATE cache_entries SET hit_count = hit_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            
            # Deserialize
            return self._deserialize(row["value"], row["value_type"])
        finally:
            conn.close()
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[float] = None,
        namespace: str = "default"
    ) -> None:
        """Set item in cache."""
        serialized, value_type = self._serialize(value)
        expires_at = time.time() + ttl if ttl else None
        
        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries 
                (key, value, value_type, created_at, expires_at, size_bytes, namespace)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (key, serialized, value_type, time.time(), expires_at, len(serialized), namespace)
            )
            conn.commit()
        finally:
            conn.close()
    
    def invalidate(self, key: str, namespace: str = "default") -> bool:
        """Remove item from cache."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE key = ? AND namespace = ?",
                (key, namespace)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    def stats(self, namespace: Optional[str] = None) -> dict:
        """Get cache statistics."""
        conn = self._get_conn()
        try:
            if namespace:
                cursor = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as items,
                        SUM(size_bytes) as total_size,
                        SUM(hit_count) as total_hits
                    FROM cache_entries WHERE namespace = ?
                    """,
                    (namespace,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as items,
                        SUM(size_bytes) as total_size,
                        SUM(hit_count) as total_hits
                    FROM cache_entries
                    """
                )
            row = cursor.fetchone()
            return {
                "items": row["items"] or 0,
                "size_mb": (row["total_size"] or 0) / (1024 * 1024),
                "total_hits": row["total_hits"] or 0,
            }
        finally:
            conn.close()
    
    def _serialize(self, value: Any) -> tuple[bytes, str]:
        """Serialize value to bytes."""
        if isinstance(value, bytes):
            return value, "bytes"
        elif isinstance(value, str):
            return value.encode("utf-8"), "str"
        else:
            return json.dumps(value, default=str).encode("utf-8"), "json"
    
    def _deserialize(self, data: bytes, value_type: str) -> Any:
        """Deserialize bytes to value."""
        if value_type == "bytes":
            return data
        elif value_type == "str":
            return data.decode("utf-8")
        else:
            return json.loads(data.decode("utf-8"))


# =============================================================================
# Cache Decorators
# =============================================================================

def cached(
    cache: LRUCache,
    key_prefix: str = "",
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., str]] = None,
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper.cache = cache
        wrapper.cache_key_prefix = key_prefix
        return wrapper
    
    return decorator


def cached_async(
    cache: LRUCache,
    key_prefix: str = "",
    ttl: Optional[float] = None,
):
    """Decorator for caching async function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


# =============================================================================
# Global Cache Instances
# =============================================================================

# Research paper cache (hot queries)
research_cache = LRUCache[dict](
    max_items=500,
    max_size_mb=50,
    ttl_seconds=3600  # 1 hour
)

# Embedding cache (frequently accessed vectors)
embedding_cache = LRUCache[list](
    max_items=10000,
    max_size_mb=200,
    ttl_seconds=86400  # 24 hours
)

# Query result cache (search results)
query_cache = LRUCache[list](
    max_items=1000,
    max_size_mb=100,
    ttl_seconds=300  # 5 minutes
)

# Chat/Trace cache
trace_cache = LRUCache[dict](
    max_items=500,
    max_size_mb=50,
    ttl_seconds=600  # 10 minutes
)

# Persistent cache (warm data)
persistent_cache = SQLiteCache()


def cache_key(*args) -> str:
    """Generate cache key from arguments."""
    raw = ":".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def get_cache_stats() -> dict:
    """Get stats for all caches."""
    return {
        "research": research_cache.stats(),
        "embedding": embedding_cache.stats(),
        "query": query_cache.stats(),
        "trace": trace_cache.stats(),
        "persistent": persistent_cache.stats(),
    }


def clear_all_caches() -> None:
    """Clear all in-memory caches."""
    research_cache.clear()
    embedding_cache.clear()
    query_cache.clear()
    trace_cache.clear()
