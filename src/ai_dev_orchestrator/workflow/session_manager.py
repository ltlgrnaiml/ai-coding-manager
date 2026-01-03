"""Session Manager - Track AI session continuity.

Sessions enable handoff between AI conversations by tracking:
- What was accomplished
- What remains to be done
- Important context for continuation
"""

import re
from datetime import datetime
from pathlib import Path


SESSIONS_DIR = Path(".sessions")

SESSION_TEMPLATE = '''# SESSION_{num:03d}: {title}

> **Started**: {started_at}
> **Status**: in_progress

---

## Objective

{objective}

---

## Progress

- [ ] Starting work...

---

## Key Decisions

*None yet.*

---

## Blockers

*None.*

---

## Handoff Notes

*To be filled at session end.*

---

## Next Steps

- [ ] TBD
'''


def get_next_session_id() -> int:
    """Get the next available session number.
    
    Returns:
        Next session number.
    """
    SESSIONS_DIR.mkdir(exist_ok=True)
    
    existing = list(SESSIONS_DIR.glob("SESSION_*.md"))
    if not existing:
        return 1
    
    numbers = []
    for f in existing:
        match = re.search(r'SESSION_(\d+)', f.stem)
        if match:
            numbers.append(int(match.group(1)))
    
    return max(numbers) + 1 if numbers else 1


def create_session(
    title: str,
    objective: str = "",
) -> Path:
    """Create a new session log.
    
    Args:
        title: Brief session title/summary.
        objective: What this session aims to accomplish.
        
    Returns:
        Path to created session file.
    """
    session_num = get_next_session_id()
    
    content = SESSION_TEMPLATE.format(
        num=session_num,
        title=title,
        started_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        objective=objective or "TBD",
    )
    
    # Create filename
    title_slug = re.sub(r'[^a-zA-Z0-9]+', '_', title)[:40]
    filename = f"SESSION_{session_num:03d}_{title_slug}.md"
    path = SESSIONS_DIR / filename
    
    SESSIONS_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return path


def get_current_session() -> dict | None:
    """Get the most recent session.
    
    Returns:
        Session info dict or None if no sessions exist.
    """
    SESSIONS_DIR.mkdir(exist_ok=True)
    
    sessions = sorted(SESSIONS_DIR.glob("SESSION_*.md"), reverse=True)
    if not sessions:
        return None
    
    latest = sessions[0]
    match = re.search(r'SESSION_(\d+)_(.+)\.md', latest.name)
    
    if match:
        with open(latest, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "number": int(match.group(1)),
            "title": match.group(2).replace('_', ' '),
            "path": str(latest),
            "content": content,
        }
    
    return None


def list_sessions(limit: int = 10) -> list[dict]:
    """List recent sessions.
    
    Args:
        limit: Maximum number of sessions to return.
        
    Returns:
        List of session summaries, most recent first.
    """
    SESSIONS_DIR.mkdir(exist_ok=True)
    
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("SESSION_*.md"), reverse=True)[:limit]:
        match = re.search(r'SESSION_(\d+)_(.+)\.md', path.name)
        if match:
            sessions.append({
                "number": int(match.group(1)),
                "title": match.group(2).replace('_', ' '),
                "path": str(path),
            })
    
    return sessions
