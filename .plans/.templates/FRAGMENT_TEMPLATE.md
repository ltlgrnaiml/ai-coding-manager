# Fragment Execution Template

> **Purpose**: Execute a single task chunk from a Plan with proper verification.
> **Part of**: AI Coding Manager (AICM)

---

## Fragment Metadata

```yaml
fragment_id: FRAG-PLAN-XXX-MX-TX
source_plan: PLAN-XXX
milestone: MX
task: TX
status: pending  # pending | in_progress | complete | blocked
created_at: YYYY-MM-DD
completed_at: null
```

---

## Pre-Execution Checklist

Before starting ANY fragment execution:

- [ ] **Environment Detection**: `python scripts/detect_env.py`
- [ ] **Read Source Plan**: Understand full context of PLAN-XXX
- [ ] **Check Dependencies**: Verify prerequisite tasks are complete
- [ ] **Session Created**: `.sessions/SESSION_XXX_description.md` exists

---

## Task Definition

**From Plan**: `{Task description from source plan}`

**Acceptance Criteria**:
```
{Copy AC from plan}
```

**Verification Command**:
```bash
{Copy verification_command from plan}
```

---

## Implementation

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `path/to/file` | create/modify/delete | What changes |

### Code Changes

```python
# Implementation here
```

### Notes

- {Implementation notes}

---

## Post-Execution Checklist

After completing ANY fragment:

### 1. Verification Commands (REQUIRED)

```bash
# Run the task-specific verification
{verification_command from plan}

# Run platform-appropriate checks
python scripts/detect_env.py  # Check platform

# Mac Native:
pytest tests/ -v

# Win11 Docker:
./scripts/verify-changes.sh
```

### 2. Checklist

- [ ] Task-specific verification passes
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No new lint errors
- [ ] Session file updated with progress
- [ ] Plan task marked complete (if passing)

### 3. Platform-Specific Verification

**Mac (Native)**:
```bash
pytest tests/ -v
# If backend changes: Test API manually
curl -s http://localhost:8100/api/health
```

**Win11 (Docker)**:
```bash
./scripts/verify-changes.sh
# Or manual:
docker compose build backend
docker compose up -d
docker logs aidev-backend | tail -20
```

---

## Completion

### Status Update

```yaml
status: complete
completed_at: YYYY-MM-DD
verification_result: pass  # pass | fail | partial
notes: "{Any notes about completion}"
```

### If Blocked

```yaml
status: blocked
blocked_by: "{Reason or dependency}"
next_action: "{What needs to happen to unblock}"
```

---

## Quick Reference

| Platform | Verify Command | Notes |
|----------|----------------|-------|
| Mac | `pytest tests/ -v` | Native Python |
| Win11 | `./scripts/verify-changes.sh` | Docker rebuild included |

**Rule**: Always run `python scripts/detect_env.py` first to know which verification to use.

---

*Fragment Template v1.0 | Part of: AI Coding Manager (AICM)*
