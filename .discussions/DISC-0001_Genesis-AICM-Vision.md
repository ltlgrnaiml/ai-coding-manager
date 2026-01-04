# DISC-0001: Genesis — AI Coding Manager (AICM) Vision and Foundation

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md` (this session's log)
> **Session**: SESSION_017

---

## Problem Statement

Before building more artifacts, we must answer: **What IS AICM, and what makes a project compatible with it?**

---

## Context

### Background

The AICM repository had accumulated ~40 DISCs, ~10 ADRs, and various contracts without a clear foundational answer to:

1. What IS the AICM product?
2. How does it use UAM, AIKH, P2RE?
3. Why is it special?
4. What makes a project AICM-compatible?

### Trigger

User directive: *"Ok time to get creative, become the full embodiment of our SOLO-DEV ETHOS... I want to archive all DISCs, all ADRs, all UAM related artifacts except our chat_logs."*

---

## The Answer: What IS AICM?

**The AI Coding Manager (AICM) is a methodology-as-software** — a system that embodies AI-human collaborative development while being built BY that methodology.

### The Core Loop

```
Chat Logs → Discussions → Decisions → Specifications → Code → Traces → Knowledge → Next Chat
```

### The Four Pillars

1. **UAM** — Unified Artifact Model (deterministic traceability)
2. **AIKH** — AI Knowledge Hub (persistent cross-project knowledge)
3. **P2RE** — Prompt-to-Response Evaluator (observability)
4. **Tap-In Protocol** — Zero ramp-up AI session continuity

### Why Special

- **Self-documenting**: Built WITH the system it defines
- **Self-informing**: Projects contribute knowledge back
- **Self-propagating**: New projects inherit the framework
- **First-principles native**: No legacy assumptions

---

## Decision

**Archive all pre-Genesis artifacts and restart with clarity.**

- All DISCs, ADRs, contracts moved to `.archive/v0/`
- Preserved: `.chat_logs/` (source of truth), `.sessions/` (AI continuity)
- Created: `VISION.md` as the new foundation

### Standardized Artifact Naming Convention

All artifacts now use **4-digit numbering** for consistency and scalability:

| Artifact | Format | Example |
|----------|--------|---------|
| Discussion | `DISC-NNNN` | `DISC-0001` |
| ADR | `ADR-NNNN` | `ADR-0001` |
| SPEC | `SPEC-NNNN` | `SPEC-0001` |
| PLAN | `PLAN-NNNN` | `PLAN-0001` |
| Session | `SESSION_NNNN` | `SESSION_0017` |

### Session ↔ Chat Log Alignment

**Principle**: Sessions (AI-initiated) and Chat Logs (user-initiated) should be cross-referenced when possible.

| Source | Naming | Timestamp Source |
|--------|--------|------------------|
| **Chat Logs** | Title from last message chain (arbitrary) | File save date/time |
| **Sessions** | `SESSION_NNNN_{summary}.md` | Created date in content |

**Alignment Strategy**:
- Session logs reference source chat by filename
- Timestamps verified via file metadata when available
- Gentle fallback when alignment not possible (no hard failures)
- Chat log content used to infer actual conversation dates

**Note**: Session numbering may need repo-specific adjustment in future as sessions span multiple projects.

---

## Child Discussions

| DISC | Title | Type | Status |
|------|-------|------|--------|
| DISC-0002 | The Rainstorm ⛈️ | Workflow | `active` 🔴 CRITICAL |
| DISC-0003 | UAM — Unified Artifact Model | Umbrella | `active` |

---

## Resulting Artifacts

| Type | ID | Title | Status |
|------|-----|-------|--------|
| Vision | `VISION.md` | AICM Vision Statement | `active` |
| Archive | `.archive/v0/` | Pre-Genesis artifacts | `preserved` |

---

## Next Steps

1. Define minimum AICM-compatible project requirements (from VISION.md)
2. Create `aicm init` scaffold script
3. Prove the loop by building AICM with AICM

---

## Resolution

**Resolution Date**: 2026-01-03

**Outcome**: Genesis established. VISION.md created. Pre-Genesis artifacts archived. The loop is now closed — every artifact traces to a chat log.
