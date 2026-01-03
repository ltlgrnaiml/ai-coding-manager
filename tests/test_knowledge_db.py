"""Tests for Knowledge database operations."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from ai_dev_orchestrator.knowledge.database import (
    init_database,
    get_connection,
    SCHEMA,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_knowledge.db"
        yield db_path


class TestDatabaseInitialization:
    """Tests for database initialization."""

    def test_init_creates_database(self, temp_db):
        """Test that init_database creates a new database."""
        conn = init_database(temp_db)
        assert temp_db.exists()
        conn.close()

    def test_init_creates_tables(self, temp_db):
        """Test that all required tables are created."""
        conn = init_database(temp_db)
        
        # Check for expected tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            "chunks",
            "documents",
            "embeddings",
            "llm_calls",
            "relationships",
        ]
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
        
        conn.close()

    def test_init_creates_fts_table(self, temp_db):
        """Test that FTS5 virtual table is created."""
        conn = init_database(temp_db)
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='content_fts'"
        )
        result = cursor.fetchone()
        assert result is not None, "FTS5 table not created"
        
        conn.close()

    def test_init_idempotent(self, temp_db):
        """Test that init_database can be called multiple times safely."""
        conn1 = init_database(temp_db)
        conn1.close()
        
        # Should not raise
        conn2 = init_database(temp_db)
        conn2.close()


class TestDatabaseOperations:
    """Tests for database CRUD operations."""

    def test_insert_document(self, temp_db):
        """Test inserting a document."""
        conn = init_database(temp_db)
        
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("ADR-0001", "adr", "Test ADR", "Content here", ".adrs/ADR-0001.json", "abc123"))
        conn.commit()
        
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", ("ADR-0001",))
        row = cursor.fetchone()
        
        assert row is not None
        assert row["id"] == "ADR-0001"
        assert row["type"] == "adr"
        assert row["title"] == "Test ADR"
        
        conn.close()

    def test_fts_search(self, temp_db):
        """Test full-text search on documents."""
        conn = init_database(temp_db)
        
        # Insert test documents
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("DISC-001", "discussion", "API Design Discussion", 
              "We need to decide between REST and GraphQL", 
              ".discussions/DISC-001.md", "hash1"))
        
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("ADR-0002", "adr", "Database Architecture", 
              "SQLite with FTS5 for knowledge storage", 
              ".adrs/ADR-0002.json", "hash2"))
        conn.commit()
        
        # Search for "REST" - FTS5 returns rowid, join with documents
        cursor = conn.execute("""
            SELECT d.id, d.title FROM content_fts f
            JOIN documents d ON f.rowid = d.rowid
            WHERE content_fts MATCH ?
        """, ("REST",))
        results = cursor.fetchall()
        
        assert len(results) == 1
        assert results[0]["id"] == "DISC-001"
        
        # Search for "SQLite"
        cursor = conn.execute("""
            SELECT d.id, d.title FROM content_fts f
            JOIN documents d ON f.rowid = d.rowid
            WHERE content_fts MATCH ?
        """, ("SQLite",))
        results = cursor.fetchall()
        
        assert len(results) == 1
        assert results[0]["id"] == "ADR-0002"
        
        conn.close()

    def test_insert_chunks(self, temp_db):
        """Test inserting document chunks."""
        conn = init_database(temp_db)
        
        # Insert parent document
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("DOC-001", "spec", "Test Spec", "Full content", "specs/test.md", "hash"))
        
        # Insert chunks
        conn.execute("""
            INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char, token_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("DOC-001", 0, "First chunk", 0, 100, 25))
        
        conn.execute("""
            INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char, token_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("DOC-001", 1, "Second chunk", 100, 200, 30))
        conn.commit()
        
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM chunks WHERE doc_id = ?", ("DOC-001",))
        count = cursor.fetchone()["cnt"]
        assert count == 2
        
        conn.close()

    def test_relationships(self, temp_db):
        """Test document relationships."""
        conn = init_database(temp_db)
        
        # Insert documents
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("ADR-0001", "adr", "Main ADR", "Content", "path1", "hash1"))
        
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("SPEC-001", "spec", "Impl Spec", "Content", "path2", "hash2"))
        
        # Create relationship
        conn.execute("""
            INSERT INTO relationships (source_id, target_id, relationship_type)
            VALUES (?, ?, ?)
        """, ("SPEC-001", "ADR-0001", "implements"))
        conn.commit()
        
        cursor = conn.execute("""
            SELECT * FROM relationships WHERE source_id = ?
        """, ("SPEC-001",))
        rel = cursor.fetchone()
        
        assert rel["target_id"] == "ADR-0001"
        assert rel["relationship_type"] == "implements"
        
        conn.close()

    def test_cascade_delete(self, temp_db):
        """Test that deleting a document cascades to chunks."""
        conn = init_database(temp_db)
        
        # Insert document with chunks
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("DOC-002", "spec", "To Delete", "Content", "path", "hash"))
        
        conn.execute("""
            INSERT INTO chunks (doc_id, chunk_index, content)
            VALUES (?, ?, ?)
        """, ("DOC-002", 0, "Chunk content"))
        conn.commit()
        
        # Delete document
        conn.execute("DELETE FROM documents WHERE id = ?", ("DOC-002",))
        conn.commit()
        
        # Verify chunks deleted
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM chunks WHERE doc_id = ?", ("DOC-002",))
        count = cursor.fetchone()["cnt"]
        assert count == 0
        
        conn.close()
