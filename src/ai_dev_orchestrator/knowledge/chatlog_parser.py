"""Chat Log Parser for Cascade/Windsurf markdown exports.

Per DISC-0024: Parse markdown chat logs with ### User Input / ### Planner Response structure.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .chatlog_database import (
    get_db_path,
    init_database,
    insert_chat_log,
    insert_chat_turn,
    insert_command,
    insert_file_ref,
    update_fts_index,
    get_stats,
)


@dataclass
class ChatTurn:
    """A single turn in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    turn_index: int
    has_code_blocks: bool = False
    has_file_refs: bool = False
    has_commands: bool = False
    file_refs: list[str] = field(default_factory=list)
    commands: list[tuple[str, bool]] = field(default_factory=list)  # (command, was_accepted)


@dataclass
class ParsedChatLog:
    """A parsed chat log file."""

    file_path: str
    filename: str
    title: str | None
    file_size: int
    modified_date: str | None
    turns: list[ChatTurn]
    projects_referenced: list[str] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def word_count(self) -> int:
        return sum(len(t.content.split()) for t in self.turns)


def parse_cascade_markdown(file_path: Path) -> ParsedChatLog:
    """Parse a Cascade/Windsurf markdown chat export."""
    content = file_path.read_text(encoding="utf-8", errors="replace")
    stat = file_path.stat()

    # Extract title from first heading or filename
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem

    # Parse turns - look for ### User Input and ### Planner Response
    turns: list[ChatTurn] = []
    turn_index = 0

    # Split by ### headers
    sections = re.split(r"(?=^### )", content, flags=re.MULTILINE)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Determine role
        if section.startswith("### User Input"):
            role = "user"
            # Remove header
            section_content = re.sub(r"^### User Input\s*\n?", "", section, flags=re.MULTILINE).strip()
        elif section.startswith("### Planner Response") or section.startswith("### Assistant"):
            role = "assistant"
            section_content = re.sub(r"^### (Planner Response|Assistant)\s*\n?", "", section, flags=re.MULTILINE).strip()
        else:
            # Skip non-turn sections (like # title)
            continue

        if not section_content:
            continue

        # Analyze content
        has_code_blocks = "```" in section_content
        has_file_refs = bool(re.search(r"\[.*?\]\(file://", section_content))
        has_commands = bool(re.search(r"\*User accepted the command", section_content))

        # Extract file references
        file_refs = re.findall(r"\[.*?\]\(file://([^)]+)\)", section_content)
        file_refs = [f.split(":")[0] for f in file_refs]  # Remove line numbers

        # Extract commands
        commands: list[tuple[str, bool]] = []
        command_matches = re.findall(r"\*User (accepted|rejected) the command `([^`]+)`\*", section_content)
        for acceptance, cmd in command_matches:
            commands.append((cmd, acceptance == "accepted"))

        turn = ChatTurn(
            role=role,
            content=section_content,
            turn_index=turn_index,
            has_code_blocks=has_code_blocks,
            has_file_refs=has_file_refs,
            has_commands=has_commands,
            file_refs=file_refs,
            commands=commands,
        )
        turns.append(turn)
        turn_index += 1

    # Extract project references from file paths
    projects: set[str] = set()
    for turn in turns:
        for ref in turn.file_refs:
            # Extract project name from path like /home/user/coding/project-name/...
            match = re.search(r"/coding/([^/]+)/", ref)
            if match:
                projects.add(match.group(1))

    return ParsedChatLog(
        file_path=str(file_path),
        filename=file_path.name,
        title=title,
        file_size=stat.st_size,
        modified_date=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        turns=turns,
        projects_referenced=list(projects),
    )


def ingest_chatlog(parsed: ParsedChatLog) -> int:
    """Ingest a parsed chat log into the database. Returns chat_log_id."""
    import json

    # Insert main record
    chat_log_id = insert_chat_log(
        file_path=parsed.file_path,
        filename=parsed.filename,
        title=parsed.title,
        file_size=parsed.file_size,
        modified_date=parsed.modified_date,
        turn_count=parsed.turn_count,
        word_count=parsed.word_count,
        projects_referenced=json.dumps(parsed.projects_referenced) if parsed.projects_referenced else None,
    )

    # Insert turns
    for turn in parsed.turns:
        turn_id = insert_chat_turn(
            chat_log_id=chat_log_id,
            turn_index=turn.turn_index,
            role=turn.role,
            content=turn.content,
            word_count=len(turn.content.split()),
            has_code_blocks=turn.has_code_blocks,
            has_file_refs=turn.has_file_refs,
            has_commands=turn.has_commands,
        )

        # Insert file references
        for file_ref in turn.file_refs:
            project = None
            match = re.search(r"/coding/([^/]+)/", file_ref)
            if match:
                project = match.group(1)
            insert_file_ref(chat_log_id, turn_id, file_ref, project)

        # Insert commands
        for cmd, was_accepted in turn.commands:
            insert_command(chat_log_id, turn_id, cmd, was_accepted)

    return chat_log_id


def ingest_all_chatlogs(chatlog_dir: Path | None = None) -> dict:
    """Ingest all chat logs from a directory.

    Args:
        chatlog_dir: Directory containing chat logs. Defaults to ChatLogs folder.

    Returns:
        Stats dictionary with ingestion results.
    """
    if chatlog_dir is None:
        chatlog_dir = get_db_path().parent

    # Initialize database
    init_database()

    results = {
        "total_files": 0,
        "ingested": 0,
        "failed": 0,
        "errors": [],
    }

    # Find all markdown files (excluding Zone.Identifier files)
    md_files = [
        f for f in chatlog_dir.glob("*.md")
        if not f.name.endswith(":Zone.Identifier") and "Zone.Identifier" not in f.name
    ]

    results["total_files"] = len(md_files)
    print(f"Found {len(md_files)} chat log files to ingest...")

    for md_file in md_files:
        try:
            parsed = parse_cascade_markdown(md_file)
            ingest_chatlog(parsed)
            results["ingested"] += 1
            print(f"  ✓ {md_file.name} ({parsed.turn_count} turns)")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"file": md_file.name, "error": str(e)})
            print(f"  ✗ {md_file.name}: {e}")

    # Rebuild FTS index
    print("Rebuilding FTS index...")
    update_fts_index()

    # Get final stats
    stats = get_stats()
    results.update(stats)

    print(f"\nIngestion complete:")
    print(f"  - Chat logs: {stats['total_chatlogs']}")
    print(f"  - Turns: {stats['total_turns']}")
    print(f"  - Words: {stats['total_words']:,}")
    print(f"  - File refs: {stats['total_file_refs']}")
    print(f"  - Commands: {stats['total_commands']}")

    return results


if __name__ == "__main__":
    # CLI entry point for bulk ingestion
    import sys

    chatlog_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    results = ingest_all_chatlogs(chatlog_dir)

    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} files failed to ingest")
        for err in results["errors"]:
            print(f"   - {err['file']}: {err['error']}")
