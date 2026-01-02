#!/usr/bin/env python3
"""Sync Monitor: Track engineering-tools changes for ai-dev-orchestrator absorption.

This script monitors the engineering-tools repo for innovations and generates
AI-readable TODO lists for absorption into ai-dev-orchestrator.

Usage:
    python scripts/sync_from_upstream.py [--since COMMIT] [--output FILE]
    python scripts/sync_from_upstream.py --watch  # Continuous monitoring
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Configuration
UPSTREAM_REPO = Path("C:/Users/Mycahya/CascadeProjects/engineering-tools")
SYNC_STATE_FILE = Path(__file__).parent.parent / ".sync_state.json"
OUTPUT_DIR = Path(__file__).parent.parent / ".sync_todos"

# Categories of changes to track
TRACK_PATTERNS = {
    "adrs": {
        "paths": [".adrs/"],
        "description": "Architecture Decision Records",
        "priority": "high",
    },
    "contracts": {
        "paths": ["shared/contracts/"],
        "description": "Pydantic contracts (SSOT)",
        "priority": "high",
    },
    "workflow": {
        "paths": [".discussions/", ".plans/", ".sessions/"],
        "description": "AI Development Workflow artifacts",
        "priority": "medium",
    },
    "gateway": {
        "paths": ["gateway/"],
        "description": "API Gateway patterns",
        "priority": "medium",
    },
    "scripts": {
        "paths": ["scripts/workflow/"],
        "description": "Workflow automation scripts",
        "priority": "medium",
    },
    "ci": {
        "paths": ["ci/"],
        "description": "CI/CD pipeline",
        "priority": "low",
    },
    "docs": {
        "paths": ["docs/", "AGENTS.md"],
        "description": "Documentation and AI guides",
        "priority": "low",
    },
}


def run_git(args: list[str], cwd: Path = UPSTREAM_REPO) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"Git error: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def get_sync_state() -> dict[str, Any]:
    """Load the last sync state."""
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text(encoding="utf-8"))
    return {"last_commit": None, "last_sync": None, "absorbed": []}


def save_sync_state(state: dict[str, Any]) -> None:
    """Save the current sync state."""
    SYNC_STATE_FILE.write_text(
        json.dumps(state, indent=2, default=str), encoding="utf-8"
    )


def get_commits_since(since_commit: str | None = None) -> list[dict[str, Any]]:
    """Get commits since the last sync point."""
    if since_commit:
        range_spec = f"{since_commit}..HEAD"
    else:
        # Default to last 50 commits if no sync point
        range_spec = "-50"

    # Get commit log with details
    log_format = "%H|%s|%an|%ai|%b|||"
    output = run_git(
        ["log", range_spec, f"--pretty=format:{log_format}", "--name-status"]
    )

    if not output:
        return []

    commits = []
    current_commit = None

    for line in output.split("\n"):
        if "|||" in line:
            # New commit header
            parts = line.replace("|||", "").split("|")
            if len(parts) >= 4:
                current_commit = {
                    "hash": parts[0],
                    "subject": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                    "body": parts[4] if len(parts) > 4 else "",
                    "files": [],
                }
                commits.append(current_commit)
        elif current_commit and line.strip():
            # File change line (M/A/D filename)
            parts = line.split("\t")
            if len(parts) >= 2:
                current_commit["files"].append(
                    {"status": parts[0], "path": parts[1]}
                )

    return commits


def categorize_commit(commit: dict[str, Any]) -> dict[str, list[str]]:
    """Categorize a commit's changes by track pattern."""
    categories: dict[str, list[str]] = {}

    for file_change in commit["files"]:
        file_path = file_change["path"]
        for category, config in TRACK_PATTERNS.items():
            for pattern in config["paths"]:
                if file_path.startswith(pattern) or pattern in file_path:
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(file_path)
                    break

    return categories


def generate_todo_entry(
    commit: dict[str, Any], categories: dict[str, list[str]]
) -> dict[str, Any]:
    """Generate a TODO entry from a commit."""
    # Determine overall priority
    priorities = []
    for cat in categories:
        if cat in TRACK_PATTERNS:
            priorities.append(TRACK_PATTERNS[cat]["priority"])

    priority_order = {"high": 0, "medium": 1, "low": 2}
    priority = min(priorities, key=lambda p: priority_order.get(p, 99)) if priorities else "low"

    return {
        "commit": commit["hash"][:8],
        "date": commit["date"],
        "subject": commit["subject"],
        "body": commit["body"],
        "categories": categories,
        "priority": priority,
        "status": "pending",
        "action_required": determine_action(commit, categories),
    }


def determine_action(
    commit: dict[str, Any], categories: dict[str, list[str]]
) -> str:
    """Determine what action is needed for this change."""
    subject = commit["subject"].lower()

    # Check for specific patterns in commit message
    if any(x in subject for x in ["add", "create", "new"]):
        return "REVIEW_AND_ADOPT"
    elif any(x in subject for x in ["fix", "bug", "patch"]):
        return "CHECK_IF_APPLICABLE"
    elif any(x in subject for x in ["refactor", "rename", "move"]):
        return "SYNC_STRUCTURE"
    elif any(x in subject for x in ["update", "improve", "enhance"]):
        return "EVALUATE_IMPROVEMENT"
    elif "adr" in subject:
        return "REVIEW_ADR"
    elif "contract" in subject:
        return "SYNC_CONTRACT"
    else:
        return "REVIEW"


