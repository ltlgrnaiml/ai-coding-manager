#!/usr/bin/env python3
"""Ingest chat logs from .chat_logs folder into AIKH chatlogs.db.

Parses Windsurf/Cascade exported markdown chat logs and populates:
- chat_logs: Main log metadata
- chat_turns: Individual user/assistant turns
- chat_file_refs: Extracted file references
- chat_commands: Extracted shell commands

Usage:
    python scripts/ingest_chat_logs.py [source_dir]
    
    source_dir: Path to chat logs folder (default: .chat_logs)
"""

import hashlib
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# AIKH Configuration
AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
CHATLOGS_DB_PATH = AIKH_HOME / "chatlogs.db"


def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    AIKH_HOME.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CHATLOGS_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def parse_chat_log(file_path: Path) -> dict:
    """Parse a markdown chat log file.
    
    Expected format:
    - User messages start with "**User:**" or "## User" or similar
    - Assistant messages start with "**Assistant:**" or "## Assistant"
    - Code blocks are fenced with ```
    - File references appear as paths like /path/to/file.py
    - Commands appear in code blocks or after $ prompt
    """
    content = file_path.read_text(encoding='utf-8', errors='replace')
    
    # Extract title from first heading or filename
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem
    
    # Parse turns - look for role markers
    turns = []
    current_role = None
    current_content = []
    
    # Common role patterns
    role_patterns = [
        (r'^### User Input', 'user'),
        (r'^### Planner Response', 'assistant'),
        (r'^### Assistant Response', 'assistant'),
        (r'^\*\*User:?\*\*', 'user'),
        (r'^## User', 'user'),
        (r'^\*\*Assistant:?\*\*', 'assistant'),
        (r'^## Assistant', 'assistant'),
        (r'^\*\*System:?\*\*', 'system'),
        (r'^## System', 'system'),
        (r'^\*\*Human:?\*\*', 'user'),
        (r'^## Human', 'user'),
        (r'^\*\*Claude:?\*\*', 'assistant'),
        (r'^\*\*Cascade:?\*\*', 'assistant'),
        (r'^---\s*$', None),  # Section divider - ignore
    ]
    
    lines = content.split('\n')
    for line in lines:
        # Check for role change
        new_role = None
        matched_pattern = False
        for pattern, role in role_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                new_role = role
                matched_pattern = True
                break
        
        if matched_pattern and new_role is None:
            # Skip dividers and other non-role markers
            continue
        
        if new_role:
            # Save previous turn
            if current_role and current_content:
                turn_text = '\n'.join(current_content).strip()
                if turn_text:
                    turns.append({
                        'role': current_role,
                        'content': turn_text,
                    })
            current_role = new_role
            current_content = []
            # Add rest of line after role marker
            rest = re.sub(r'^\*\*\w+:?\*\*\s*', '', line)
            rest = re.sub(r'^##\s*\w+\s*', '', rest)
            if rest.strip():
                current_content.append(rest)
        else:
            current_content.append(line)
    
    # Don't forget last turn
    if current_role and current_content:
        turn_text = '\n'.join(current_content).strip()
        if turn_text:
            turns.append({
                'role': current_role,
                'content': turn_text,
            })
    
    # If no turns found, treat entire content as single assistant turn
    if not turns:
        turns = [{'role': 'assistant', 'content': content}]
    
    # Enrich turns with metadata
    for turn in turns:
        text = turn['content']
        turn['word_count'] = len(text.split())
        turn['has_code_blocks'] = 1 if '```' in text else 0
        turn['has_file_refs'] = 1 if re.search(r'[/\\][\w.-]+\.(py|js|ts|tsx|json|md|yaml|yml|sh)', text) else 0
        turn['has_commands'] = 1 if re.search(r'^\s*\$\s+\w+|```(?:bash|sh|shell)', text, re.MULTILINE) else 0
    
    # Extract file references
    file_refs = []
    file_pattern = r'(?:^|[\s`"\'])(/[\w./-]+\.(?:py|js|ts|tsx|jsx|json|md|yaml|yml|sh|css|html|sql|go|rs|cpp|c|h))'
    for match in re.finditer(file_pattern, content):
        file_refs.append(match.group(1))
    
    # Extract commands
    commands = []
    cmd_pattern = r'^\s*\$\s+(.+)$'
    for match in re.finditer(cmd_pattern, content, re.MULTILINE):
        commands.append(match.group(1).strip())
    
    # Also extract from bash code blocks
    bash_block_pattern = r'```(?:bash|sh|shell)\n(.*?)```'
    for match in re.finditer(bash_block_pattern, content, re.DOTALL):
        block_content = match.group(1)
        for line in block_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    
    # Dedupe
    file_refs = list(set(file_refs))
    commands = list(set(commands))[:50]  # Limit commands
    
    return {
        'title': title,
        'content': content,
        'turns': turns,
        'file_refs': file_refs,
        'commands': commands,
        'word_count': len(content.split()),
        'turn_count': len(turns),
    }


