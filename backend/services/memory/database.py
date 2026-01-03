"""Memory Architecture - Database Layer.

SQLite storage for conversation memory with full indexing and FTS5 support.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    Memory, MemorySession, MemoryType, MessageRole,
    AssembledContext, ContextSection, ContextSectionType, DebugInfo,
    SharedMemoryEntry, AgentScope, AgentHandoff
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0.0"


def get_memory_db_path() -> Path:
    """Get path to memory database."""
    aikh_dir = Path(os.getenv("AIKH_DIR", Path.home() / ".aikh"))
    aikh_dir.mkdir(parents=True, exist_ok=True)
    return aikh_dir / "memory.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with optimized settings."""
    db_path = get_memory_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def init_database() -> None:
    """Initialize the memory database schema."""
    conn = get_connection()
    try:
        conn.executescript("""
            -- Schema version tracking
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            );
            
            -- Memory sessions (conversations)
            CREATE TABLE IF NOT EXISTS memory_sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT,
                summary TEXT,
                summary_hash TEXT,
                total_messages INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            );
            
            -- Individual memories
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES memory_sessions(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                role TEXT,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                embedding BLOB,
                tokens INTEGER NOT NULL DEFAULT 0,
                priority INTEGER DEFAULT 50,
                pinned BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL,
                metadata TEXT
            );
            
            -- Pinned memories (user-specified important context)
            CREATE TABLE IF NOT EXISTS pinned_memories (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES memory_sessions(id) ON DELETE CASCADE,
                memory_id TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                label TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(session_id, memory_id)
            );
            
            -- Assembled contexts (for debugging/replay)
            CREATE TABLE IF NOT EXISTS assembled_contexts (
                id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES memory_sessions(id),
                context_hash TEXT NOT NULL,
                model_id TEXT NOT NULL,
                token_budget INTEGER NOT NULL,
                tokens_used INTEGER NOT NULL,
                sections TEXT NOT NULL,
                messages TEXT NOT NULL,
                debug_info TEXT,
                created_at TEXT NOT NULL,
                trace_id TEXT
            );
            
            -- Shared agent memory
            CREATE TABLE IF NOT EXISTS shared_memory (
                key TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                scope TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                version INTEGER DEFAULT 1,
                PRIMARY KEY (key, agent_id, scope)
            );
            
            -- Agent handoffs
            CREATE TABLE IF NOT EXISTS agent_handoffs (
                id TEXT PRIMARY KEY,
                from_agent TEXT NOT NULL,
                to_agent TEXT NOT NULL,
                session_id TEXT REFERENCES memory_sessions(id),
                state TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL
            );
            
            -- Full-text search on memory content
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content,
                content='memories',
                content_rowid='rowid'
            );
            
            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
            
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
            END;
            
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
                INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
            END;
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
            CREATE INDEX IF NOT EXISTS idx_memories_pinned ON memories(pinned) WHERE pinned = TRUE;
            CREATE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_hash);
            CREATE INDEX IF NOT EXISTS idx_contexts_session ON assembled_contexts(session_id);
            CREATE INDEX IF NOT EXISTS idx_contexts_hash ON assembled_contexts(context_hash);
            CREATE INDEX IF NOT EXISTS idx_contexts_created ON assembled_contexts(created_at);
            CREATE INDEX IF NOT EXISTS idx_shared_scope ON shared_memory(scope);
            CREATE INDEX IF NOT EXISTS idx_handoffs_session ON agent_handoffs(session_id);
        """)
        
        # Record schema version
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, datetime.utcnow().isoformat())
        )
        conn.commit()
        logger.info(f"Memory database initialized at {get_memory_db_path()}")
    finally:
        conn.close()


# =============================================================================
# Session Operations
# =============================================================================

