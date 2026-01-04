#!/usr/bin/env python3
"""AIKH Database Refresh - Comprehensive Database Population & Embedding Generation.

Refreshes all AIKH databases with:
1. Workspace artifacts ingestion (ADRs, specs, discussions, sessions, etc.)
2. Archived artifacts table creation and population
3. Chat log embedding generation
4. Research paper embedding generation
5. Full-text search index rebuild

Optimized for Apple Silicon M4 Max using MPS acceleration.

Usage:
    python scripts/refresh_aikh_databases.py --all
    python scripts/refresh_aikh_databases.py --artifacts
    python scripts/refresh_aikh_databases.py --chatlogs
    python scripts/refresh_aikh_databases.py --research
    python scripts/refresh_aikh_databases.py --embeddings-only
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    print("⚠️  sentence-transformers not available. Install: pip install sentence-transformers")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
RESEARCH_DB = AIKH_HOME / "research.db"
CHATLOGS_DB = AIKH_HOME / "chatlogs.db"
ARTIFACTS_DB = AIKH_HOME / "artifacts.db"

WORKSPACE_ROOT = Path(__file__).parent.parent

# Directories to scan for artifacts
ARTIFACT_DIRS = {
    'discussion': WORKSPACE_ROOT / '.discussions',
    'adr': WORKSPACE_ROOT / '.adrs',
    'session': WORKSPACE_ROOT / '.sessions',
    'plan': WORKSPACE_ROOT / '.plans',
    'question': WORKSPACE_ROOT / '.questions',
    'spec': WORKSPACE_ROOT / 'docs' / 'specs',
    'contract': WORKSPACE_ROOT / 'contracts',
}

# Archive directory
ARCHIVE_DIR = WORKSPACE_ROOT / '.archive'

# Embedding model
EMBEDDING_MODEL = 'all-mpnet-base-v2'  # 768 dimensions
BATCH_SIZE = 32


# =============================================================================
# Device Detection
# =============================================================================

def get_device() -> str:
    """Detect the best device for ML inference."""
    if not TORCH_AVAILABLE:
        return "cpu"
    
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("🍎 Apple Silicon MPS detected")
        return "mps"
    
    if torch.cuda.is_available():
        print(f"🎮 CUDA detected: {torch.cuda.get_device_name(0)}")
        return "cuda"
    
    print("💻 Using CPU")
    return "cpu"


# =============================================================================
# Embedding Utilities
# =============================================================================

class EmbeddingGenerator:
    """Generate embeddings with Apple Silicon optimization."""
    
    def __init__(self, device: str = None):
        self.device = device or get_device()
        self._model = None
        self._model_name = EMBEDDING_MODEL
    
    def _load_model(self):
        if self._model is None and EMBEDDER_AVAILABLE:
            print(f"📦 Loading {EMBEDDING_MODEL} on {self.device}...")
            self._model = SentenceTransformer(EMBEDDING_MODEL, device=self.device)
            print("✅ Model loaded")
    
    def embed_batch(self, texts: List[str], show_progress: bool = True) -> List[bytes]:
        """Generate embeddings and return as blobs."""
        self._load_model()
        if self._model is None:
            return [None] * len(texts)
        
        # Process in batches
        all_blobs = []
        total = len(texts)
        
        for i in range(0, total, BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            vectors = self._model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
            
            for vec in vectors:
                blob = struct.pack(f'{len(vec)}f', *vec.tolist())
                all_blobs.append(blob)
            
            if show_progress and total > BATCH_SIZE:
                progress = min(i + BATCH_SIZE, total)
                print(f"  Embedded {progress}/{total} ({progress*100//total}%)")
        
        return all_blobs
    
    def embed_single(self, text: str) -> bytes:
        """Generate embedding for single text."""
        self._load_model()
        if self._model is None:
            return None
        vec = self._model.encode(text, normalize_embeddings=True)
        return struct.pack(f'{len(vec)}f', *vec.tolist())


# =============================================================================
# Database Connections
# =============================================================================

def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get database connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file content."""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


# =============================================================================
# Artifacts Database
# =============================================================================

