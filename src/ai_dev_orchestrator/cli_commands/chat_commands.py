"""CLI commands for chat log management.

Provides commands for:
- Importing chat logs with deduplication
- Viewing timeline of conversations
- Comparing and searching user inputs
- Viewing session details
"""

import logging
from pathlib import Path
from typing import Optional

import click

from ai_dev_orchestrator.knowledge.chat_log_manager import (
    ChatLogManager,
    ImportResult,
    create_chat_manager,
)
from ai_dev_orchestrator.knowledge.database import init_database

logger = logging.getLogger(__name__)


def _print_import_summary(results: list[ImportResult]) -> None:
    """Print summary of import results."""
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    
    total_messages = sum(r.total_messages for r in results)
    new_messages = sum(r.new_messages for r in results if r.success)
    dup_messages = sum(r.duplicate_messages for r in results if r.success)
    merged = sum(1 for r in results if r.success and r.merged_with_existing)
    
    click.echo(f"\n📊 Import Summary:")
    click.echo(f"   Files processed: {total}")
    click.echo(f"   ✅ Successful: {successful}")
    click.echo(f"   ❌ Failed: {failed}")
    click.echo(f"   🔄 Merged with existing: {merged}")
    click.echo(f"\n📝 Messages:")
    click.echo(f"   Total in files: {total_messages}")
    click.echo(f"   ✨ New (added): {new_messages}")
    click.echo(f"   🔁 Duplicates (skipped): {dup_messages}")
    
    if failed > 0:
        click.echo(f"\n❌ Failed files:")
        for result in results:
            if not result.success:
                click.echo(f"   • {result.file_path.name}: {result.error}")


def _print_import_details(results: list[ImportResult]) -> None:
    """Print detailed import results."""
    click.echo(f"\n📋 Detailed Results:")
    
    for result in results:
        status = "✅" if result.success else "❌"
        click.echo(f"\n{status} {result.file_path.name}")
        
        if result.success:
            click.echo(f"   📁 Session: {result.session_id}")
            click.echo(f"   📝 Messages: {result.total_messages}")
            click.echo(f"   ✨ New: {result.new_messages}")
            click.echo(f"   🔁 Duplicates: {result.duplicate_messages}")
            if result.merged_with_existing:
                click.echo(f"   🔄 Merged with existing session")
        else:
            click.echo(f"   ❌ Error: {result.error}")


@click.group()
def chats():
    """Manage chat logs with intelligent deduplication."""
    pass


@chats.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--pattern', '-p', default='*.md', help='File pattern (default: *.md)')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed results')
@click.option('--init-db', is_flag=True, help='Initialize database first')
def import_logs(path: str, pattern: str, recursive: bool, verbose: bool, init_db: bool):
    """Import chat logs from a file or directory.
    
    Automatically deduplicates messages - if you save the same chat multiple times
    with additional content, only the new messages will be added.
    
    Examples:
        ai-dev chats import /path/to/ChatLogs -r
        ai-dev chats import chat_export.md
        ai-dev chats import ./logs -p "*.txt" --verbose
    """
    if init_db:
        click.echo("🔧 Initializing database...")
        init_database()
    
    path_obj = Path(path)
    manager = create_chat_manager()
    
    if path_obj.is_file():
        click.echo(f"📄 Importing file: {path_obj.name}")
        result = manager.import_file(path_obj)
        results = [result]
    else:
        file_count = len(list(path_obj.rglob(pattern) if recursive else path_obj.glob(pattern)))
        click.echo(f"📁 Importing from directory: {path_obj}")
        click.echo(f"📂 Pattern: {pattern} {'(recursive)' if recursive else ''}")
        click.echo(f"🔍 Found {file_count} files")
        results = manager.import_directory(path_obj, pattern, recursive)
    
    if not results:
        click.echo("❌ No files found or processed")
        return
    
    _print_import_summary(results)
    
    if verbose:
        _print_import_details(results)


