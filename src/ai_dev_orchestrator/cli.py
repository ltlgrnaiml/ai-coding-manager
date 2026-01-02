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
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
