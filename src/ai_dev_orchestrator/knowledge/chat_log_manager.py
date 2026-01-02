"""Chat Log Manager - Intelligent deduplication and analysis for chat logs.

Handles:
- Message-level deduplication across incremental file saves
- Session merging when the same chat is saved multiple times
- Field extraction (### User Input, ### Assistant, etc.)
- Similarity queries for comparing user inputs
- Timeline views across sessions
"""

import hashlib
import json
import logging
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ai_dev_orchestrator.knowledge.database import get_connection, init_database

logger = logging.getLogger(__name__)


@dataclass
class ParsedMessage:
    """A parsed message from a chat log."""
    role: str
    content: str
    content_hash: str
    sequence_num: int
    timestamp: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class ParsedChatFile:
    """Result of parsing a chat log file."""
    file_path: Path
    file_hash: str
    title: str
    messages: List[ParsedMessage]
    detected_format: str
    first_message_content: Optional[str] = None  # For session matching


@dataclass
class ImportResult:
    """Result of importing a chat file."""
    file_path: Path
    success: bool
    session_id: Optional[str] = None
    total_messages: int = 0
    new_messages: int = 0
    duplicate_messages: int = 0
    error: Optional[str] = None
    merged_with_existing: bool = False


@dataclass
class ChatSession:
    """A chat session from the database."""
    id: str
    title: str
    first_message_at: Optional[str]
    last_message_at: Optional[str]
    message_count: int
    user_message_count: int
    assistant_message_count: int
    topics: List[str]
    summary: Optional[str]
    source_files: List[str] = field(default_factory=list)


@dataclass
class MessageMatch:
    """A message that matched a similarity query."""
    message_id: int
    session_id: str
    session_title: str
    role: str
    content: str
    similarity_score: float
    timestamp: Optional[str] = None


