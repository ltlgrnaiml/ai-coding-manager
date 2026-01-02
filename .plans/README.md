# Plans Directory

Implementation plans for AI-assisted development.

## What are Plans?

Plans are **T4 artifacts** in the 6-tier workflow. They contain:

- **Milestones**: Major deliverables
- **Tasks**: Atomic units of work with verification commands
- **Acceptance Criteria**: What must be true for completion

## Plan Granularity

Plans support three granularity levels:

| Level | Target Models | Key Fields |
|-------|---------------|------------|
| L1 | Premium (Opus, Sonnet) | `context` |
| L2 | Mid-tier (Gemini Pro) | + `constraints`, `existing_patterns` |
| L3 | Budget (Haiku, Flash) | + `steps` with code snippets |

## Creating a Plan

```bash
python scripts/new_plan.py "My Feature Name"
```

## Plan Structure

```json
{
  "id": "PLAN-001",
  "title": "Feature Implementation Plan",
  "granularity": "L1",
  "milestones": [
    {
      "id": "M1",
      "name": "Backend Foundation",
      "tasks": [
        {
          "id": "T-M1-01",
          "description": "Create data models",
          "verification_command": "python -c 'from myapp.models import User'",
          "context": ["ARCHITECTURE: Use Pydantic BaseModel"]
        }
      ]
    }
  ]
}
```

## Verification First

**CRITICAL**: Every task must have a `verification_command` that proves completion.

```text
1. IMPLEMENT the task
2. RUN the verification command
3. DOCUMENT evidence
4. MARK complete
```
