# Sessions Directory

Session logs for AI-assisted development continuity.

## Purpose

Sessions track work across AI assistant conversations. Each session creates a log file documenting:

- What was accomplished
- What remains to be done
- Blockers encountered
- Handoff notes for the next session

## Session Naming

```
SESSION_XXX_<brief_summary>.md
```

Example: `SESSION_001_Initial-Setup.md`

## Session Protocol

### Starting a Session

1. Check this directory for the highest `SESSION_XXX` number
2. Your session = highest + 1
3. Create your session file
4. Read recent session logs for context

### During a Session

- Update your session file with progress
- Note any blockers or questions
- Keep track of files modified

### Ending a Session

1. Update session file with final status
2. Document remaining work
3. Add handoff notes for next session
4. Ensure project builds and tests pass

## Session File Template

```markdown
# SESSION_XXX: Brief Summary

**Date**: YYYY-MM-DD
**Plan**: PLAN-XXX (if applicable)
**Status**: In Progress | Completed | Blocked

## Objectives

- [ ] Task 1
- [ ] Task 2

## Progress

### Completed

- Description of completed work

### Remaining

- What still needs to be done

## Blockers

- Any issues preventing progress

## Handoff Notes

Notes for the next session...

## Files Modified

- `path/to/file.py`
```
