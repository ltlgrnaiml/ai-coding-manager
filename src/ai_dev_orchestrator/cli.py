"""CLI for AI Dev Orchestrator.

Provides command-line tools for:
- Creating plans, discussions, and sessions
- Managing the knowledge archive
- Running health checks on LLM integrations
"""

import argparse
import sys


def cmd_new_plan(args):
    """Create a new plan."""
    from ai_dev_orchestrator.workflow import create_plan
    
    plan = create_plan(
        title=args.title,
        objective=args.objective or "",
        granularity=args.granularity,
    )
    print(f"Created {plan['id']}: {plan['title']}")
    print(f"  Granularity: {plan['granularity']}")
    print(f"  Path: .plans/{plan['id']}*.json")


def cmd_new_discussion(args):
    """Create a new discussion."""
    from ai_dev_orchestrator.workflow import create_discussion
    
    path = create_discussion(
        title=args.title,
        summary=args.summary or "",
    )
    print(f"Created discussion: {path}")


def cmd_new_session(args):
    """Create a new session."""
    from ai_dev_orchestrator.workflow import create_session
    
    path = create_session(
        title=args.title,
        objective=args.objective or "",
    )
    print(f"Created session: {path}")


def cmd_health(args):
    """Check LLM health status."""
    from ai_dev_orchestrator.llm import check_health, LLMStatus
    
    result = check_health(force_refresh=True)
    
    status_emoji = {
        LLMStatus.AVAILABLE: "✅",
        LLMStatus.UNAVAILABLE: "❌",
        LLMStatus.NO_API_KEY: "⚠️",
        LLMStatus.RATE_LIMITED: "⏳",
        LLMStatus.ERROR: "❌",
    }
    
    print(f"{status_emoji.get(result.status, '?')} LLM Status: {result.status.value}")
    print(f"   Message: {result.message}")
    if result.model:
        print(f"   Model: {result.model}")


def cmd_stats(args):
    """Show LLM usage statistics."""
    from ai_dev_orchestrator.llm import get_llm_usage_stats
    
    stats = get_llm_usage_stats()
    print("📊 LLM Usage Statistics")
    print(f"   Total Calls: {stats['total_calls']}")
    print(f"   Input Tokens: {stats['total_input_tokens']:,}")
    print(f"   Output Tokens: {stats['total_output_tokens']:,}")
    print(f"   Estimated Cost: ${stats['total_cost']:.4f}")


def cmd_init_db(args):
    """Initialize the knowledge database."""
    from ai_dev_orchestrator.knowledge import init_database, DB_PATH
    
    conn = init_database()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")


def cmd_models(args):
    """List available xAI models."""
    from ai_dev_orchestrator.llm import get_available_models, get_current_model
    
    current = get_current_model()
    models = get_available_models()
    
    print("📦 Available xAI Models\n")
    for m in models:
        marker = "→" if m.id == current else " "
        reasoning = " 🧠" if m.reasoning else ""
        print(f"{marker} {m.id}")
        print(f"    {m.name}{reasoning}")
        print(f"    Context: {m.context_window:,} tokens | ${m.input_price}/${m.output_price} per 1M")
        print()


def cmd_chats(args):
    """Handle chats commands."""
    from ai_dev_orchestrator.cli_commands import chat_commands
    from ai_dev_orchestrator.knowledge.database import init_database
    
    if args.chats_command == "import":
        chat_commands.import_logs.callback(
            path=args.path,
            pattern=args.pattern,
            recursive=args.recursive,
            verbose=args.verbose,
            init_db=args.init_db
        )
    elif args.chats_command == "sessions":
        chat_commands.sessions.callback(
            limit=args.limit,
            verbose=args.verbose
        )
    elif args.chats_command == "view":
        chat_commands.view.callback(
            session_id=args.session_id,
            role=args.role,
            limit=args.limit,
            truncate=args.truncate
        )
    elif args.chats_command == "inputs":
        chat_commands.inputs.callback(
            role=args.role or 'user',
            limit=args.limit,
            truncate=args.truncate
        )
    elif args.chats_command == "search":
        chat_commands.search.callback(
            query=args.query,
            role=args.role,
            limit=args.limit
        )
    elif args.chats_command == "timeline":
        chat_commands.timeline.callback(
            start=args.start,
            end=args.end,
            role=args.role,
            limit=args.limit
        )
    elif args.chats_command == "stats":
        chat_commands.stats.callback(verbose=args.verbose)
    else:
        print("Usage: ai-dev chats {import|sessions|view|inputs|search|timeline|stats}")
        print("Use 'ai-dev chats --help' for more information.")


