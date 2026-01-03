"""Chat Log Service API.

Per DISC-0024: API endpoints for cross-project chat logs.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# ChatLogs database path - use AIKH centralized location
def get_db_path() -> Path:
    """Get the chat log database path from AIKH."""
    # Environment override
    if env_path := os.environ.get("CHATLOG_DB_PATH"):
        return Path(env_path)
    # Docker mount
    if Path("/aikh/chatlogs.db").exists():
        return Path("/aikh/chatlogs.db")
    # AIKH_HOME environment
    if aikh_home := os.environ.get("AIKH_HOME"):
        return Path(aikh_home) / "chatlogs.db"
    # Default to user home
    return Path.home() / ".aikh" / "chatlogs.db"


def get_connection() -> sqlite3.Connection:
    """Get a connection to the chat logs database."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_all_chatlogs(limit: int = 100) -> list[dict[str, Any]]:
    """Get all chat logs ordered by modified date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_logs ORDER BY modified_date DESC LIMIT ?", (limit,))
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
    cursor.execute("SELECT * FROM chat_turns WHERE chat_log_id = ? ORDER BY turn_index", (chat_log_id,))
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
    stats["embedded_count"] = 0  # Not implemented yet
    conn.close()
    return stats


def search_chatlogs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Full-text search across chat logs."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT cl.*, bm25(chat_fts) as rank
            FROM chat_fts
            JOIN chat_logs cl ON cl.id = CAST(chat_fts.chat_log_id AS INTEGER)
            WHERE chat_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # FTS table may not exist, fall back to LIKE search
        cursor.execute("""
            SELECT * FROM chat_logs WHERE title LIKE ? LIMIT ?
        """, (f"%{query}%", limit))
        results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

router = APIRouter(prefix="/api/chatlogs", tags=["chatlogs"])


class ChatLogSummary(BaseModel):
    """Summary of a chat log for list view."""

    id: int
    filename: str
    title: str | None
    turn_count: int
    word_count: int
    modified_date: str | None
    projects_referenced: str | None


class ChatLogDetail(BaseModel):
    """Full chat log with turns."""

    id: int
    filename: str
    title: str | None
    file_path: str
    file_size: int
    turn_count: int
    word_count: int
    modified_date: str | None
    projects_referenced: str | None
    turns: list[dict[str, Any]]
    file_refs: list[dict[str, Any]]
    commands: list[dict[str, Any]]


class ChatLogListResponse(BaseModel):
    """Response for chat log list."""

    items: list[ChatLogSummary]
    total: int


class ChatLogStats(BaseModel):
    """Database statistics."""

    total_chatlogs: int
    total_turns: int
    total_words: int
    total_file_refs: int
    total_commands: int
    embedded_count: int


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    limit: int = 20


@router.get("", response_model=ChatLogListResponse)
async def list_chatlogs(
    limit: int = Query(100, description="Maximum number of results"),
    search: str | None = Query(None, description="Search query"),
) -> ChatLogListResponse:
    """List all chat logs or search."""
    if search:
        results = search_chatlogs(search, limit)
    else:
        results = get_all_chatlogs(limit)

    items = [
        ChatLogSummary(
            id=r["id"],
            filename=r["filename"],
            title=r["title"],
            turn_count=r["turn_count"],
            word_count=r["word_count"],
            modified_date=r["modified_date"],
            projects_referenced=r.get("projects_referenced"),
        )
        for r in results
    ]

    return ChatLogListResponse(items=items, total=len(items))


@router.get("/stats", response_model=ChatLogStats)
async def get_chatlog_stats() -> ChatLogStats:
    """Get chat log database statistics."""
    stats = get_stats()
    return ChatLogStats(**stats)


@router.get("/{chatlog_id}", response_model=ChatLogDetail)
async def get_chatlog(chatlog_id: int) -> ChatLogDetail:
    """Get a single chat log with all turns."""
    result = get_chatlog_with_turns(chatlog_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Chat log {chatlog_id} not found")

    return ChatLogDetail(
        id=result["id"],
        filename=result["filename"],
        title=result["title"],
        file_path=result["file_path"],
        file_size=result["file_size"],
        turn_count=result["turn_count"],
        word_count=result["word_count"],
        modified_date=result["modified_date"],
        projects_referenced=result.get("projects_referenced"),
        turns=result["turns"],
        file_refs=result["file_refs"],
        commands=result["commands"],
    )


@router.post("/search")
async def search_logs(request: SearchRequest) -> ChatLogListResponse:
    """Full-text search across chat logs."""
    results = search_chatlogs(request.query, request.limit)

    items = [
        ChatLogSummary(
            id=r["id"],
            filename=r["filename"],
            title=r["title"],
            turn_count=r["turn_count"],
            word_count=r["word_count"],
            modified_date=r["modified_date"],
            projects_referenced=r.get("projects_referenced"),
        )
        for r in results
    ]

    return ChatLogListResponse(items=items, total=len(items))


@router.post("/sync")
async def sync_chatlogs() -> dict[str, Any]:
    """Trigger manual sync/re-ingestion of chat logs."""
    # Return current stats - actual ingestion done via scripts/ingest_chat_logs.py
    stats = get_stats()
    return {
        "status": "use scripts/ingest_chat_logs.py for ingestion",
        "total_chatlogs": stats["total_chatlogs"],
        "total_turns": stats["total_turns"],
    }