@chats.command()
@click.option('--limit', '-n', default=20, help='Number of sessions to show')
@click.option('--verbose', '-v', is_flag=True, help='Show more details')
def sessions(limit: int, verbose: bool):
    """List all chat sessions.
    
    Shows sessions sorted by most recently updated.
    """
    manager = create_chat_manager()
    session_list = manager.get_sessions(limit=limit)
    
    if not session_list:
        click.echo("📭 No chat sessions found. Import some chat logs first.")
        return
    
    click.echo(f"💬 Chat Sessions ({len(session_list)} shown)")
    click.echo("=" * 60)
    
    for session in session_list:
        click.echo(f"\n📁 {session.id}")
        click.echo(f"   📝 Title: {session.title}")
        click.echo(f"   💬 Messages: {session.message_count} ({session.user_message_count}👤 / {session.assistant_message_count}🤖)")
        
        if session.first_message_at:
            click.echo(f"   📅 First: {session.first_message_at}")
        if session.last_message_at:
            click.echo(f"   📅 Last: {session.last_message_at}")
        
        if verbose:
            if session.topics:
                click.echo(f"   🏷️  Topics: {', '.join(session.topics)}")
            if session.summary:
                click.echo(f"   📋 Summary: {session.summary[:100]}...")
            if session.source_files:
                click.echo(f"   📂 Source files: {len(session.source_files)}")
                for f in session.source_files[:3]:
                    click.echo(f"      • {Path(f).name}")
                if len(session.source_files) > 3:
                    click.echo(f"      ... and {len(session.source_files) - 3} more")


@chats.command()
@click.argument('session_id')
@click.option('--role', '-r', type=click.Choice(['user', 'assistant']), help='Filter by role')
@click.option('--limit', '-n', default=50, help='Max messages to show')
@click.option('--truncate', '-t', default=200, help='Truncate message content at N chars (0=full)')
def view(session_id: str, role: Optional[str], limit: int, truncate: int):
    """View messages from a specific session.
    
    Examples:
        ai-dev chats view chat_abc123
        ai-dev chats view chat_abc123 --role user
        ai-dev chats view chat_abc123 -t 0  # Full content
    """
    manager = create_chat_manager()
    messages = manager.get_session_messages(session_id, role=role, limit=limit)
    
    if not messages:
        click.echo(f"❌ No messages found for session: {session_id}")
        return
    
    click.echo(f"💬 Session: {session_id}")
    click.echo(f"📝 Showing {len(messages)} messages" + (f" (role={role})" if role else ""))
    click.echo("=" * 60)
    
    for msg in messages:
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        content = msg['content']
        if truncate > 0 and len(content) > truncate:
            content = content[:truncate] + "..."
        
        click.echo(f"\n{role_icon} [{msg['sequence_num']}] {msg['role'].upper()}")
        click.echo(f"   {content}")


@chats.command()
@click.option('--role', '-r', type=click.Choice(['user', 'assistant']), default='user', help='Role to show')
@click.option('--limit', '-n', default=30, help='Max messages to show')
@click.option('--truncate', '-t', default=150, help='Truncate at N chars')
def inputs(role: str, limit: int, truncate: int):
    """List all user inputs (or assistant responses) across sessions.
    
    Great for seeing patterns in your questions or AI responses.
    
    Examples:
        ai-dev chats inputs  # All user inputs
        ai-dev chats inputs --role assistant  # All AI responses
    """
    manager = create_chat_manager()
    
    conn = manager._get_conn()
    rows = conn.execute("""
        SELECT m.*, s.title as session_title
        FROM chat_messages m
        JOIN chat_sessions s ON m.session_id = s.id
        WHERE m.role = ?
        ORDER BY m.created_at DESC
        LIMIT ?
    """, (role, limit)).fetchall()
    
    if not rows:
        click.echo(f"📭 No {role} messages found.")
        return
    
    role_icon = "👤" if role == 'user' else "🤖"
    click.echo(f"{role_icon} {role.upper()} Messages ({len(rows)} shown)")
    click.echo("=" * 60)
    
    for row in rows:
        content = row['content']
        if truncate > 0 and len(content) > truncate:
            content = content[:truncate] + "..."
        
        click.echo(f"\n📁 {row['session_title'][:40]}")
        click.echo(f"   {content}")


