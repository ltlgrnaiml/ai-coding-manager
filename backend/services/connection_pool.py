"""SQLite Connection Pool.

Thread-safe connection pooling for SQLite databases.
Reduces connection overhead across research, traces, and chat logs.
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue, Empty
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PooledConnection:
    """Wrapper for pooled SQLite connection."""
    connection: sqlite3.Connection
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    
    def is_stale(self, max_age: float = 3600) -> bool:
        """Check if connection is too old."""
        return time.time() - self.created_at > max_age


class ConnectionPool:
    """Thread-safe SQLite connection pool."""
    
    def __init__(
        self,
        db_path: Path | str,
        min_connections: int = 2,
        max_connections: int = 10,
        max_idle_time: float = 300,
        max_connection_age: float = 3600,
    ):
        self.db_path = Path(db_path)
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.max_connection_age = max_connection_age
        
        self._pool: Queue[PooledConnection] = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._active_count = 0
        self._total_created = 0
        self._total_reused = 0
        
        # Pre-populate minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Create minimum connections."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        for _ in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._pool.put(conn)
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Create new pooled connection."""
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY")
            
            self._total_created += 1
            return PooledConnection(connection=conn)
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    def get_connection(self, timeout: float = 5.0) -> Optional[sqlite3.Connection]:
        """Get connection from pool."""
        try:
            # Try to get existing connection
            pooled = self._pool.get(timeout=0.1)
            
            # Check if stale
            if pooled.is_stale(self.max_connection_age):
                pooled.connection.close()
                pooled = self._create_connection()
            
            if pooled:
                pooled.last_used = time.time()
                pooled.use_count += 1
                self._total_reused += 1
                
                with self._lock:
                    self._active_count += 1
                
                return pooled.connection
                
        except Empty:
            pass
        
        # Create new connection if under limit
        with self._lock:
            if self._active_count < self.max_connections:
                pooled = self._create_connection()
                if pooled:
                    self._active_count += 1
                    return pooled.connection
        
        # Wait for available connection
        try:
            pooled = self._pool.get(timeout=timeout)
            pooled.last_used = time.time()
            pooled.use_count += 1
            self._total_reused += 1
            
            with self._lock:
                self._active_count += 1
            
            return pooled.connection
        except Empty:
            logger.warning("Connection pool exhausted")
            return None
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool."""
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
        
        try:
            # Verify connection is still valid
            conn.execute("SELECT 1")
            
            pooled = PooledConnection(connection=conn)
            pooled.last_used = time.time()
            
            try:
                self._pool.put_nowait(pooled)
            except:
                # Pool full, close connection
                conn.close()
        except:
            # Connection broken, close it
            try:
                conn.close()
            except:
                pass
    
    @contextmanager
    def connection(self):
        """Context manager for connection."""
        conn = self.get_connection()
        if conn is None:
            raise RuntimeError("Failed to get database connection")
        
        try:
            yield conn
        finally:
            self.return_connection(conn)
    
    def stats(self) -> dict:
        """Get pool statistics."""
        return {
            "db_path": str(self.db_path),
            "pool_size": self._pool.qsize(),
            "active_connections": self._active_count,
            "max_connections": self.max_connections,
            "total_created": self._total_created,
            "total_reused": self._total_reused,
            "reuse_rate": self._total_reused / max(1, self._total_created + self._total_reused),
        }
    
    def close_all(self) -> None:
        """Close all connections."""
        while not self._pool.empty():
            try:
                pooled = self._pool.get_nowait()
                pooled.connection.close()
            except:
                pass
        
        with self._lock:
            self._active_count = 0


class PoolManager:
    """Manages connection pools for multiple databases."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._pools = {}
        return cls._instance
    
    def get_pool(self, db_path: Path | str, **kwargs) -> ConnectionPool:
        """Get or create pool for database."""
        db_path = str(db_path)
        
        if db_path not in self._pools:
            self._pools[db_path] = ConnectionPool(db_path, **kwargs)
        
        return self._pools[db_path]
    
    def stats(self) -> dict:
        """Get stats for all pools."""
        return {
            path: pool.stats()
            for path, pool in self._pools.items()
        }
    
    def close_all(self) -> None:
        """Close all pools."""
        for pool in self._pools.values():
            pool.close_all()
        self._pools.clear()


# Global pool manager
pool_manager = PoolManager()


def get_pooled_connection(db_path: Path | str) -> sqlite3.Connection:
    """Get connection from pool for database."""
    pool = pool_manager.get_pool(db_path)
    conn = pool.get_connection()
    if conn is None:
        raise RuntimeError(f"Failed to get connection for {db_path}")
    return conn


@contextmanager
def pooled_connection(db_path: Path | str):
    """Context manager for pooled connection."""
    pool = pool_manager.get_pool(db_path)
    with pool.connection() as conn:
        yield conn
