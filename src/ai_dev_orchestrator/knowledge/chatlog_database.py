"""AIKH Chat Logs Database.

AI Knowledge Hub (AIKH) - Chat Logs Store
Cross-project chat history and conversation logs.

This database stores:
- Chat log files and metadata
- Individual conversation turns
- File references and commands extracted from chats
- Embeddings for semantic search across chat history
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .aikh_config import CHATLOGS_DB_PATH, get_aikh_home

# Legacy paths for backward compatibility
LEGACY_LOCAL_PATH = Path("/home/mycahya/coding/ChatLogs/chathistory.db")
DOCKER_DB_PATH = Path("/chatlogs/chathistory.db")


def get_db_path() -> Path:
    """Get the chat log database path.
    
    Priority:
    1. CHATLOG_DB_PATH environment variable
    2. Docker path (/chatlogs) if mounted
    3. AIKH centralized path (~/.aikh/chatlogs.db)
    """
    env_path = os.environ.get("CHATLOG_DB_PATH")
    if env_path:
        return Path(env_path)
    # Detect if running in Docker (check for /chatlogs mount)
    if DOCKER_DB_PATH.parent.exists():
        return DOCKER_DB_PATH
    # Use AIKH centralized path
    return CHATLOGS_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a connection to the AIKH chat logs database."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database() -> None:
    """Initialize the chat logs database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Core chat log table
    cursor.execute("""
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
        )
    """)

    # Individual conversation turns
    cursor.execute("""
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
        )
    """)

    # Extracted file references
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_file_refs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
            turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            project_name TEXT
        )
    """)

    # Extracted commands
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
            turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
            command TEXT NOT NULL,
            was_accepted INTEGER DEFAULT 0
        )
    """)

    # GPU embeddings for semantic search
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
            turn_id INTEGER REFERENCES chat_turns(id),
            embedding BLOB NOT NULL,
            embedding_model TEXT DEFAULT 'all-mpnet-base-v2',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # FTS5 full-text search on chat content (standalone table, not contentless)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chat_fts USING fts5(
            title,
            content,
            tokenize='porter'
        )
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_filename ON chat_logs(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_modified ON chat_logs(modified_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_turns_role ON chat_turns(role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_turns_chat_log ON chat_turns(chat_log_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_file_refs_path ON chat_file_refs(file_path)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_file_refs_project ON chat_file_refs(project_name)")

    conn.commit()
    conn.close()


def insert_chat_log(
    file_path: str,
    filename: str,
    title: str | None,
    file_size: int,
    modified_date: str | None,
    turn_count: int,
    word_count: int,
    projects_referenced: str | None = None,
) -> int:
    """Insert or update a chat log entry. Returns the chat_log_id."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT id FROM chat_logs WHERE file_path = ?", (file_path,))
    existing = cursor.fetchone()

    if existing:
        # Update existing
        cursor.execute("""
            UPDATE chat_logs SET
                filename = ?,
                title = ?,
                file_size = ?,
                modified_date = ?,
                turn_count = ?,
                word_count = ?,
                projects_referenced = ?,
                ingested_at = ?
            WHERE id = ?
        """, (filename, title, file_size, modified_date, turn_count, word_count,
              projects_referenced, datetime.now().isoformat(), existing["id"]))
        chat_log_id = existing["id"]

        # Clear old turns for re-ingestion
        cursor.execute("DELETE FROM chat_turns WHERE chat_log_id = ?", (chat_log_id,))
        cursor.execute("DELETE FROM chat_file_refs WHERE chat_log_id = ?", (chat_log_id,))
        cursor.execute("DELETE FROM chat_commands WHERE chat_log_id = ?", (chat_log_id,))
    else:
        # Insert new
        cursor.execute("""
            INSERT INTO chat_logs (file_path, filename, title, file_size, modified_date,
                                   turn_count, word_count, projects_referenced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_path, filename, title, file_size, modified_date, turn_count,
              word_count, projects_referenced))
        chat_log_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return chat_log_id


def insert_chat_turn(
    chat_log_id: int,
    turn_index: int,
    role: str,
    content: str,
    word_count: int,
    has_code_blocks: bool = False,
    has_file_refs: bool = False,
    has_commands: bool = False,
) -> int:
    """Insert a chat turn. Returns the turn_id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_turns (chat_log_id, turn_index, role, content, word_count,
                                has_code_blocks, has_file_refs, has_commands)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_log_id, turn_index, role, content, word_count,
          int(has_code_blocks), int(has_file_refs), int(has_commands)))

    turn_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return turn_id


def insert_file_ref(chat_log_id: int, turn_id: int | None, file_path: str, project_name: str | None) -> None:
    """Insert a file reference."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_file_refs (chat_log_id, turn_id, file_path, project_name)
        VALUES (?, ?, ?, ?)
    """, (chat_log_id, turn_id, file_path, project_name))
    conn.commit()
    conn.close()


def insert_command(chat_log_id: int, turn_id: int | None, command: str, was_accepted: bool) -> None:
    """Insert a command reference."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_commands (chat_log_id, turn_id, command, was_accepted)
        VALUES (?, ?, ?, ?)
    """, (chat_log_id, turn_id, command, int(was_accepted)))
    conn.commit()
    conn.close()


def update_fts_index() -> None:
    """Rebuild the FTS index from chat_logs table."""
    conn = get_connection()
    cursor = conn.cursor()

    # Drop and recreate to ensure clean state
    cursor.execute("DROP TABLE IF EXISTS chat_fts")
    cursor.execute("""
        CREATE VIRTUAL TABLE chat_fts USING fts5(
            chat_log_id,
            title,
            content,
            tokenize='porter'
        )
    """)

    # Get all turns content grouped by chat_log
    cursor.execute("""
        SELECT cl.id, cl.title, GROUP_CONCAT(ct.content, ' ') as all_content
        FROM chat_logs cl
        LEFT JOIN chat_turns ct ON ct.chat_log_id = cl.id
        GROUP BY cl.id
    """)

    for row in cursor.fetchall():
        cursor.execute(
            "INSERT INTO chat_fts(chat_log_id, title, content) VALUES (?, ?, ?)",
            (str(row["id"]), row["title"] or "", row["all_content"] or "")
        )

    conn.commit()
    conn.close()


def search_chatlogs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Full-text search across chat logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cl.*, bm25(chat_fts) as rank
        FROM chat_fts
        JOIN chat_logs cl ON cl.id = CAST(chat_fts.chat_log_id AS INTEGER)
        WHERE chat_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_all_chatlogs(limit: int = 100) -> list[dict[str, Any]]:
    """Get all chat logs ordered by modified date."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM chat_logs
        ORDER BY modified_date DESC
        LIMIT ?
    """, (limit,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_chatlog_with_turns(chat_log_id: int) -> dict[str, Any] | None:
    """Get a chat log with all its turns."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM chat_logs WHERE id = ?", (chat_log_id,))
    chat_log = cursor.fetchone()
    if not chat_log:
        conn.close()
        return None

    result = dict(chat_log)

    cursor.execute("""
        SELECT * FROM chat_turns
        WHERE chat_log_id = ?
        ORDER BY turn_index
    """, (chat_log_id,))
    result["turns"] = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM chat_file_refs WHERE chat_log_id = ?", (chat_log_id,))
    result["file_refs"] = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM chat_commands WHERE chat_log_id = ?", (chat_log_id,))
    result["commands"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return result


def get_stats() -> dict[str, Any]:
    """Get database statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) as count FROM chat_logs")
    stats["total_chatlogs"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_turns")
    stats["total_turns"] = cursor.fetchone()["count"]

    cursor.execute("SELECT SUM(word_count) as total FROM chat_logs")
    row = cursor.fetchone()
    stats["total_words"] = row["total"] or 0

    cursor.execute("SELECT COUNT(*) as count FROM chat_file_refs")
    stats["total_file_refs"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_commands")
    stats["total_commands"] = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM chat_embeddings")
    stats["embedded_count"] = cursor.fetchone()["count"]

    conn.close()
    return stats
