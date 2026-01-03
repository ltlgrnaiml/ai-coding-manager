"""Lazy Loading Service for Large Data.

Provides deferred loading and streaming for:
- PDF files (BLOBs)
- Images
- Large text content
- Embeddings

Applies to: research papers, chat logs, traces
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Generic, Optional, TypeVar
import sqlite3

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class LazyRef(Generic[T]):
    """Lazy reference to data - loads on first access."""
    
    loader: Callable[[], T]
    _value: Optional[T] = field(default=None, repr=False)
    _loaded: bool = False
    
    @property
    def value(self) -> T:
        """Get value, loading if necessary."""
        if not self._loaded:
            self._value = self.loader()
            self._loaded = True
        return self._value
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    def unload(self) -> None:
        """Unload value to free memory."""
        self._value = None
        self._loaded = False


@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result set."""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size


class LazyBlobLoader:
    """Lazy loader for database BLOBs."""
    
    def __init__(self, db_path: Path | str, chunk_size: int = 1024 * 1024):
        self.db_path = Path(db_path)
        self.chunk_size = chunk_size  # 1MB chunks
    
    def get_blob_size(self, table: str, column: str, row_id: int | str, id_column: str = "id") -> int:
        """Get BLOB size without loading data."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                f"SELECT length({column}) FROM {table} WHERE {id_column} = ?",
                (row_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            conn.close()
    
    def get_blob_lazy(
        self, 
        table: str, 
        column: str, 
        row_id: int | str,
        id_column: str = "id"
    ) -> LazyRef[bytes]:
        """Get lazy reference to BLOB data."""
        def loader() -> bytes:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    f"SELECT {column} FROM {table} WHERE {id_column} = ?",
                    (row_id,)
                )
                row = cursor.fetchone()
                return row[0] if row else b""
            finally:
                conn.close()
        
        return LazyRef(loader=loader)
    
    async def stream_blob(
        self,
        table: str,
        column: str,
        row_id: int | str,
        id_column: str = "id"
    ) -> AsyncIterator[bytes]:
        """Stream BLOB data in chunks."""
        size = self.get_blob_size(table, column, row_id, id_column)
        
        conn = sqlite3.connect(str(self.db_path))
        try:
            offset = 0
            while offset < size:
                cursor = conn.execute(
                    f"SELECT substr({column}, ?, ?) FROM {table} WHERE {id_column} = ?",
                    (offset + 1, self.chunk_size, row_id)  # SQLite substr is 1-indexed
                )
                row = cursor.fetchone()
                if not row or not row[0]:
                    break
                
                yield row[0]
                offset += self.chunk_size
                
                # Yield control to event loop
                await asyncio.sleep(0)
        finally:
            conn.close()
    
    def get_blob_range(
        self,
        table: str,
        column: str,
        row_id: int | str,
        start: int,
        length: int,
        id_column: str = "id"
    ) -> bytes:
        """Get range of BLOB data (for HTTP range requests)."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                f"SELECT substr({column}, ?, ?) FROM {table} WHERE {id_column} = ?",
                (start + 1, length, row_id)  # SQLite substr is 1-indexed
            )
            row = cursor.fetchone()
            return row[0] if row else b""
        finally:
            conn.close()


class PaginatedQuery:
    """Paginated database queries."""
    
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
    
    def query(
        self,
        sql: str,
        params: tuple = (),
        page: int = 1,
        page_size: int = 20,
        count_sql: Optional[str] = None,
    ) -> PaginatedResult[dict]:
        """Execute paginated query."""
        offset = (page - 1) * page_size
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            # Get total count
            if count_sql:
                cursor = conn.execute(count_sql, params)
            else:
                # Auto-generate count query
                count_query = f"SELECT COUNT(*) FROM ({sql.split('ORDER BY')[0].split('LIMIT')[0]})"
                cursor = conn.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get page of results
            paginated_sql = f"{sql} LIMIT ? OFFSET ?"
            cursor = conn.execute(paginated_sql, params + (page_size, offset))
            items = [dict(row) for row in cursor.fetchall()]
            
            return PaginatedResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                has_next=offset + page_size < total,
                has_prev=page > 1,
            )
        finally:
            conn.close()


class VirtualizedList:
    """Virtualized list for UI rendering optimization."""
    
    def __init__(
        self,
        fetch_func: Callable[[int, int], list[Any]],
        total_count: int,
        window_size: int = 50,
        buffer_size: int = 10,
    ):
        self.fetch_func = fetch_func
        self.total_count = total_count
        self.window_size = window_size
        self.buffer_size = buffer_size
        
        self._cache: dict[int, Any] = {}
        self._loaded_ranges: list[tuple[int, int]] = []
    
    def get_window(self, start_index: int) -> list[Any]:
        """Get items for current window with buffering."""
        # Calculate buffered range
        buffer_start = max(0, start_index - self.buffer_size)
        buffer_end = min(self.total_count, start_index + self.window_size + self.buffer_size)
        
        # Find items not in cache
        missing_ranges = self._find_missing_ranges(buffer_start, buffer_end)
        
        # Fetch missing items
        for range_start, range_end in missing_ranges:
            items = self.fetch_func(range_start, range_end - range_start)
            for i, item in enumerate(items):
                self._cache[range_start + i] = item
        
        # Return window items
        return [
            self._cache.get(i) 
            for i in range(start_index, min(start_index + self.window_size, self.total_count))
        ]
    
    def _find_missing_ranges(self, start: int, end: int) -> list[tuple[int, int]]:
        """Find ranges not in cache."""
        missing = []
        current_start = None
        
        for i in range(start, end):
            if i not in self._cache:
                if current_start is None:
                    current_start = i
            else:
                if current_start is not None:
                    missing.append((current_start, i))
                    current_start = None
        
        if current_start is not None:
            missing.append((current_start, end))
        
        return missing
    
    def clear_cache(self) -> None:
        """Clear item cache."""
        self._cache.clear()


def create_paper_lazy_loader() -> LazyBlobLoader:
    """Create lazy loader for research papers."""
    from .p2re.database import get_database_path
    import os
    
    aikh_dir = Path(os.getenv("AIKH_DIR", Path.home() / ".aikh"))
    research_db = aikh_dir / "research.db"
    
    return LazyBlobLoader(research_db)


def create_trace_paginator() -> PaginatedQuery:
    """Create paginated query for traces."""
    from .p2re.database import get_database_path
    
    return PaginatedQuery(get_database_path())