@chats.command()
@click.argument('query')
@click.option('--role', '-r', type=click.Choice(['user', 'assistant']), help='Filter by role')
@click.option('--limit', '-n', default=20, help='Max results')
def search(query: str, role: Optional[str], limit: int):
    """Search messages by content.
    
    Examples:
        ai-dev chats search "authentication"
        ai-dev chats search "how to" --role user
    """
    manager = create_chat_manager()
    results = manager.search_messages(query, role=role, limit=limit)
    
    if not results:
        click.echo(f"🔍 No messages found matching: {query}")
        return
    
    click.echo(f"🔍 Found {len(results)} messages matching '{query}'")
    click.echo("=" * 60)
    
    for msg in results:
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        session_title = msg.get('session_title', msg['session_id'])[:30]
        
        # Highlight the query in content
        content = msg['content'][:200]
        if len(msg['content']) > 200:
            content += "..."
        
        click.echo(f"\n{role_icon} [{session_title}]")
        click.echo(f"   {content}")


@chats.command()
@click.option('--start', '-s', help='Start date (YYYY-MM-DD)')
@click.option('--end', '-e', help='End date (YYYY-MM-DD)')
@click.option('--role', '-r', type=click.Choice(['user', 'assistant']), help='Filter by role')
@click.option('--limit', '-n', default=50, help='Max messages')
def timeline(start: Optional[str], end: Optional[str], role: Optional[str], limit: int):
    """View messages in chronological order.
    
    Examples:
        ai-dev chats timeline
        ai-dev chats timeline --start 2024-01-01 --end 2024-12-31
        ai-dev chats timeline --role user
    """
    manager = create_chat_manager()
    messages = manager.get_timeline(start_date=start, end_date=end, role=role)
    
    if not messages:
        click.echo("📭 No messages found in timeline.")
        return
    
    messages = messages[:limit]  # Apply limit after query
    
    date_range = ""
    if start or end:
        date_range = f" ({start or '...'} to {end or '...'})"
    
    click.echo(f"📅 Timeline{date_range}")
    click.echo(f"📝 Showing {len(messages)} messages")
    click.echo("=" * 60)
    
    current_date = None
    for msg in messages:
        msg_date = msg.get('created_at', '')[:10] if msg.get('created_at') else 'Unknown'
        
        if msg_date != current_date:
            current_date = msg_date
            click.echo(f"\n📆 {current_date}")
            click.echo("-" * 40)
        
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        session_title = msg.get('session_title', '')[:25]
        content = msg['content'][:100]
        if len(msg['content']) > 100:
            content += "..."
        
        click.echo(f"{role_icon} [{session_title}] {content}")


@chats.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed stats')
def stats(verbose: bool):
    """Show chat log statistics.
    
    Displays counts of sessions, messages, and deduplication effectiveness.
    """
    manager = create_chat_manager()
    stat_data = manager.get_stats()
    
    click.echo("📊 Chat Log Statistics")
    click.echo("=" * 40)
    click.echo(f"💬 Sessions: {stat_data['total_sessions']}")
    click.echo(f"📝 Total Messages: {stat_data['total_messages']}")
    click.echo(f"   👤 User: {stat_data['user_messages']}")
    click.echo(f"   🤖 Assistant: {stat_data['assistant_messages']}")
    click.echo(f"📂 Source Files: {stat_data['source_files']}")
    
    deduped = stat_data.get('deduplicated_messages') or 0
    if deduped > 0:
        click.echo(f"\n🔁 Deduplication Stats:")
        click.echo(f"   Duplicates removed: {deduped}")
        total_in_files = stat_data['total_messages'] + deduped
        savings = (deduped / total_in_files * 100) if total_in_files > 0 else 0
        click.echo(f"   Storage savings: {savings:.1f}%")
    
    if verbose:
        sessions = manager.get_sessions(limit=5)
        if sessions:
            click.echo(f"\n📅 Recent Sessions:")
            for s in sessions:
                click.echo(f"   • {s.title[:40]} ({s.message_count} msgs)")


if __name__ == '__main__':
    chats()