class ChatLogManager:
    """Manages chat log ingestion, deduplication, and querying."""
    
    # Patterns for detecting message boundaries in various formats
    MESSAGE_PATTERNS = {
        'markdown_headers': [
            (r'^###\s*User\s*(?:Input|Message|:)?\s*$', 'user'),
            (r'^###\s*(?:Assistant|AI|Claude|Cascade)\s*(?:Response|Message|:)?\s*$', 'assistant'),
            (r'^##\s*User\s*(?:Input|:)?\s*$', 'user'),
            (r'^##\s*(?:Assistant|AI)\s*(?:Response|:)?\s*$', 'assistant'),
        ],
        'inline_markers': [
            (r'^(?:User|Human|You):\s*', 'user'),
            (r'^(?:Assistant|AI|Claude|Cascade):\s*', 'assistant'),
        ],
        'json_keys': ['role', 'content', 'speaker', 'text'],
    }
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize chat log manager."""
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Ensure database schema is initialized."""
        init_database(self.db_path)
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        return get_connection(self.db_path)
    
    @staticmethod
    def _compute_content_hash(role: str, content: str) -> str:
        """Compute hash of message for deduplication.
        
        Normalizes whitespace and case for role to handle minor variations.
        """
        normalized_role = role.lower().strip()
        # Normalize whitespace in content but preserve structure
        normalized_content = ' '.join(content.split())
        hash_input = f"{normalized_role}:{normalized_content}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:32]
    
    @staticmethod
    def _compute_file_hash(content: str) -> str:
        """Compute hash of file content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]
    
    def _detect_format(self, content: str) -> str:
        """Detect the format of a chat log file."""
        content_stripped = content.strip()
        
        # Check for JSON
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            try:
                json.loads(content_stripped)
                return 'json'
            except json.JSONDecodeError:
                pass
        
        # Check for markdown headers (### User Input style)
        for pattern, _ in self.MESSAGE_PATTERNS['markdown_headers']:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                return 'markdown_headers'
        
        # Check for inline markers (User: ... style)
        for pattern, _ in self.MESSAGE_PATTERNS['inline_markers']:
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                return 'inline_markers'
        
        return 'unknown'
    
    def _parse_markdown_headers(self, content: str, file_path: Path) -> List[ParsedMessage]:
        """Parse chat log with markdown header format (### User Input)."""
        messages = []
        current_role = None
        current_content = []
        sequence = 0
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for role headers
            matched_role = None
            for pattern, role in self.MESSAGE_PATTERNS['markdown_headers']:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    matched_role = role
                    break
            
            if matched_role:
                # Save previous message
                if current_role and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        messages.append(ParsedMessage(
                            role=current_role,
                            content=content_text,
                            content_hash=self._compute_content_hash(current_role, content_text),
                            sequence_num=sequence,
                            source_file=str(file_path)
                        ))
                        sequence += 1
                
                current_role = matched_role
                current_content = []
            elif current_role is not None:
                current_content.append(line)
        
        # Save final message
        if current_role and current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                messages.append(ParsedMessage(
                    role=current_role,
                    content=content_text,
                    content_hash=self._compute_content_hash(current_role, content_text),
                    sequence_num=sequence,
                    source_file=str(file_path)
                ))
        
        return messages
    
    def _parse_inline_markers(self, content: str, file_path: Path) -> List[ParsedMessage]:
        """Parse chat log with inline markers (User: ... style)."""
        messages = []
        current_role = None
        current_content = []
        sequence = 0
        
        lines = content.split('\n')
        
        for line in lines:
            # Check for role markers
            matched_role = None
            remaining_content = line
            
            for pattern, role in self.MESSAGE_PATTERNS['inline_markers']:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    matched_role = role
                    remaining_content = line[match.end():].strip()
                    break
            
            if matched_role:
                # Save previous message
                if current_role and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        messages.append(ParsedMessage(
                            role=current_role,
                            content=content_text,
                            content_hash=self._compute_content_hash(current_role, content_text),
                            sequence_num=sequence,
                            source_file=str(file_path)
                        ))
                        sequence += 1
                
                current_role = matched_role
                current_content = [remaining_content] if remaining_content else []
            elif current_role is not None:
                # Skip separator lines
                if not re.match(r'^[-=*]{3,}$', line.strip()):
                    current_content.append(line)
        
        # Save final message
        if current_role and current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                messages.append(ParsedMessage(
                    role=current_role,
                    content=content_text,
                    content_hash=self._compute_content_hash(current_role, content_text),
                    sequence_num=sequence,
                    source_file=str(file_path)
                ))
        
        return messages
    
    def _parse_json(self, content: str, file_path: Path) -> List[ParsedMessage]:
        """Parse JSON format chat log."""
        messages = []
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return messages
        
        # Handle array of messages
        if isinstance(data, list):
            msg_list = data
        elif isinstance(data, dict):
            # Look for messages array in common keys
            for key in ['messages', 'conversation', 'chat', 'data']:
                if key in data and isinstance(data[key], list):
                    msg_list = data[key]
                    break
            else:
                msg_list = [data]
        else:
            return messages
        
        for i, msg in enumerate(msg_list):
            if not isinstance(msg, dict):
                continue
            
            # Extract role
            role = msg.get('role') or msg.get('speaker') or msg.get('type', 'unknown')
            role = role.lower()
            if role in ['human', 'you']:
                role = 'user'
            elif role in ['ai', 'claude', 'cascade', 'bot']:
                role = 'assistant'
            
            # Extract content
            content_text = msg.get('content') or msg.get('text') or msg.get('message', '')
            
            if content_text:
                messages.append(ParsedMessage(
                    role=role,
                    content=content_text,
                    content_hash=self._compute_content_hash(role, content_text),
                    sequence_num=i,
                    timestamp=msg.get('timestamp') or msg.get('time'),
                    source_file=str(file_path)
                ))
        
        return messages
    
    def parse_file(self, file_path: Path) -> ParsedChatFile:
        """Parse a chat log file into structured messages."""
        content = file_path.read_text(encoding='utf-8', errors='replace')
        file_hash = self._compute_file_hash(content)
        detected_format = self._detect_format(content)
        
        # Parse based on format
        if detected_format == 'json':
            messages = self._parse_json(content, file_path)
        elif detected_format == 'markdown_headers':
            messages = self._parse_markdown_headers(content, file_path)
        elif detected_format == 'inline_markers':
            messages = self._parse_inline_markers(content, file_path)
        else:
            # Try both parsers and use whichever gets more messages
            md_messages = self._parse_markdown_headers(content, file_path)
            inline_messages = self._parse_inline_markers(content, file_path)
            messages = md_messages if len(md_messages) >= len(inline_messages) else inline_messages
            if messages:
                detected_format = 'markdown_headers' if messages == md_messages else 'inline_markers'
        
        # Extract title from filename or first few messages
        title = self._extract_title(file_path, messages)
        
        first_content = None
        if messages:
            # Use first few user messages for session matching
            user_msgs = [m for m in messages if m.role == 'user'][:3]
            if user_msgs:
                first_content = ' '.join(m.content[:200] for m in user_msgs)
        
        return ParsedChatFile(
            file_path=file_path,
            file_hash=file_hash,
            title=title,
            messages=messages,
            detected_format=detected_format,
            first_message_content=first_content
        )
    
    def _extract_title(self, file_path: Path, messages: List[ParsedMessage]) -> str:
        """Extract a title from the file or messages."""
        # Clean up filename
        title = file_path.stem
        title = re.sub(r'^\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?', '', title)  # Remove date prefix
        title = re.sub(r'[-_]+', ' ', title)
        title = title.strip().title()
        
        if not title and messages:
            # Use first user message as title
            user_msgs = [m for m in messages if m.role == 'user']
            if user_msgs:
                first_msg = user_msgs[0].content[:80]
                title = first_msg.split('\n')[0][:60] + ('...' if len(first_msg) > 60 else '')
        
        return title or 'Untitled Chat'
    
    def _find_matching_session(self, parsed: ParsedChatFile) -> Optional[str]:
        """Find an existing session that matches this file's content.
        
        Matches by checking if significant overlap exists in message hashes.
        """
        if not parsed.messages:
            return None
        
        conn = self._get_conn()
        
        # Get hashes of first few messages
        first_hashes = [m.content_hash for m in parsed.messages[:5]]
        
        # Find sessions with matching messages
        placeholders = ','.join('?' * len(first_hashes))
        result = conn.execute(f"""
            SELECT session_id, COUNT(*) as match_count
            FROM chat_messages
            WHERE content_hash IN ({placeholders})
            GROUP BY session_id
            HAVING match_count >= ?
            ORDER BY match_count DESC
            LIMIT 1
        """, first_hashes + [min(3, len(first_hashes))]).fetchone()
        
        if result:
            return result['session_id']
        
        return None
    
    def import_file(self, file_path: Path) -> ImportResult:
        """Import a chat log file with deduplication.
        
        If the file contains messages from an existing session, merges them.
        Otherwise creates a new session.
        """
        try:
            parsed = self.parse_file(file_path)
            
            if not parsed.messages:
                return ImportResult(
                    file_path=file_path,
                    success=False,
                    error="No messages found in file"
                )
            
            conn = self._get_conn()
            
            # Check if file was already imported
            existing_file = conn.execute(
                "SELECT session_id FROM chat_source_files WHERE file_path = ?",
                (str(file_path),)
            ).fetchone()
            
            if existing_file:
                return ImportResult(
                    file_path=file_path,
                    success=True,
                    session_id=existing_file['session_id'],
                    total_messages=len(parsed.messages),
                    new_messages=0,
                    duplicate_messages=len(parsed.messages),
                    error="File already imported"
                )
            
            # Find matching session or create new one
            session_id = self._find_matching_session(parsed)
            merged = session_id is not None
            
            if not session_id:
                session_id = f"chat_{uuid4().hex[:12]}"
                conn.execute("""
                    INSERT INTO chat_sessions (id, title, message_count)
                    VALUES (?, ?, 0)
                """, (session_id, parsed.title))
            
            # Insert messages with deduplication
            new_count = 0
            dup_count = 0
            max_seq = 0
            
            if merged:
                # Get current max sequence number
                result = conn.execute(
                    "SELECT MAX(sequence_num) as max_seq FROM chat_messages WHERE session_id = ?",
                    (session_id,)
                ).fetchone()
                max_seq = (result['max_seq'] or 0) + 1
            
            for i, msg in enumerate(parsed.messages):
                try:
                    conn.execute("""
                        INSERT INTO chat_messages 
                        (session_id, content_hash, role, content, sequence_num, timestamp, source_file)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session_id,
                        msg.content_hash,
                        msg.role,
                        msg.content,
                        max_seq + i if merged else msg.sequence_num,
                        msg.timestamp,
                        str(file_path)
                    ))
                    new_count += 1
                except sqlite3.IntegrityError:
                    # Duplicate message
                    dup_count += 1
            
            # Record source file
            conn.execute("""
                INSERT OR REPLACE INTO chat_source_files 
                (session_id, file_path, file_hash, message_count, new_messages)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, str(file_path), parsed.file_hash, len(parsed.messages), new_count))
            
            # Update session statistics
            self._update_session_stats(conn, session_id)
            
            conn.commit()
            
            return ImportResult(
                file_path=file_path,
                success=True,
                session_id=session_id,
                total_messages=len(parsed.messages),
                new_messages=new_count,
                duplicate_messages=dup_count,
                merged_with_existing=merged
            )
            
        except Exception as e:
            logger.exception(f"Error importing {file_path}")
            return ImportResult(
                file_path=file_path,
                success=False,
                error=str(e)
            )
    
    def _update_session_stats(self, conn: sqlite3.Connection, session_id: str) -> None:
        """Update session statistics after import."""
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN role = 'user' THEN 1 ELSE 0 END) as user_count,
                SUM(CASE WHEN role = 'assistant' THEN 1 ELSE 0 END) as assistant_count,
                MIN(timestamp) as first_msg,
                MAX(timestamp) as last_msg
            FROM chat_messages
            WHERE session_id = ?
        """, (session_id,)).fetchone()
        
        conn.execute("""
            UPDATE chat_sessions
            SET message_count = ?,
                user_message_count = ?,
                assistant_message_count = ?,
                first_message_at = COALESCE(?, first_message_at),
                last_message_at = COALESCE(?, last_message_at)
            WHERE id = ?
        """, (
            stats['total'],
            stats['user_count'],
            stats['assistant_count'],
            stats['first_msg'],
            stats['last_msg'],
            session_id
        ))
    
    def import_directory(self, dir_path: Path, pattern: str = "*.md", recursive: bool = True) -> List[ImportResult]:
        """Import all matching chat log files from a directory."""
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        results = []
        for file_path in sorted(files):
            if file_path.is_file():
                result = self.import_file(file_path)
                results.append(result)
                
                status = "✅" if result.success else "❌"
                if result.success:
                    logger.info(f"{status} {file_path.name}: {result.new_messages} new, {result.duplicate_messages} dup")
                else:
                    logger.warning(f"{status} {file_path.name}: {result.error}")
        
        return results
    
    def get_sessions(self, limit: int = 100, offset: int = 0) -> List[ChatSession]:
        """Get all chat sessions."""
        conn = self._get_conn()
        
        rows = conn.execute("""
            SELECT s.*, GROUP_CONCAT(f.file_path, '|||') as source_files
            FROM chat_sessions s
            LEFT JOIN chat_source_files f ON s.id = f.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        
        sessions = []
        for row in rows:
            topics = json.loads(row['topics']) if row['topics'] else []
            source_files = row['source_files'].split('|||') if row['source_files'] else []
            
            sessions.append(ChatSession(
                id=row['id'],
                title=row['title'],
                first_message_at=row['first_message_at'],
                last_message_at=row['last_message_at'],
                message_count=row['message_count'],
                user_message_count=row['user_message_count'],
                assistant_message_count=row['assistant_message_count'],
                topics=topics,
                summary=row['summary'],
                source_files=source_files
            ))
        
        return sessions
    
    def get_session_messages(
        self, 
        session_id: str, 
        role: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get messages from a session, optionally filtered by role."""
        conn = self._get_conn()
        
        if role:
            rows = conn.execute("""
                SELECT * FROM chat_messages
                WHERE session_id = ? AND role = ?
                ORDER BY sequence_num
                LIMIT ?
            """, (session_id, role, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY sequence_num
                LIMIT ?
            """, (session_id, limit)).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_all_user_inputs(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all user inputs across all sessions."""
        conn = self._get_conn()
        
        rows = conn.execute("""
            SELECT m.*, s.title as session_title
            FROM chat_messages m
            JOIN chat_sessions s ON m.session_id = s.id
            WHERE m.role = 'user'
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        return [dict(row) for row in rows]
    
    def search_messages(
        self, 
        query: str, 
        role: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search messages by content."""
        conn = self._get_conn()
        
        search_pattern = f"%{query}%"
        
        if role:
            rows = conn.execute("""
                SELECT m.*, s.title as session_title
                FROM chat_messages m
                JOIN chat_sessions s ON m.session_id = s.id
                WHERE m.content LIKE ? AND m.role = ?
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (search_pattern, role, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT m.*, s.title as session_title
                FROM chat_messages m
                JOIN chat_sessions s ON m.session_id = s.id
                WHERE m.content LIKE ?
                ORDER BY m.created_at DESC
                LIMIT ?
            """, (search_pattern, limit)).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_timeline(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages in timeline order."""
        conn = self._get_conn()
        
        query = """
            SELECT m.*, s.title as session_title
            FROM chat_messages m
            JOIN chat_sessions s ON m.session_id = s.id
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND m.created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND m.created_at <= ?"
            params.append(end_date)
        
        if role:
            query += " AND m.role = ?"
            params.append(role)
        
        query += " ORDER BY m.created_at ASC"
        
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics."""
        conn = self._get_conn()
        
        stats = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM chat_sessions) as total_sessions,
                (SELECT COUNT(*) FROM chat_messages) as total_messages,
                (SELECT COUNT(*) FROM chat_messages WHERE role = 'user') as user_messages,
                (SELECT COUNT(*) FROM chat_messages WHERE role = 'assistant') as assistant_messages,
                (SELECT COUNT(*) FROM chat_source_files) as source_files,
                (SELECT SUM(message_count - new_messages) FROM chat_source_files) as deduplicated_messages
        """).fetchone()
        
        return dict(stats)


def create_chat_manager(db_path: Optional[Path] = None) -> ChatLogManager:
    """Create a new chat log manager instance."""
    return ChatLogManager(db_path)
