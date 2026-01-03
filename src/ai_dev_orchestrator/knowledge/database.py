"""AIKH Artifacts Database Schema and Initialization.

AI Knowledge Hub (AIKH) - Artifacts Store
SQLite database with FTS5 for full-text search and vector storage for embeddings.

This database stores:
- Documents (ADRs, specs, plans, etc.)
- Chunks for RAG retrieval
- Embeddings for semantic search
- Document relationships for graph-aware retrieval
- LLM call history
"""

import os
import sqlite3
from pathlib import Path

from .aikh_config import get_database_path, ARTIFACTS_DB_PATH

# Legacy support - prefer AIKH path, fallback to workspace
WORKSPACE_DIR = Path(os.getenv("AI_DEV_WORKSPACE", ".workspace"))
DB_PATH = ARTIFACTS_DB_PATH  # Now uses ~/.aikh/artifacts.db

SCHEMA = """
-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    archived_at TEXT DEFAULT NULL
);

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    UNIQUE(doc_id, chunk_index)
);

-- Embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Relationships table (for graph-aware retrieval)
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL REFERENCES documents(id),
    target_id TEXT NOT NULL REFERENCES documents(id),
    relationship_type TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source_id, target_id, relationship_type)
);

-- LLM Calls table (for tracking RAG queries)
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    model TEXT NOT NULL,
    prompt TEXT,
    response TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
    title, content, doc_id UNINDEXED, content='documents', content_rowid='rowid'
);

-- Triggers for FTS sync
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO content_fts(rowid, title, content, doc_id) VALUES (new.rowid, new.title, new.content, new.id);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO content_fts(content_fts, rowid, title, content, doc_id) VALUES ('delete', old.rowid, old.title, old.content, old.id);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO content_fts(content_fts, rowid, title, content, doc_id) VALUES ('delete', old.rowid, old.title, old.content, old.id);
    INSERT INTO content_fts(rowid, title, content, doc_id) VALUES (new.rowid, new.title, new.content, new.id);
END;

-- Updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_documents_timestamp AFTER UPDATE ON documents BEGIN
    UPDATE documents SET updated_at = datetime('now') WHERE id = new.id;
END;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_archived ON documents(archived_at);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);

-- Chat Sessions table (canonical session, may span multiple source files)
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    first_message_at TEXT,
    last_message_at TEXT,
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    assistant_message_count INTEGER DEFAULT 0,
    topics TEXT,  -- JSON array of topics
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Chat Messages table (individual messages with dedup via content_hash)
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    content_hash TEXT NOT NULL,  -- SHA256 of normalized(role + content) for dedup
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sequence_num INTEGER NOT NULL,  -- Order within session
    timestamp TEXT,
    source_file TEXT,  -- Which file this was imported from
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(session_id, content_hash)  -- Prevent duplicate messages in same session
);

-- Chat Source Files table (track which files contributed to which sessions)
CREATE TABLE IF NOT EXISTS chat_source_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    new_messages INTEGER DEFAULT 0,  -- Messages added from this file (vs duplicates)
    imported_at TEXT DEFAULT (datetime('now')),
    UNIQUE(session_id, file_path)
);

-- Message embeddings for similarity search
CREATE TABLE IF NOT EXISTS message_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(message_id, model)
);

-- Chat indexes
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_chat_messages_hash ON chat_messages(content_hash);
CREATE INDEX IF NOT EXISTS idx_chat_source_files_session ON chat_source_files(session_id);
CREATE INDEX IF NOT EXISTS idx_message_embeddings_message ON message_embeddings(message_id);

-- Trigger to update chat_sessions.updated_at
CREATE TRIGGER IF NOT EXISTS update_chat_sessions_timestamp AFTER UPDATE ON chat_sessions BEGIN
    UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = new.id;
END;
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get database connection with row factory.
    
    Args:
        db_path: Optional custom database path.
        
    Returns:
        SQLite connection with Row factory enabled.
    """
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize database with schema.
    
    Args:
        db_path: Optional custom database path.
        
    Returns:
        Initialized database connection.
    """
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