def create_session(session: MemorySession) -> MemorySession:
    """Create a new memory session."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO memory_sessions 
               (id, name, created_at, updated_at, metadata, summary, summary_hash, total_messages, total_tokens)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.id,
                session.name,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                json.dumps(session.metadata) if session.metadata else None,
                session.summary,
                session.summary_hash,
                session.total_messages,
                session.total_tokens,
            )
        )
        conn.commit()
        return session
    finally:
        conn.close()


def get_session(session_id: str) -> Optional[MemorySession]:
    """Get a session by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM memory_sessions WHERE id = ?",
            (session_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return _row_to_session(row)
    finally:
        conn.close()


def list_sessions(limit: int = 50, offset: int = 0) -> list[MemorySession]:
    """List sessions ordered by update time."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM memory_sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        
        return [_row_to_session(row) for row in rows]
    finally:
        conn.close()


def update_session(session: MemorySession) -> None:
    """Update session metadata."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE memory_sessions SET
               name = ?, updated_at = ?, metadata = ?, summary = ?, summary_hash = ?,
               total_messages = ?, total_tokens = ?
               WHERE id = ?""",
            (
                session.name,
                datetime.utcnow().isoformat(),
                json.dumps(session.metadata) if session.metadata else None,
                session.summary,
                session.summary_hash,
                session.total_messages,
                session.total_tokens,
                session.id,
            )
        )
        conn.commit()
    finally:
        conn.close()


def delete_session(session_id: str) -> bool:
    """Delete a session and all its memories."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM memory_sessions WHERE id = ?",
            (session_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# =============================================================================
# Memory Operations
# =============================================================================

def add_memory(memory: Memory) -> Memory:
    """Add a memory to the database."""
    conn = get_connection()
    try:
        embedding_blob = None
        if memory.embedding:
            import struct
            embedding_blob = struct.pack(f'{len(memory.embedding)}f', *memory.embedding)
        
        conn.execute(
            """INSERT INTO memories
               (id, session_id, type, role, content, content_hash, embedding, tokens, priority, pinned, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.id,
                memory.session_id,
                memory.type.value,
                memory.role.value if memory.role else None,
                memory.content,
                memory.content_hash,
                embedding_blob,
                memory.tokens,
                memory.priority,
                memory.pinned,
                memory.created_at.isoformat(),
                json.dumps(memory.metadata) if memory.metadata else None,
            )
        )
        
        # Update session stats
        if memory.session_id:
            conn.execute(
                """UPDATE memory_sessions SET
                   total_messages = total_messages + 1,
                   total_tokens = total_tokens + ?,
                   updated_at = ?
                   WHERE id = ?""",
                (memory.tokens, datetime.utcnow().isoformat(), memory.session_id)
            )
        
        conn.commit()
        return memory
    finally:
        conn.close()


def get_memory(memory_id: str) -> Optional[Memory]:
    """Get a memory by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?",
            (memory_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return _row_to_memory(row)
    finally:
        conn.close()


def get_session_memories(
    session_id: str,
    types: Optional[list[MemoryType]] = None,
    limit: int = 100,
    offset: int = 0,
    pinned_only: bool = False,
) -> list[Memory]:
    """Get memories for a session."""
    conn = get_connection()
    try:
        query = "SELECT * FROM memories WHERE session_id = ?"
        params: list = [session_id]
        
        if types:
            placeholders = ",".join("?" * len(types))
            query += f" AND type IN ({placeholders})"
            params.extend(t.value for t in types)
        
        if pinned_only:
            query += " AND pinned = TRUE"
        
        query += " ORDER BY created_at ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        return [_row_to_memory(row) for row in rows]
    finally:
        conn.close()


def get_recent_memories(
    session_id: str,
    limit: int = 20,
) -> list[Memory]:
    """Get most recent memories for a session."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM memories 
               WHERE session_id = ? AND type = 'message'
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, limit)
        ).fetchall()
        
        # Return in chronological order
        return [_row_to_memory(row) for row in reversed(rows)]
    finally:
        conn.close()


def search_memories_fts(
    query: str,
    session_id: Optional[str] = None,
    limit: int = 10,
) -> list[Memory]:
    """Full-text search on memories."""
    # Sanitize query for FTS5 - escape special characters
    # FTS5 special chars: AND OR NOT ( ) " * : ^
    sanitized = query.replace('"', '""')
    # Wrap in quotes to treat as phrase search (safe)
    fts_query = f'"{sanitized}"'
    
    conn = get_connection()
    try:
        if session_id:
            rows = conn.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts fts ON m.rowid = fts.rowid
                   WHERE memories_fts MATCH ? AND m.session_id = ?
                   ORDER BY rank LIMIT ?""",
                (fts_query, session_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts fts ON m.rowid = fts.rowid
                   WHERE memories_fts MATCH ?
                   ORDER BY rank LIMIT ?""",
                (fts_query, limit)
            ).fetchall()
        
        return [_row_to_memory(row) for row in rows]
    except sqlite3.OperationalError as e:
        # FTS query failed - fall back to LIKE search
        logger.warning(f"FTS search failed, falling back to LIKE: {e}")
        if session_id:
            rows = conn.execute(
                """SELECT * FROM memories 
                   WHERE session_id = ? AND content LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (session_id, f"%{query}%", limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM memories 
                   WHERE content LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (f"%{query}%", limit)
            ).fetchall()
        
        return [_row_to_memory(row) for row in rows]
    finally:
        conn.close()


def pin_memory(session_id: str, memory_id: str, label: Optional[str] = None) -> bool:
    """Pin a memory for persistent inclusion."""
    conn = get_connection()
    try:
        # Update memory
        conn.execute(
            "UPDATE memories SET pinned = TRUE WHERE id = ?",
            (memory_id,)
        )
        
        # Add to pinned table
        pin_id = f"pin_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        conn.execute(
            """INSERT OR REPLACE INTO pinned_memories (id, session_id, memory_id, label, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (pin_id, session_id, memory_id, label, datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to pin memory: {e}")
        return False
    finally:
        conn.close()


def unpin_memory(session_id: str, memory_id: str) -> bool:
    """Unpin a memory."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE memories SET pinned = FALSE WHERE id = ?",
            (memory_id,)
        )
        conn.execute(
            "DELETE FROM pinned_memories WHERE session_id = ? AND memory_id = ?",
            (session_id, memory_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to unpin memory: {e}")
        return False
    finally:
        conn.close()


# =============================================================================
# Context Operations
# =============================================================================

def save_context(context: AssembledContext) -> None:
    """Save an assembled context for debugging/replay."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO assembled_contexts
               (id, session_id, context_hash, model_id, token_budget, tokens_used,
                sections, messages, debug_info, created_at, trace_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                context.context_id,
                context.session_id,
                context.context_hash,
                context.model_id,
                context.token_budget,
                context.tokens_used,
                json.dumps([s.model_dump() for s in context.sections]),
                json.dumps(context.messages),
                json.dumps(context.debug_info.model_dump()) if context.debug_info else None,
                context.assembled_at.isoformat(),
                context.trace_id,
            )
        )
        conn.commit()
    finally:
        conn.close()


def get_context(context_id: str) -> Optional[AssembledContext]:
    """Get a saved context by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM assembled_contexts WHERE id = ?",
            (context_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return _row_to_context(row)
    finally:
        conn.close()


def get_context_by_hash(context_hash: str) -> Optional[AssembledContext]:
    """Get a context by its deterministic hash."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM assembled_contexts WHERE context_hash = ? ORDER BY created_at DESC LIMIT 1",
            (context_hash,)
        ).fetchone()
        
        if not row:
            return None
        
        return _row_to_context(row)
    finally:
        conn.close()


def list_session_contexts(session_id: str, limit: int = 20) -> list[dict]:
    """List context assemblies for a session (summary only)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, context_hash, model_id, token_budget, tokens_used, created_at, trace_id
               FROM assembled_contexts WHERE session_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, limit)
        ).fetchall()
        
        return [dict(row) for row in rows]
    finally:
        conn.close()


# =============================================================================
# Shared Memory Operations (Agentic)
# =============================================================================

def set_shared_memory(entry: SharedMemoryEntry) -> None:
    """Set a shared memory entry."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO shared_memory
               (key, agent_id, scope, value, created_at, expires_at, version)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.key,
                entry.agent_id,
                entry.scope.value,
                json.dumps(entry.value),
                entry.created_at.isoformat(),
                entry.expires_at.isoformat() if entry.expires_at else None,
                entry.version,
            )
        )
        conn.commit()
    finally:
        conn.close()


def get_shared_memory(key: str, scope: AgentScope) -> list[SharedMemoryEntry]:
    """Get all entries for a key within scope."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM shared_memory WHERE key = ? AND scope = ?",
            (key, scope.value)
        ).fetchall()
        
        return [_row_to_shared_entry(row) for row in rows]
    finally:
        conn.close()


def save_handoff(handoff: AgentHandoff) -> None:
    """Save an agent handoff."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO agent_handoffs
               (id, from_agent, to_agent, session_id, state, summary, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                handoff.id,
                handoff.from_agent,
                handoff.to_agent,
                handoff.session_id,
                json.dumps(handoff.state),
                handoff.summary,
                handoff.created_at.isoformat(),
            )
        )
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# Statistics
# =============================================================================

def get_stats() -> dict:
    """Get memory system statistics."""
    conn = get_connection()
    try:
        stats = {}
        
        # Total counts
        stats["total_sessions"] = conn.execute(
            "SELECT COUNT(*) FROM memory_sessions"
        ).fetchone()[0]
        
        stats["total_memories"] = conn.execute(
            "SELECT COUNT(*) FROM memories"
        ).fetchone()[0]
        
        stats["total_tokens"] = conn.execute(
            "SELECT COALESCE(SUM(tokens), 0) FROM memories"
        ).fetchone()[0]
        
        stats["total_contexts"] = conn.execute(
            "SELECT COUNT(*) FROM assembled_contexts"
        ).fetchone()[0]
        
        # By type
        type_counts = conn.execute(
            "SELECT type, COUNT(*) as count FROM memories GROUP BY type"
        ).fetchall()
        stats["memories_by_type"] = {row["type"]: row["count"] for row in type_counts}
        
        # Top sessions
        top_sessions = conn.execute(
            """SELECT id, name, total_messages, total_tokens, updated_at
               FROM memory_sessions ORDER BY total_messages DESC LIMIT 5"""
        ).fetchall()
        stats["top_sessions"] = [dict(row) for row in top_sessions]
        
        return stats
    finally:
        conn.close()


# =============================================================================
# Helper Functions
# =============================================================================

def _row_to_session(row) -> MemorySession:
    """Convert database row to MemorySession."""
    return MemorySession(
        id=row["id"],
        name=row["name"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        summary=row["summary"],
        summary_hash=row["summary_hash"],
        total_messages=row["total_messages"],
        total_tokens=row["total_tokens"],
    )


def _row_to_memory(row) -> Memory:
    """Convert database row to Memory."""
    embedding = None
    if row["embedding"]:
        import struct
        blob = row["embedding"]
        count = len(blob) // 4
        embedding = list(struct.unpack(f'{count}f', blob))
    
    return Memory(
        id=row["id"],
        session_id=row["session_id"],
        type=MemoryType(row["type"]),
        role=MessageRole(row["role"]) if row["role"] else None,
        content=row["content"],
        tokens=row["tokens"],
        priority=row["priority"],
        pinned=bool(row["pinned"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        embedding=embedding,
    )


def _row_to_context(row) -> AssembledContext:
    """Convert database row to AssembledContext."""
    sections_data = json.loads(row["sections"])
    sections = [
        ContextSection(
            type=ContextSectionType(s["type"]),
            content=s["content"],
            tokens=s["tokens"],
            priority=s["priority"],
            source_ids=s.get("source_ids", []),
            metadata=s.get("metadata", {}),
        )
        for s in sections_data
    ]
    
    debug_info = None
    if row["debug_info"]:
        debug_data = json.loads(row["debug_info"])
        debug_info = DebugInfo(**debug_data)
    
    return AssembledContext(
        context_id=row["id"],
        session_id=row["session_id"],
        assembled_at=datetime.fromisoformat(row["created_at"]),
        model_id=row["model_id"],
        token_budget=row["token_budget"],
        tokens_used=row["tokens_used"],
        sections=sections,
        messages=json.loads(row["messages"]),
        debug_info=debug_info,
        trace_id=row["trace_id"],
    )


def _row_to_shared_entry(row) -> SharedMemoryEntry:
    """Convert database row to SharedMemoryEntry."""
    return SharedMemoryEntry(
        key=row["key"],
        agent_id=row["agent_id"],
        scope=AgentScope(row["scope"]),
        value=json.loads(row["value"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        expires_at=datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None,
        version=row["version"],
    )
