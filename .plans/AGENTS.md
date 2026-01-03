# Plans - AI Agent Instructions

<!-- WINDSURF_SPECIFIC: This file contains Windsurf Cascade-specific instructions. -->

> **Applies to**: All files in `.plans/` directory
> **ADR Reference**: ADR-0001 (AI Development Workflow)

---

## Purpose

This directory contains **Plan** artifacts (Tier 4 of the AI Development Workflow).
Plans break down implementation work into milestones, tasks, and acceptance criteria.

---

## When to Create a Plan

**ALWAYS** create a plan when:

1. Work has **more than 3 tasks**
2. Work spans **multiple sessions**
3. Implementing from a **SPEC** or **Discussion**

**MAY SKIP** plan for:

1. Single-file bug fixes
2. Documentation updates
3. Simple refactoring (< 3 files)

---

## Fragment-Based Execution

### The Golden Rule

**NEVER mark a task complete without running its verification command.**

### Execution Flow

For each task:

```text
1. READ the task description and verification command
2. IMPLEMENT the change
3. RUN the verification command
4. IF passes → Mark [x] and log evidence
5. IF fails → Debug, fix, re-verify
6. ONLY THEN proceed to next task
```

### Verification Evidence

Log verification evidence in the session file:

```markdown
**Verification Evidence**:
$ grep "from module import Class" path/to/files/
path/to/file.py:from module import Class
✓ Import verified

$ pytest tests/test_module.py -v
======================== 3 passed in 0.42s ========================
✓ Tests pass
```

---

## Plan Granularity Levels

### L1: Standard (Premium Models)

**Target Models**: Claude Opus, Claude Sonnet 3.5+, GPT-4o, Grok-4

**Task Schema**: `id`, `description`, `verification_command`, `status`

**Execution**: Models infer implementation from context.

### L2: Enhanced (Mid-Tier Models)

**Target Models**: Claude Sonnet 3.5, GPT-4o-mini, Gemini 1.5 Flash, Grok-2

**Additional Fields**: `context[]`, `hints[]`, `constraints[]`, `references[]`

**When to use L2**:
- Task involves multiple files
- Task has complex dependencies
- Previous similar task failed

### L3: Procedural (Budget Models)

**Target Models**: Claude Haiku, Gemini Flash 8B, Grok-fast

**Additional Fields**: `steps[]` with step-by-step instructions

**Execution**: STOP and escalate on failure (no log_and_continue).

---

## Session Management

### At Session Start

1. Read `.plans/INDEX.md` for active plans
2. Read the active plan file
3. Check Progress Summary for current state
4. Announce what you'll work on

### During Session

1. Work one task at a time
2. Update task checkbox when verified complete
3. Note blockers immediately

### At Session End

1. Update Progress Summary
2. Write Handoff Notes for next session
3. List files modified

---

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Marking task done without verification | Run verification command first |
| Working multiple tasks in parallel | Complete one task fully before next |
| Skipping blockers | Stop, log, ask USER |
| Breadth over depth | Depth first: complete one milestone fully |

---

## Quick Reference: Task Verification Commands

```bash
# Verify import exists
grep "from module import Class" path/to/files/

# Verify method is called
grep "method_name(" path/to/files/

# Verify tests pass
pytest tests/specific_test.py -v

# Verify no lint errors
ruff check path/to/file.py

# Verify module imports
python -c "from module import Class; print('OK')"
```