ARCHIVED_ARTIFACTS_SCHEMA = """
-- Archived artifacts table
CREATE TABLE IF NOT EXISTS archived_artifacts (
    id TEXT PRIMARY KEY,
    original_type TEXT NOT NULL,
    original_path TEXT NOT NULL,
    archive_path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    archived_at TEXT DEFAULT (datetime('now')),
    archive_reason TEXT,
    metadata TEXT  -- JSON blob for extra data
);

-- Archived chunks for RAG
CREATE TABLE IF NOT EXISTS archived_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL REFERENCES archived_artifacts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    UNIQUE(artifact_id, chunk_index)
);

-- Archived embeddings
CREATE TABLE IF NOT EXISTS archived_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL REFERENCES archived_chunks(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_archived_artifacts_type ON archived_artifacts(original_type);
CREATE INDEX IF NOT EXISTS idx_archived_chunks_artifact ON archived_chunks(artifact_id);
CREATE INDEX IF NOT EXISTS idx_archived_embeddings_chunk ON archived_embeddings(chunk_id);
"""


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Tuple[str, int]]:
    """Split text into overlapping chunks. Returns (chunk_text, token_estimate)."""
    if len(text) <= chunk_size:
        return [(text, len(text.split()))]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at paragraph or sentence boundary
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + chunk_size // 2:
                end = para_break + 2
            else:
                # Look for sentence break
                for punct in ['. ', '! ', '? ', '.\n']:
                    sent_break = text.rfind(punct, start, end)
                    if sent_break > start + chunk_size // 2:
                        end = sent_break + len(punct)
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append((chunk, len(chunk.split())))
        
        start = end - overlap
    
    return chunks


