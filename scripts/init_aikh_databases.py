#!/usr/bin/env python3
"""Initialize all AIKH (AI Knowledge Hub) databases.

This script creates and initializes the three core AIKH databases:
1. Artifacts DB - Documents, chunks, embeddings, relationships
2. Chatlogs DB - Cross-project chat history
3. Research DB - Academic papers and citations

Usage:
    python scripts/init_aikh_databases.py
"""

import os
import sys
import sqlite3
from pathlib import Path

# AIKH Configuration - standalone (no package imports needed)
AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
ARTIFACTS_DB_PATH = AIKH_HOME / "artifacts.db"
CHATLOGS_DB_PATH = AIKH_HOME / "chatlogs.db"
RESEARCH_DB_PATH = AIKH_HOME / "research.db"

# =============================================================================
# Schema Definitions
# =============================================================================

ARTIFACTS_SCHEMA = """
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

-- LLM Calls table
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_archived ON documents(archived_at);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
"""

CHATLOGS_SCHEMA = """
-- Core chat log table
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    title TEXT,
    file_size INTEGER,
    created_date TEXT,
    modified_date TEXT,
    turn_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    projects_referenced TEXT,
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Individual conversation turns
CREATE TABLE IF NOT EXISTS chat_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_index INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    has_code_blocks INTEGER DEFAULT 0,
    has_file_refs INTEGER DEFAULT 0,
    has_commands INTEGER DEFAULT 0,
    UNIQUE(chat_log_id, turn_index)
);

-- Extracted file references
CREATE TABLE IF NOT EXISTS chat_file_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    project_name TEXT
);

-- Extracted commands
CREATE TABLE IF NOT EXISTS chat_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    was_accepted INTEGER DEFAULT 0
);

-- Embeddings for semantic search
CREATE TABLE IF NOT EXISTS chat_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id),
    embedding BLOB NOT NULL,
    embedding_model TEXT DEFAULT 'all-mpnet-base-v2',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS chat_fts USING fts5(
    content, filename, title,
    content='chat_turns',
    content_rowid='id',
    tokenize='porter'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chat_turns_log ON chat_turns(chat_log_id);
CREATE INDEX IF NOT EXISTS idx_chat_file_refs_log ON chat_file_refs(chat_log_id);
CREATE INDEX IF NOT EXISTS idx_chat_commands_log ON chat_commands(chat_log_id);
"""

RESEARCH_SCHEMA = """
-- Research papers table with academic metadata
CREATE TABLE IF NOT EXISTS research_papers (
    id TEXT PRIMARY KEY,
    arxiv_id TEXT UNIQUE,
    doi TEXT UNIQUE,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    publication_date TEXT,
    venue TEXT,
    keywords TEXT,
    source_path TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    page_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    table_count INTEGER DEFAULT 0,
    extraction_date TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Paper sections table
CREATE TABLE IF NOT EXISTS paper_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    section_content TEXT NOT NULL,
    section_order INTEGER DEFAULT 0,
    UNIQUE(paper_id, section_name)
);

-- Paper chunks table for RAG
CREATE TABLE IF NOT EXISTS paper_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    section_id INTEGER REFERENCES paper_sections(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    chunk_type TEXT DEFAULT 'text',
    UNIQUE(paper_id, chunk_index)
);

-- Paper embeddings table
CREATE TABLE IF NOT EXISTS paper_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL REFERENCES paper_chunks(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Paper images table
CREATE TABLE IF NOT EXISTS paper_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    image_index INTEGER NOT NULL,
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    image_path TEXT,
    image_data BLOB,
    mime_type TEXT,
    file_size INTEGER,
    caption TEXT,
    extracted_text TEXT,
    is_plot BOOLEAN DEFAULT 0,
    plot_type TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, page_number, image_index)
);

-- Paper tables table
CREATE TABLE IF NOT EXISTS paper_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    table_index INTEGER NOT NULL,
    headers TEXT NOT NULL,
    rows TEXT NOT NULL,
    caption TEXT,
    extracted_data TEXT,
    UNIQUE(paper_id, page_number, table_index)
);

-- Paper citations
CREATE TABLE IF NOT EXISTS paper_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    cited_paper_id TEXT REFERENCES research_papers(id) ON DELETE SET NULL,
    citation_text TEXT,
    citation_context TEXT,
    citation_type TEXT DEFAULT 'reference',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Paper categories
CREATE TABLE IF NOT EXISTS paper_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'manual',
    UNIQUE(paper_id, category)
);

-- Paper files (PDF storage)
CREATE TABLE IF NOT EXISTS paper_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    file_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_data BLOB NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, file_name)
);

-- FTS5 for research papers
CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(
    title, abstract, authors, keywords,
    paper_id UNINDEXED,
    content='',
    tokenize='porter'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_papers_arxiv ON research_papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON research_papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_date ON research_papers(publication_date);
CREATE INDEX IF NOT EXISTS idx_sections_paper ON paper_sections(paper_id);
CREATE INDEX IF NOT EXISTS idx_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk ON paper_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_images_paper ON paper_images(paper_id);
CREATE INDEX IF NOT EXISTS idx_tables_paper ON paper_tables(paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON paper_citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_categories_paper ON paper_categories(paper_id);
CREATE INDEX IF NOT EXISTS idx_files_paper ON paper_files(paper_id);
"""