def ingest_chat_log(conn: sqlite3.Connection, file_path: Path) -> tuple[int, dict]:
    """Ingest a single chat log file.
    
    Returns:
        Tuple of (chat_log_id, status_dict)
    """
    # Check if already ingested
    cursor = conn.execute(
        "SELECT id FROM chat_logs WHERE file_path = ?",
        (str(file_path),)
    )
    existing = cursor.fetchone()
    if existing:
        return existing['id'], {'status': 'skipped', 'reason': 'already exists'}
    
    # Parse the file
    try:
        parsed = parse_chat_log(file_path)
    except Exception as e:
        return -1, {'status': 'error', 'error': str(e)}
    
    # Get file metadata
    stat = file_path.stat()
    
    # Insert chat_log
    cursor = conn.execute("""
        INSERT INTO chat_logs 
        (file_path, filename, title, file_size, created_date, modified_date, 
         turn_count, word_count, projects_referenced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(file_path),
        file_path.name,
        parsed['title'],
        stat.st_size,
        datetime.fromtimestamp(stat.st_ctime).isoformat(),
        datetime.fromtimestamp(stat.st_mtime).isoformat(),
        parsed['turn_count'],
        parsed['word_count'],
        None,  # projects_referenced - could extract later
    ))
    chat_log_id = cursor.lastrowid
    
    # Insert turns
    for i, turn in enumerate(parsed['turns']):
        cursor = conn.execute("""
            INSERT INTO chat_turns
            (chat_log_id, turn_index, role, content, word_count, 
             has_code_blocks, has_file_refs, has_commands)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_log_id,
            i,
            turn['role'],
            turn['content'],
            turn['word_count'],
            turn['has_code_blocks'],
            turn['has_file_refs'],
            turn['has_commands'],
        ))
        turn_id = cursor.lastrowid
        
        # Insert file refs for this turn
        for file_ref in parsed['file_refs']:
            if file_ref in turn['content']:
                conn.execute("""
                    INSERT OR IGNORE INTO chat_file_refs
                    (chat_log_id, turn_id, file_path, project_name)
                    VALUES (?, ?, ?, ?)
                """, (chat_log_id, turn_id, file_ref, None))
    
    # Insert commands
    for cmd in parsed['commands']:
        conn.execute("""
            INSERT INTO chat_commands
            (chat_log_id, turn_id, command, was_accepted)
            VALUES (?, ?, ?, ?)
        """, (chat_log_id, None, cmd, 0))
    
    conn.commit()
    
    return chat_log_id, {
        'status': 'ingested',
        'turns': len(parsed['turns']),
        'file_refs': len(parsed['file_refs']),
        'commands': len(parsed['commands']),
    }


def main():
    """Main entry point."""
    # Get source directory
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1])
    else:
        source_dir = Path('.chat_logs')
    
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        sys.exit(1)
    
    # Get all markdown files
    md_files = list(source_dir.glob('*.md'))
    if not md_files:
        print(f"No markdown files found in {source_dir}")
        sys.exit(1)
    
    print(f"Found {len(md_files)} chat log files in {source_dir}")
    print(f"Database: {CHATLOGS_DB_PATH}")
    print("=" * 60)
    
    # Connect to database
    conn = get_db_connection()
    
    # Get initial count
    cursor = conn.execute("SELECT COUNT(*) FROM chat_logs")
    initial_count = cursor.fetchone()[0]
    
    # Process each file
    ingested = 0
    skipped = 0
    failed = 0
    total_turns = 0
    
    for md_file in sorted(md_files):
        if md_file.name == 'README.md':
            continue
            
        print(f"  {md_file.name[:50]:<50}", end=" ", flush=True)
        
        chat_id, result = ingest_chat_log(conn, md_file)
        
        if result['status'] == 'ingested':
            ingested += 1
            total_turns += result['turns']
            print(f"OK ({result['turns']} turns)")
        elif result['status'] == 'skipped':
            skipped += 1
            print(f"SKIPPED ({result['reason']})")
        else:
            failed += 1
            print(f"FAILED ({result.get('error', 'unknown')})")
    
    # Get final count
    cursor = conn.execute("SELECT COUNT(*) FROM chat_logs")
    final_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM chat_turns")
    turn_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM chat_file_refs")
    ref_count = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM chat_commands")
    cmd_count = cursor.fetchone()[0]
    
    conn.close()
    
    print("=" * 60)
    print(f"Results: {ingested} ingested, {skipped} skipped, {failed} failed")
    print(f"Chat logs in DB: {final_count} (added {final_count - initial_count})")
    print(f"Total turns: {turn_count}")
    print(f"File references: {ref_count}")
    print(f"Commands: {cmd_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
