# AI Dev Orchestrator - AI Coding Guide

> **Windsurf Auto-Discovery**: This file applies globally to all files in the repository.

---

## Project Philosophy

This is an **AI-assisted development framework** that helps you get consistent, high-quality code from AI coding assistants.

| Principle | Rule |
|-----------|------|
| **Quality > Speed** | Take the correct architectural path, never the shortcut |
| **First-Principles** | Question every decision. No legacy assumptions. |
| **Plan Granularity** | Match plan detail (L1/L2/L3) to model capability |
| **Verify Everything** | Never mark a task complete without running verification |

---

## Plan Granularity Levels

### L1: Standard (Premium Models)

For Opus, Sonnet, GPT-5.2 - models that handle ambiguity well.

```json
"context": [
  "ARCHITECTURE: Functional style, no classes",
  "FILE: Create services/my_service.py",
  "ENUM: Status: pending, active, completed"
]
```

### L2: Enhanced (Mid-Tier Models)

For Gemini Pro, GPT-5.1 - need explicit constraints.

```json
"context": [...],
"constraints": [
  "DO NOT use class-based architecture",
  "MUST place tests in tests/unit/"
],
"existing_patterns": [
  "Follow pattern in services/user_service.py"
]
```

### L3: Procedural (Budget Models)

For Haiku, Flash, Grok - need step-by-step instructions.

```json
"context": [...],
"constraints": [...],
"steps": [
  {
    "step_number": 1,
    "instruction": "Create the file services/my_service.py",
    "code_snippet": "# Contents here...",
    "verification_hint": "test -f services/my_service.py"
  }
]
```

---

## 6-Tier Workflow

| Tier | Artifact | Purpose |
|------|----------|---------|
| T0 | `.discussions/DISC-XXX.md` | Capture design conversation |
| T1 | `.adrs/ADR-XXXX.json` | Record WHY decisions were made |
| T2 | `docs/specs/SPEC-XXX.json` | Define WHAT to build |
| T3 | `contracts/*.py` | Define data shapes (Pydantic) |
| T4 | `.plans/PLAN-XXX.json` | Milestones, tasks, acceptance criteria |
| T5 | Fragment execution | One verifiable unit of work |

---

## Session Discipline

Every AI session must:

1. Check `.sessions/` for recent session logs
2. Claim next session number and create session file
3. Read the active plan in `.plans/`
4. Ensure tests pass before making changes
5. Update session file with progress
6. Document remaining work before ending

---

## Code Patterns

### Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Files | `{domain}_{action}.py` | `plan_loader.py` |
| Functions | `{verb}_{noun}()` | `load_plan()` |
| Classes | `PascalCase` | `PlanSchema` |

### Required Docstring Format (Google Style)

```python
def compute_task_id(inputs: dict[str, Any]) -> str:
    """Compute deterministic task ID from inputs.

    Args:
        inputs: Dictionary of task inputs to hash.

    Returns:
        8-character SHA-256 hash prefix.

    Raises:
        ValueError: If inputs is empty.
    """
```

---

## Verification First

**CRITICAL**: Never mark a task complete without verification.

```text
1. IMPLEMENT one task
2. VERIFY with command (grep, pytest, import check)
3. DOCUMENT evidence in plan
4. ONLY THEN mark complete
```

---

## Quick Commands

| Command | Purpose |
|---------|---------|
| `pip install -e .` | Install package |
| `ruff check .` | Run linting |
| `ruff format .` | Auto-format code |
| `pytest tests/ -v` | Run all tests |

---

*This AGENTS.md follows Windsurf's hierarchical pattern.*