def cmd_archive(args):
    """Handle archive commands."""
    from ai_dev_orchestrator.cli_commands.archive_artifacts import (
        downloads, files, directory, status
    )
    
    if args.archive_command == "downloads":
        downloads.callback(
            downloads_path=args.downloads_path,
            pattern=args.pattern,
            verbose=args.verbose,
            init_db=args.init_db
        )
    elif args.archive_command == "files":
        files.callback(
            files=tuple(args.files),
            verbose=args.verbose,
            init_db=args.init_db
        )
    elif args.archive_command == "directory":
        directory.callback(
            directory=args.directory,
            pattern=args.pattern,
            recursive=args.recursive,
            verbose=args.verbose,
            init_db=args.init_db
        )
    elif args.archive_command == "status":
        status.callback(verbose=args.verbose)
    else:
        print("Usage: ai-dev archive {downloads|files|directory|status}")
        print("Use 'ai-dev archive --help' for more information.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="ai-dev",
        description="AI Dev Orchestrator - Structured AI-assisted code development",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # new-plan
    p_plan = subparsers.add_parser("new-plan", help="Create a new plan")
    p_plan.add_argument("title", help="Plan title")
    p_plan.add_argument("-o", "--objective", help="Plan objective")
    p_plan.add_argument("-g", "--granularity", choices=["L1", "L2", "L3"], default="L1",
                        help="Plan granularity level")
    p_plan.set_defaults(func=cmd_new_plan)
    
    # new-discussion
    p_disc = subparsers.add_parser("new-discussion", help="Create a new discussion")
    p_disc.add_argument("title", help="Discussion title")
    p_disc.add_argument("-s", "--summary", help="Brief summary")
    p_disc.set_defaults(func=cmd_new_discussion)
    
    # new-session
    p_sess = subparsers.add_parser("new-session", help="Create a new session")
    p_sess.add_argument("title", help="Session title")
    p_sess.add_argument("-o", "--objective", help="Session objective")
    p_sess.set_defaults(func=cmd_new_session)
    
    # health
    p_health = subparsers.add_parser("health", help="Check LLM health")
    p_health.set_defaults(func=cmd_health)
    
    # stats
    p_stats = subparsers.add_parser("stats", help="Show LLM usage statistics")
    p_stats.set_defaults(func=cmd_stats)
    
    # init-db
    p_initdb = subparsers.add_parser("init-db", help="Initialize knowledge database")
    p_initdb.set_defaults(func=cmd_init_db)
    
    # models
    p_models = subparsers.add_parser("models", help="List available xAI models")
    p_models.set_defaults(func=cmd_models)
    
    # archive
    p_archive = subparsers.add_parser("archive", help="Archive markdown artifacts to knowledge database")
    archive_subparsers = p_archive.add_subparsers(dest="archive_command", help="Archive commands")
    
    # archive downloads
    p_archive_downloads = archive_subparsers.add_parser("downloads", help="Process Downloads folder")
    p_archive_downloads.add_argument("-d", "--downloads-path", help="Custom Downloads folder path")
    p_archive_downloads.add_argument("-p", "--pattern", default="*.md", help="File pattern (default: *.md)")
    p_archive_downloads.add_argument("-v", "--verbose", action="store_true", help="Show detailed results")
    p_archive_downloads.add_argument("--init-db", action="store_true", help="Initialize database first")
    
    # archive files
    p_archive_files = archive_subparsers.add_parser("files", help="Process specific files")
    p_archive_files.add_argument("files", nargs="+", help="File paths to process")
    p_archive_files.add_argument("-v", "--verbose", action="store_true", help="Show detailed results")
    p_archive_files.add_argument("--init-db", action="store_true", help="Initialize database first")
    
    # archive directory
    p_archive_dir = archive_subparsers.add_parser("directory", help="Process directory")
    p_archive_dir.add_argument("directory", help="Directory path to process")
    p_archive_dir.add_argument("-p", "--pattern", default="*.md", help="File pattern (default: *.md)")
    p_archive_dir.add_argument("-r", "--recursive", action="store_true", help="Process recursively")
    p_archive_dir.add_argument("-v", "--verbose", action="store_true", help="Show detailed results")
    p_archive_dir.add_argument("--init-db", action="store_true", help="Initialize database first")
    
    # archive status
    p_archive_status = archive_subparsers.add_parser("status", help="Show database status")
    p_archive_status.add_argument("-v", "--verbose", action="store_true", help="Show detailed statistics")
    
    p_archive.set_defaults(func=cmd_archive)
    
    # chats
    p_chats = subparsers.add_parser("chats", help="Manage chat logs with deduplication")
    chats_subparsers = p_chats.add_subparsers(dest="chats_command", help="Chat commands")
    
    # chats import
    p_chats_import = chats_subparsers.add_parser("import", help="Import chat logs from file/directory")
    p_chats_import.add_argument("path", help="File or directory path")
    p_chats_import.add_argument("-p", "--pattern", default="*.md", help="File pattern (default: *.md)")
    p_chats_import.add_argument("-r", "--recursive", action="store_true", help="Process subdirectories")
    p_chats_import.add_argument("-v", "--verbose", action="store_true", help="Show detailed results")
    p_chats_import.add_argument("--init-db", action="store_true", help="Initialize database first")
    
    # chats sessions
    p_chats_sessions = chats_subparsers.add_parser("sessions", help="List chat sessions")
    p_chats_sessions.add_argument("-n", "--limit", type=int, default=20, help="Number to show")
    p_chats_sessions.add_argument("-v", "--verbose", action="store_true", help="Show details")
    
    # chats view
    p_chats_view = chats_subparsers.add_parser("view", help="View session messages")
    p_chats_view.add_argument("session_id", help="Session ID")
    p_chats_view.add_argument("-r", "--role", choices=["user", "assistant"], help="Filter by role")
    p_chats_view.add_argument("-n", "--limit", type=int, default=50, help="Max messages")
    p_chats_view.add_argument("-t", "--truncate", type=int, default=200, help="Truncate at N chars")
    
    # chats inputs
    p_chats_inputs = chats_subparsers.add_parser("inputs", help="List all user inputs")
    p_chats_inputs.add_argument("-r", "--role", choices=["user", "assistant"], help="Role to show")
    p_chats_inputs.add_argument("-n", "--limit", type=int, default=30, help="Max messages")
    p_chats_inputs.add_argument("-t", "--truncate", type=int, default=150, help="Truncate at N chars")
    
    # chats search
    p_chats_search = chats_subparsers.add_parser("search", help="Search messages")
    p_chats_search.add_argument("query", help="Search query")
    p_chats_search.add_argument("-r", "--role", choices=["user", "assistant"], help="Filter by role")
    p_chats_search.add_argument("-n", "--limit", type=int, default=20, help="Max results")
    
    # chats timeline
    p_chats_timeline = chats_subparsers.add_parser("timeline", help="View chronological timeline")
    p_chats_timeline.add_argument("-s", "--start", help="Start date (YYYY-MM-DD)")
    p_chats_timeline.add_argument("-e", "--end", help="End date (YYYY-MM-DD)")
    p_chats_timeline.add_argument("-r", "--role", choices=["user", "assistant"], help="Filter by role")
    p_chats_timeline.add_argument("-n", "--limit", type=int, default=50, help="Max messages")
    
    # chats stats
    p_chats_stats = chats_subparsers.add_parser("stats", help="Show statistics")
    p_chats_stats.add_argument("-v", "--verbose", action="store_true", help="Show detailed stats")
    
    p_chats.set_defaults(func=cmd_chats)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