def init_db(db_path: Path, schema: str, name: str) -> int:
    """Initialize a database with the given schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(schema)
        conn.commit()
        
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"      ✓ Success - {table_count} tables created")
        return 0
    except Exception as e:
        print(f"      ✗ Error: {e}")
        return 1


def detect_gpu():
    """Detect available GPU for ML acceleration."""
    try:
        import torch
        if torch.cuda.is_available():
            return f"CUDA ({torch.cuda.get_device_name(0)})"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "MPS (Apple Silicon)"
    except ImportError:
        pass
    return "CPU (PyTorch not installed)"


def main():
    """Initialize all AIKH databases."""
    print("=" * 60)
    print("AI Knowledge Hub (AIKH) Database Initialization")
    print("=" * 60)
    
    # Ensure AIKH home exists
    AIKH_HOME.mkdir(parents=True, exist_ok=True)
    print(f"\nAIKH Home: {AIKH_HOME}")
    
    errors = 0
    
    # Initialize Artifacts Database
    print(f"\n[1/3] Initializing Artifacts Database...")
    print(f"      Path: {ARTIFACTS_DB_PATH}")
    errors += init_db(ARTIFACTS_DB_PATH, ARTIFACTS_SCHEMA, "Artifacts")
    
    # Initialize Chatlogs Database
    print(f"\n[2/3] Initializing Chatlogs Database...")
    print(f"      Path: {CHATLOGS_DB_PATH}")
    errors += init_db(CHATLOGS_DB_PATH, CHATLOGS_SCHEMA, "Chatlogs")
    
    # Initialize Research Database
    print(f"\n[3/3] Initializing Research Database...")
    print(f"      Path: {RESEARCH_DB_PATH}")
    errors += init_db(RESEARCH_DB_PATH, RESEARCH_SCHEMA, "Research")
    
    # Summary
    print("\n" + "=" * 60)
    if errors == 0:
        print("All AIKH databases initialized successfully!")
    else:
        print(f"Completed with {errors} error(s)")
    print("=" * 60)
    
    # GPU Status
    print(f"\nGPU Acceleration: {detect_gpu()}")
    print(f"Platform: {sys.platform}")
    
    # List databases
    print(f"\nDatabase Files:")
    for db in [ARTIFACTS_DB_PATH, CHATLOGS_DB_PATH, RESEARCH_DB_PATH]:
        if db.exists():
            size_kb = db.stat().st_size / 1024
            print(f"  ✓ {db.name}: {size_kb:.1f} KB")
        else:
            print(f"  ✗ {db.name}: NOT FOUND")
    
    return errors


if __name__ == "__main__":
    sys.exit(main())
