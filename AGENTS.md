# Global Rules for AI Coding Assistants (Solo-Dev Edition)

> **Context**: Solo-developer, greenfield project, AI-assisted development.
> Full control over codebase. No external consumers. First-principles approach.

---

## Rule 0 — Quality Over Speed

**Take the correct architectural path, never the shortcut.**

- Prefer clean designs over quick fixes
- Avoid wrappers, shims, indirection unless truly necessary
- Leave the codebase better than you found it
- Future-you inherits today's decisions — choose debt-free solutions

**Good > Fast. Always.**

---

## Rule 1 — First-Principles Thinking

**Question every decision. Hold no legacy assumptions.**

Before implementing anything:

1. Ask: "Is this the RIGHT solution given current circumstances?"
2. Ask: "Am I carrying forward a pattern just because it existed before?"
3. Ask: "Would I design it this way if starting fresh today?"

If the answer to #2 is yes and #3 is no — redesign it.

No sacred cows. No "we've always done it this way."

---

## Rule 2 — Single Source of Truth (SSOT)

Every project must define one canonical location for:

- Architecture decisions (`.adrs/`)
- Technical specifications (`docs/specs/`)
- Contracts (`shared/contracts/`)
- Session logs (`.sessions/`)
- Open questions (`.questions/`)

**Rule:** Never duplicate definitions. Never fragment planning. One source per concern.

---

## Rule 3 — Session Identity & Continuity

**Every AI conversation = one session.**

### Session ID

- Check `.sessions/` for highest existing SESSION_XXX number
- Your session = highest + 1
- Create `.sessions/SESSION_XXX_<brief_summary>.md` as your session log

### Code Comments (when helpful)

```python
# SESSION_XXX: Reason for change
```

This enables traceability across AI sessions.

---

## Rule 4 — Before Starting Work

Every session must:

1. Read `docs/AI_CODING_GUIDE.md` (if exists)
2. Check `.sessions/` for recent session logs
3. Check `.questions/` for open issues
4. Claim session number and create session file
5. Ensure tests pass before making changes
6. Only then begin implementation

**Start informed, not blind.**

---

## Rule 5 — Behavioral Regression Protection

Define baseline outputs for critical behavior (snapshots, golden files, fixtures, deterministic logs).

**Before modifying behavior-critical logic:**

1. Run baseline tests — they must pass
2. Make changes
3. Re-run baseline tests
4. If results differ → regression → fix it

**Never modify baseline data without explicit USER approval.**

---

## Rule 6 — Breaking Changes > Fragile Compatibility

**Favor clean breaks over compatibility hacks.**

Since this is greenfield with no external consumers:

1. Rename/move the type/function directly
2. Let the compiler/linter fail
3. Fix all import sites
4. Delete legacy names immediately

**No adapters. No shims. No "temporary" re-exports. Fix the source.**

---

## Rule 7 — No Dead Code

**Remove immediately:**

- Unused functions and modules
- Commented-out code
- "Kept for reference" logic (git history exists)
- Deprecated patterns

**The repository contains only living, active code.**

---

## Rule 8 — Modular Architecture

When organizing code:

- Each module owns its own state
- Keep fields private — expose intentional APIs
- Avoid deep relative imports
- File size: < 500 lines preferred, < 1000 max
- Organize by responsibility, not convenience
- Clear inputs/outputs for every component

---

## Rule 9 — Deterministic System Design

**Every component must have:**

- Clear single responsibility
- Defined inputs (typed, validated)
- Defined outputs (typed, contracted)
- Explicit error handling
- Predictable behavior

**Upstream providers and downstream consumers must have clear expectations.**

---

## Rule 10 — Documentation is Automated

**Automate documentation generation:**

- Pydantic models → JSON Schema (auto-generated)
- FastAPI → OpenAPI spec (auto-generated)
- Docstrings → API docs (mkdocstrings)
- Commits → Changelog (git-cliff)

**Manual documentation = documentation that rots. Automate it.**

---

## Rule 11 — Code Quality Standards

All code must be:

- **Modern**: Use current language features and patterns
- **Modular**: Clear boundaries, single responsibility
- **Clean**: Readable, well-formatted, consistent style
- **Efficient**: No premature optimization, but no waste
- **Type-safe**: Full type hints (Python), typed props (TypeScript)
- **Documented**: Google-style docstrings on all public functions

---

## Rule 12 — Ask Questions

**If ANY of the following occur:**

- Requirements conflict
- Plans seem incomplete

Create a question file under `.questions/` and ask the USER.

**Never guess on architectural decisions.**

---

## Rule 13 — Maximize Context Window

While context is fresh:

- Complete as much aligned work as possible
- Don't stop mid-task if more progress is obvious
- Minimize context re-initialization for next session

If a task grows too large: split into sub-tasks and document in session file.

---

## Rule 14 — Before Finishing Session

Every session must:

1. Update session file with progress
2. Ensure project builds
3. Ensure all tests pass
4. **Run post-change verification** (see Rule 16)
5. Document remaining work, blockers, or next steps
6. Write handoff notes for next session

### Session Handoff Checklist

- [ ] Project builds cleanly
- [ ] All tests pass
- [ ] Regression tests pass (if applicable)
- [ ] **Post-change verification passes** (`./scripts/verify-changes.sh`)
- [ ] Session file updated
- [ ] Remaining TODOs documented

---

## Rule 15 — TODO Tracking

Any incomplete work must be tracked:

### In Code

```python
# TODO(SESSIONS_XXX): Description of what's missing
```

### In Global TODO List

Add to project TODO file with file path + description.

**Future sessions must know what remains.**

---

## Rule 16 — Post-Change Verification (CRITICAL)

**After ANY code changes, run the verification checklist.**

This prevents the most common failures:
- `.env` not loaded (API keys missing)
- Databases not initialized
- Docker containers running stale code

### Quick Check

```bash
./scripts/verify-changes.sh
```

### What It Verifies

1. **Environment**: `.env` exists and has real API keys
2. **Docker**: Containers rebuilt and running
3. **Databases**: Knowledge, P2RE, Memory DBs initialized
4. **Health**: Backend and frontend endpoints responding
5. **Files**: Database files exist on disk

### When to Run

- After ANY Python/TypeScript code change
- After modifying `.env` or `docker-compose.yml`
- After pulling from git
- Before marking a task complete
- Before session handoff

### Full Documentation

See `POST_CHANGE_CHECKLIST.md` for detailed failure recovery procedures.

---

## Solo-Dev Principles Summary

1. **First-Principles**: Question everything, no legacy baggage
2. **Full Control**: Break things freely, fix them completely
3. **AI-Assisted**: Optimize for AI comprehension and continuity
4. **Automate Everything**: Documentation, tests, validation
5. **Deterministic Design**: Clear contracts, predictable behavior
6. **Quality First**: Modern, clean, efficient, industry-leading
