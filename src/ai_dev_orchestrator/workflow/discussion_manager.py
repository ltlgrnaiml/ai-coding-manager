"""Discussion Manager - Create and manage design discussions.

Discussions capture AI ↔ Human design conversations before
formalizing into ADRs, SPECs, and Plans.
"""

import re
from datetime import datetime
from pathlib import Path


DISCUSSIONS_DIR = Path(".discussions")

DISCUSSION_TEMPLATE = '''# {title}

> **ID**: {id}
> **Status**: draft
> **Created**: {created_at}

---

## Summary

{summary}

---

## Context

{context}

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | TBD | High |

---

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | TBD | Medium |

---

## Open Questions

- [ ] TBD

---

## Decision

*To be determined after discussion.*

---

## Next Steps

- [ ] Define requirements
- [ ] Create ADR if architectural decision needed
- [ ] Create SPEC for implementation details
- [ ] Create PLAN for execution
'''


def get_next_discussion_id() -> str:
    """Get the next available discussion ID.
    
    Returns:
        Next discussion ID in format DISC-XXX.
    """
    DISCUSSIONS_DIR.mkdir(exist_ok=True)
    
    existing = list(DISCUSSIONS_DIR.glob("DISC-*.md"))
    if not existing:
        return "DISC-001"
    
    numbers = []
    for f in existing:
        match = re.search(r'DISC-(\d+)', f.stem)
        if match:
            numbers.append(int(match.group(1)))
    
    next_num = max(numbers) + 1 if numbers else 1
    return f"DISC-{next_num:03d}"


def create_discussion(
    title: str,
    summary: str = "",
    context: str = "",
) -> Path:
    """Create a new discussion.
    
    Args:
        title: Discussion title.
        summary: Brief summary of the discussion topic.
        context: Background context.
        
    Returns:
        Path to created discussion file.
    """
    disc_id = get_next_discussion_id()
    
    content = DISCUSSION_TEMPLATE.format(
        id=disc_id,
        title=title,
        created_at=datetime.utcnow().strftime("%Y-%m-%d"),
        summary=summary or "TBD",
        context=context or "TBD",
    )
    
    # Create filename
    title_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title)[:40]
    filename = f"{disc_id}_{title_slug}.md"
    path = DISCUSSIONS_DIR / filename
    
    DISCUSSIONS_DIR.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return path


def load_discussion(disc_id: str) -> str | None:
    """Load a discussion by ID.
    
    Args:
        disc_id: Discussion ID (e.g., DISC-001).
        
    Returns:
        Discussion content or None if not found.
    """
    for path in DISCUSSIONS_DIR.glob(f"{disc_id}*.md"):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def save_discussion(disc_id: str, content: str) -> Path | None:
    """Save discussion content.
    
    Args:
        disc_id: Discussion ID.
        content: Updated content.
        
    Returns:
        Path to saved file or None if not found.
    """
    for path in DISCUSSIONS_DIR.glob(f"{disc_id}*.md"):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
    return None


def list_discussions() -> list[dict]:
    """List all discussions.
    
    Returns:
        List of discussion summaries.
    """
    DISCUSSIONS_DIR.mkdir(exist_ok=True)
    
    discussions = []
    for path in sorted(DISCUSSIONS_DIR.glob("DISC-*.md")):
        match = re.search(r'(DISC-\d+)_(.+)\.md', path.name)
        if match:
            discussions.append({
                "id": match.group(1),
                "title": match.group(2).replace('-', ' '),
                "path": str(path),
            })
    
    return discussions