def generate_sync_report(
    commits: list[dict[str, Any]], output_file: Path | None = None
) -> str:
    """Generate a comprehensive sync report."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    todos = []
    for commit in commits:
        categories = categorize_commit(commit)
        if categories:  # Only include commits with tracked changes
            todos.append(generate_todo_entry(commit, categories))

    if not todos:
        return "No relevant changes found since last sync."

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    todos.sort(key=lambda t: priority_order.get(t["priority"], 99))

    # Generate markdown report
    report_lines = [
        "# Engineering-Tools Sync Report",
        f"Generated: {datetime.now().isoformat()}",
        f"Commits analyzed: {len(commits)}",
        f"Relevant changes: {len(todos)}",
        "",
        "---",
        "",
        "## AI TODO List",
        "",
        "Review these changes from engineering-tools and determine what to absorb into ai-dev-orchestrator.",
        "",
    ]

    # Group by priority
    for priority in ["high", "medium", "low"]:
        priority_todos = [t for t in todos if t["priority"] == priority]
        if priority_todos:
            report_lines.append(f"### Priority: {priority.upper()}")
            report_lines.append("")

            for todo in priority_todos:
                report_lines.append(f"#### [{todo['commit']}] {todo['subject']}")
                report_lines.append(f"- **Date**: {todo['date']}")
                report_lines.append(f"- **Action**: `{todo['action_required']}`")
                report_lines.append(f"- **Categories**: {', '.join(todo['categories'].keys())}")

                if todo["body"]:
                    report_lines.append(f"- **Details**: {todo['body'][:200]}")

                report_lines.append("- **Files**:")
                for cat, files in todo["categories"].items():
                    for f in files[:5]:  # Limit to 5 files per category
                        report_lines.append(f"  - `{f}`")
                    if len(files) > 5:
                        report_lines.append(f"  - ... and {len(files) - 5} more")

                report_lines.append("")

    # Add action summary
    report_lines.extend([
        "---",
        "",
        "## Action Summary",
        "",
        "| Action | Count |",
        "|--------|-------|",
    ])

    action_counts: dict[str, int] = {}
    for todo in todos:
        action = todo["action_required"]
        action_counts[action] = action_counts.get(action, 0) + 1

    for action, count in sorted(action_counts.items()):
        report_lines.append(f"| {action} | {count} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. Review HIGH priority items first",
        "2. For `SYNC_CONTRACT` items, check if ai-dev-orchestrator has equivalent contracts",
        "3. For `REVIEW_ADR` items, determine if the ADR applies to ai-dev-orchestrator",
        "4. For `REVIEW_AND_ADOPT` items, evaluate if the innovation should be ported",
        "",
    ])

    report = "\n".join(report_lines)

    # Save to file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"SYNC_TODO_{timestamp}.md"

    output_file.write_text(report, encoding="utf-8")
    print(f"Report saved to: {output_file}")

    # Also save as JSON for programmatic access
    json_file = output_file.with_suffix(".json")
    json_file.write_text(
        json.dumps({"generated": datetime.now().isoformat(), "todos": todos}, indent=2),
        encoding="utf-8",
    )

    return report


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor engineering-tools for changes to absorb into ai-dev-orchestrator"
    )
    parser.add_argument(
        "--since",
        help="Git commit hash to start from (default: last sync point)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: .sync_todos/SYNC_TODO_<timestamp>.md)",
    )
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Update sync state to current HEAD after generating report",
    )
    parser.add_argument(
        "--show-state",
        action="store_true",
        help="Show current sync state and exit",
    )

    args = parser.parse_args()

    # Check upstream repo exists
    if not UPSTREAM_REPO.exists():
        print(f"Error: Upstream repo not found at {UPSTREAM_REPO}", file=sys.stderr)
        sys.exit(1)

    state = get_sync_state()

    if args.show_state:
        print(json.dumps(state, indent=2))
        return

    since = args.since or state.get("last_commit")
    print(f"Scanning commits since: {since or 'beginning'}")

    commits = get_commits_since(since)
    print(f"Found {len(commits)} commits")

    if commits:
        report = generate_sync_report(commits, args.output)
        print("\n" + "=" * 60)
        print(report[:2000])  # Print first 2000 chars
        if len(report) > 2000:
            print(f"\n... (truncated, see full report in .sync_todos/)")

    if args.update_state:
        current_head = run_git(["rev-parse", "HEAD"])
        state["last_commit"] = current_head
        state["last_sync"] = datetime.now().isoformat()
        save_sync_state(state)
        print(f"\nSync state updated to: {current_head[:8]}")


if __name__ == "__main__":
    main()