def refresh_artifacts_db(embedder: EmbeddingGenerator):
    """Refresh artifacts.db with workspace documents and embeddings."""
    print("\n" + "="*60)
    print("📁 REFRESHING ARTIFACTS DATABASE")
    print("="*60)
    
    conn = get_connection(ARTIFACTS_DB)
    
    # Ensure archived_artifacts table exists
    conn.executescript(ARCHIVED_ARTIFACTS_SCHEMA)
    conn.commit()
    
    # Collect all documents to ingest
    documents = []
    
    for doc_type, dir_path in ARTIFACT_DIRS.items():
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob('*.md'):
            if file_path.name.startswith('.'):
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract title from first heading or filename
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else file_path.stem
                
                documents.append({
                    'type': doc_type,
                    'path': file_path,
                    'title': title,
                    'content': content,
                    'hash': compute_file_hash(file_path)
                })
            except Exception as e:
                print(f"  ⚠️  Error reading {file_path}: {e}")
    
    print(f"📄 Found {len(documents)} documents to ingest")
    
    # Insert documents and chunks
    doc_count = 0
    chunk_count = 0
    
    for doc in documents:
        doc_id = f"{doc['type']}_{doc['hash']}"
        rel_path = str(doc['path'].relative_to(WORKSPACE_ROOT))
        
        # Check if already exists with same hash
        existing = conn.execute(
            "SELECT file_hash FROM documents WHERE file_path = ?",
            (rel_path,)
        ).fetchone()
        
        if existing and existing['file_hash'] == doc['hash']:
            continue  # Skip unchanged
        
        # Delete old version if exists
        if existing:
            conn.execute("DELETE FROM documents WHERE file_path = ?", (rel_path,))
        
        # Insert document
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, doc['type'], doc['title'], doc['content'], rel_path, doc['hash']))
        doc_count += 1
        
        # Create chunks
        chunks = chunk_text(doc['content'])
        for idx, (chunk_text_content, token_count) in enumerate(chunks):
            conn.execute("""
                INSERT INTO chunks (doc_id, chunk_index, content, token_count)
                VALUES (?, ?, ?, ?)
            """, (doc_id, idx, chunk_text_content, token_count))
            chunk_count += 1
    
    conn.commit()
    print(f"✅ Inserted {doc_count} documents, {chunk_count} chunks")
    
    # Generate embeddings for chunks without embeddings
    print("\n🔮 Generating embeddings for chunks...")
    
    rows = conn.execute("""
        SELECT c.id, c.content FROM chunks c
        LEFT JOIN embeddings e ON e.chunk_id = c.id
        WHERE e.id IS NULL
    """).fetchall()
    
    if rows:
        texts = [r['content'] for r in rows]
        chunk_ids = [r['id'] for r in rows]
        
        blobs = embedder.embed_batch(texts)
        
        for chunk_id, blob in zip(chunk_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO embeddings (chunk_id, vector, model, dimensions)
                    VALUES (?, ?, ?, ?)
                """, (chunk_id, blob, EMBEDDING_MODEL, 768))
        
        conn.commit()
        print(f"✅ Generated {len(rows)} embeddings")
    else:
        print("✅ All chunks already have embeddings")
    
    # Process archived artifacts
    print("\n📦 Processing archived artifacts...")
    refresh_archived_artifacts(conn, embedder)
    
    conn.close()


def refresh_archived_artifacts(conn: sqlite3.Connection, embedder: EmbeddingGenerator):
    """Ingest archived artifacts from .archive/ directory."""
    if not ARCHIVE_DIR.exists():
        print("  No .archive/ directory found")
        return
    
    archived_docs = []
    
    for version_dir in ARCHIVE_DIR.iterdir():
        if not version_dir.is_dir():
            continue
        
        version = version_dir.name  # e.g., 'v0'
        
        for file_path in version_dir.rglob('*'):
            if file_path.is_dir():
                continue
            if file_path.suffix not in ['.md', '.txt', '.json', '.yaml', '.yml']:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Determine original type from path
                parts = file_path.relative_to(version_dir).parts
                orig_type = parts[0] if parts else 'unknown'
                
                # Extract title
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else file_path.stem
                
                archived_docs.append({
                    'version': version,
                    'type': orig_type,
                    'path': file_path,
                    'title': title,
                    'content': content,
                    'hash': compute_file_hash(file_path)
                })
            except Exception as e:
                print(f"  ⚠️  Error reading {file_path}: {e}")
    
    print(f"  Found {len(archived_docs)} archived files")
    
    if not archived_docs:
        return
    
    # Insert archived artifacts
    for doc in archived_docs:
        artifact_id = f"archive_{doc['version']}_{doc['hash']}"
        archive_path = str(doc['path'].relative_to(WORKSPACE_ROOT))
        
        # Check if exists
        existing = conn.execute(
            "SELECT id FROM archived_artifacts WHERE archive_path = ?",
            (archive_path,)
        ).fetchone()
        
        if existing:
            continue
        
        # Insert
        conn.execute("""
            INSERT INTO archived_artifacts 
            (id, original_type, original_path, archive_path, title, content, file_hash, archive_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (artifact_id, doc['type'], '', archive_path, doc['title'], 
              doc['content'], doc['hash'], f"Pre-{doc['version']} archive"))
        
        # Create chunks
        chunks = chunk_text(doc['content'])
        for idx, (chunk_content, token_count) in enumerate(chunks):
            conn.execute("""
                INSERT INTO archived_chunks (artifact_id, chunk_index, content, token_count)
                VALUES (?, ?, ?, ?)
            """, (artifact_id, idx, chunk_content, token_count))
    
    conn.commit()
    
    # Generate embeddings for archived chunks
    rows = conn.execute("""
        SELECT c.id, c.content FROM archived_chunks c
        LEFT JOIN archived_embeddings e ON e.chunk_id = c.id
        WHERE e.id IS NULL
    """).fetchall()
    
    if rows:
        texts = [r['content'] for r in rows]
        chunk_ids = [r['id'] for r in rows]
        
        blobs = embedder.embed_batch(texts, show_progress=False)
        
        for chunk_id, blob in zip(chunk_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO archived_embeddings (chunk_id, vector, model)
                    VALUES (?, ?, ?)
                """, (chunk_id, blob, EMBEDDING_MODEL))
        
        conn.commit()
        print(f"  ✅ Generated {len(rows)} archived embeddings")


# =============================================================================
# Chatlogs Database
# =============================================================================

def refresh_chatlogs_db(embedder: EmbeddingGenerator):
    """Generate embeddings for chat logs."""
    print("\n" + "="*60)
    print("💬 REFRESHING CHATLOGS DATABASE")
    print("="*60)
    
    if not CHATLOGS_DB.exists():
        print("❌ chatlogs.db not found")
        return
    
    conn = get_connection(CHATLOGS_DB)
    
    # Check current state
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM chat_logs) as logs,
            (SELECT COUNT(*) FROM chat_turns) as turns,
            (SELECT COUNT(*) FROM chat_embeddings) as embeddings
    """).fetchone()
    
    print(f"📊 Current state: {stats['logs']} logs, {stats['turns']} turns, {stats['embeddings']} embeddings")
    
    # Get turns without embeddings
    # We'll embed each turn individually for granular search
    rows = conn.execute("""
        SELECT t.id, t.content, t.role, l.title
        FROM chat_turns t
        JOIN chat_logs l ON t.chat_log_id = l.id
        LEFT JOIN chat_embeddings e ON e.turn_id = t.id
        WHERE e.id IS NULL
        AND LENGTH(t.content) > 50  -- Skip very short messages
    """).fetchall()
    
    print(f"🔮 Generating embeddings for {len(rows)} turns...")
    
    if rows:
        texts = [f"{r['role']}: {r['content'][:2000]}" for r in rows]  # Truncate long content
        turn_ids = [r['id'] for r in rows]
        chat_log_ids = [conn.execute(
            "SELECT chat_log_id FROM chat_turns WHERE id = ?", (tid,)
        ).fetchone()['chat_log_id'] for tid in turn_ids]
        
        blobs = embedder.embed_batch(texts)
        
        embedded_count = 0
        for turn_id, chat_log_id, blob in zip(turn_ids, chat_log_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO chat_embeddings (chat_log_id, turn_id, embedding, embedding_model)
                    VALUES (?, ?, ?, ?)
                """, (chat_log_id, turn_id, blob, EMBEDDING_MODEL))
                embedded_count += 1
        
        conn.commit()
        print(f"✅ Generated {embedded_count} embeddings")
    else:
        print("✅ All turns already have embeddings")
    
    # Also create log-level embeddings (summary of each chat)
    print("\n📝 Generating log-level summary embeddings...")
    
    logs_without_summary = conn.execute("""
        SELECT l.id, l.title, l.filename,
               GROUP_CONCAT(t.content, ' ') as all_content
        FROM chat_logs l
        JOIN chat_turns t ON t.chat_log_id = l.id
        LEFT JOIN chat_embeddings e ON e.chat_log_id = l.id AND e.turn_id IS NULL
        WHERE e.id IS NULL
        GROUP BY l.id
    """).fetchall()
    
    if logs_without_summary:
        texts = []
        log_ids = []
        
        for row in logs_without_summary:
            # Create summary text
            summary = f"Chat: {row['title'] or row['filename']}\n{row['all_content'][:3000]}"
            texts.append(summary)
            log_ids.append(row['id'])
        
        blobs = embedder.embed_batch(texts, show_progress=False)
        
        for log_id, blob in zip(log_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO chat_embeddings (chat_log_id, turn_id, embedding, embedding_model)
                    VALUES (?, NULL, ?, ?)
                """, (log_id, blob, EMBEDDING_MODEL))
        
        conn.commit()
        print(f"✅ Generated {len(logs_without_summary)} log-level embeddings")
    else:
        print("✅ All logs already have summary embeddings")
    
    conn.close()


# =============================================================================
# Research Database
# =============================================================================

def refresh_research_db(embedder: EmbeddingGenerator):
    """Generate embeddings for research papers."""
    print("\n" + "="*60)
    print("📚 REFRESHING RESEARCH DATABASE")
    print("="*60)
    
    if not RESEARCH_DB.exists():
        print("❌ research.db not found")
        return
    
    conn = get_connection(RESEARCH_DB)
    
    # Check current state
    stats = conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM research_papers) as papers,
            (SELECT COUNT(*) FROM paper_chunks) as chunks,
            (SELECT COUNT(*) FROM paper_embeddings) as embeddings
    """).fetchone()
    
    print(f"📊 Current state: {stats['papers']} papers, {stats['chunks']} chunks, {stats['embeddings']} embeddings")
    
    # Get chunks without embeddings
    rows = conn.execute("""
        SELECT c.id, c.content, p.title
        FROM paper_chunks c
        JOIN research_papers p ON c.paper_id = p.id
        LEFT JOIN paper_embeddings e ON e.chunk_id = c.id
        WHERE e.id IS NULL
        AND LENGTH(c.content) > 50
    """).fetchall()
    
    print(f"🔮 Generating embeddings for {len(rows)} chunks...")
    
    if rows:
        texts = [r['content'][:2000] for r in rows]  # Truncate if needed
        chunk_ids = [r['id'] for r in rows]
        
        blobs = embedder.embed_batch(texts)
        
        embedded_count = 0
        for chunk_id, blob in zip(chunk_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO paper_embeddings (chunk_id, vector, model, dimensions)
                    VALUES (?, ?, ?, ?)
                """, (chunk_id, blob, EMBEDDING_MODEL, 768))
                embedded_count += 1
        
        conn.commit()
        print(f"✅ Generated {embedded_count} embeddings")
    else:
        print("✅ All chunks already have embeddings")
    
    # Also create paper-level embeddings (title + abstract)
    print("\n📝 Generating paper-level embeddings...")
    
    # Check if paper-level embedding table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_summary_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
            vector BLOB NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(paper_id, model)
        )
    """)
    conn.commit()
    
    papers_without_summary = conn.execute("""
        SELECT p.id, p.title, p.abstract, p.keywords
        FROM research_papers p
        LEFT JOIN paper_summary_embeddings e ON e.paper_id = p.id
        WHERE e.id IS NULL
    """).fetchall()
    
    if papers_without_summary:
        texts = []
        paper_ids = []
        
        for row in papers_without_summary:
            summary = f"{row['title']} {row['abstract'] or ''} {row['keywords'] or ''}"
            texts.append(summary[:3000])
            paper_ids.append(row['id'])
        
        blobs = embedder.embed_batch(texts, show_progress=False)
        
        for paper_id, blob in zip(paper_ids, blobs):
            if blob:
                conn.execute("""
                    INSERT INTO paper_summary_embeddings (paper_id, vector, model)
                    VALUES (?, ?, ?)
                """, (paper_id, blob, EMBEDDING_MODEL))
        
        conn.commit()
        print(f"✅ Generated {len(papers_without_summary)} paper-level embeddings")
    else:
        print("✅ All papers already have summary embeddings")
    
    conn.close()


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Refresh AIKH databases with content and embeddings"
    )
    parser.add_argument('--all', action='store_true', help="Refresh all databases")
    parser.add_argument('--artifacts', action='store_true', help="Refresh artifacts.db")
    parser.add_argument('--chatlogs', action='store_true', help="Refresh chatlogs.db")
    parser.add_argument('--research', action='store_true', help="Refresh research.db")
    parser.add_argument('--embeddings-only', action='store_true', 
                        help="Only generate missing embeddings, don't re-ingest")
    
    args = parser.parse_args()
    
    if not any([args.all, args.artifacts, args.chatlogs, args.research]):
        parser.error("Specify --all or specific database(s)")
    
    print("🔧 AIKH DATABASE REFRESH")
    print(f"📍 AIKH Home: {AIKH_HOME}")
    print(f"📁 Workspace: {WORKSPACE_ROOT}")
    
    # Initialize embedder
    embedder = EmbeddingGenerator()
    
    start_time = time.time()
    
    if args.all or args.artifacts:
        refresh_artifacts_db(embedder)
    
    if args.all or args.chatlogs:
        refresh_chatlogs_db(embedder)
    
    if args.all or args.research:
        refresh_research_db(embedder)
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("📊 REFRESH COMPLETE")
    print("="*60)
    print(f"⏱️  Elapsed time: {elapsed:.1f}s")
    
    # Print final stats
    print("\n📈 Final Database Statistics:")
    
    for db_name, db_path in [
        ("Artifacts", ARTIFACTS_DB),
        ("Chatlogs", CHATLOGS_DB),
        ("Research", RESEARCH_DB)
    ]:
        if db_path.exists():
            conn = get_connection(db_path)
            try:
                if db_name == "Artifacts":
                    stats = conn.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM documents) as docs,
                            (SELECT COUNT(*) FROM chunks) as chunks,
                            (SELECT COUNT(*) FROM embeddings) as embeddings,
                            (SELECT COUNT(*) FROM archived_artifacts) as archived
                    """).fetchone()
                    print(f"  {db_name}: {stats['docs']} docs, {stats['chunks']} chunks, "
                          f"{stats['embeddings']} embeddings, {stats['archived']} archived")
                elif db_name == "Chatlogs":
                    stats = conn.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM chat_logs) as logs,
                            (SELECT COUNT(*) FROM chat_turns) as turns,
                            (SELECT COUNT(*) FROM chat_embeddings) as embeddings
                    """).fetchone()
                    print(f"  {db_name}: {stats['logs']} logs, {stats['turns']} turns, "
                          f"{stats['embeddings']} embeddings")
                elif db_name == "Research":
                    stats = conn.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM research_papers) as papers,
                            (SELECT COUNT(*) FROM paper_chunks) as chunks,
                            (SELECT COUNT(*) FROM paper_embeddings) as embeddings
                    """).fetchone()
                    print(f"  {db_name}: {stats['papers']} papers, {stats['chunks']} chunks, "
                          f"{stats['embeddings']} embeddings")
            except Exception as e:
                print(f"  {db_name}: Error reading stats: {e}")
            conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
