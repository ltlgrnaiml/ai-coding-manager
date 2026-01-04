# SPROMPT-NNNN: [Title] — [Brief Description]

> **Type**: Super Prompt (SPROMPT)
> **Version**: 1.1.0
> **Created**: YYYY-MM-DD
> **Source Discussion**: DISC-NNNN
> **Target Model**: Large Reasoning Model (Claude Opus, GPT-4o, Gemini Ultra, etc.)
> **Estimated Tokens**: ~NNK context required
> **Expected Duration**: Single extended session (N-N hours)

---

## ⚡ SPROMPT PROTOCOL v1.1

**SPROMPT** (Super Prompt) is designed for autonomous AI execution of complex, multi-artifact development tasks.

### Protocol Rules

1. **Self-contains all context** — No external lookups required mid-execution
2. **Defines the full artifact chain** — RAG → DISC → ADR → SPEC → Contract → Plan → Code → Test → Validate
3. **Includes reasoning patterns** — Chain-of-Thought (CoT) and Tree-of-Thought (ToT) decision points
4. **Specifies verification gates** — Each phase has explicit success criteria
5. **Handles failure gracefully** — Rollback and retry strategies included
6. **🆕 Requires visual evidence** — Screenshots or interaction logs for UI work
7. **🆕 Tracks attribution** — Clearly separates AI vs human contributions
8. **🆕 Distinguishes required vs optional** — Clear must-have checklist

**Execution Mode**: Autonomous with checkpoint summaries and evidence collection

---

## 🎯 MISSION OBJECTIVE

[One paragraph describing the high-level goal]

**Success Criteria**: [Concrete, testable criteria for completion]

---

## 📋 ARTIFACT CHECKLIST (Enhancement #1: Required vs Optional)

### 🔴 REQUIRED (Must complete for passing grade)

| # | Artifact | Type | Path | Verification |
|---|----------|------|------|--------------|
| 1 | [Name] | [Type] | [Path] | [How to verify] |
| 2 | [Name] | [Type] | [Path] | [How to verify] |

### 🟡 OPTIONAL (Bonus points)

| # | Artifact | Type | Path | Notes |
|---|----------|------|------|-------|
| 1 | [Name] | [Type] | [Path] | [Why optional] |

### Completion Threshold

- **Passing**: All REQUIRED artifacts complete + Gates 1-3 pass
- **Good (B)**: Passing + 50% optional + Gates 1-5 pass
- **Excellent (A)**: All artifacts + All gates + Visual verification

---

## 📚 SECTION 1: RAG CONTEXT

### 1.1 Required Reading — Foundation Documents

```
READ_ORDER:
1. [path/to/file]     # [why read this]
2. [path/to/file]     # [why read this]
```

**After reading, summarize**:
- Key architectural decisions
- Existing patterns to follow
- Constraints to respect

### 1.2 Required Reading — Existing Codebase

```
READ_ORDER:
1. [path/to/file]     # [what to learn]
2. [path/to/file]     # [what to learn]
```

### 1.3 Reference Patterns

```
PATTERN_FILES:
- [path] — [pattern name]
- [path] — [pattern name]
```

---

## 🧠 SECTION 2: CHAIN OF THOUGHT — Problem Decomposition

### CoT-1: [Decision Name]

```
QUESTION: [Architectural question]

ANALYSIS:
├── Option A: [Name]
│   ├── Pro: [benefit]
│   └── Con: [drawback]
│
├── Option B: [Name]
│   ├── Pro: [benefit]
│   └── Con: [drawback]
│
└── DECISION: [Selected option with reasoning]
```

---

## 🌳 SECTION 3: TREE OF THOUGHT — Implementation Paths

### ToT-1: [Component/Feature]

```
APPROACHES:
├── A: [Approach name]
│   └── [Assessment]
│
├── B: [Approach name]
│   └── ✅ SELECTED — [Why]
│
└── C: [Approach name]
    └── [Assessment]

IMPLEMENTATION:
- [Key implementation detail]
- [Key implementation detail]
```

---

## 📋 SECTION 4: EXECUTION PLAN

### Phase 1: [Title]

**Goal**: [What this phase achieves]

**Tasks**:
```
[ ] 1.1 [Task description]
[ ] 1.2 [Task description]
```

**Verification Gate**:
```bash
# Command to verify
[command]
# Expected: [outcome]
```

---

## 🔧 SECTION 5: TECHNICAL SPECIFICATIONS

### 5.1 Type Definitions

```typescript
// [Description]
interface [Name] {
  [fields]
}
```

### 5.2 API Contracts

```typescript
// [Endpoint description]
interface [Request/Response] {
  [fields]
}
```

---

## ✅ SECTION 6: VERIFICATION GATES

### Gate 1: [Name] (REQUIRED)
```bash
[command]
# Expected: [outcome]
```

### Gate 2: [Name] (REQUIRED)
```bash
[command]
# Expected: [outcome]
```

---

## 📸 SECTION 7: VISUAL VERIFICATION PROTOCOL (Enhancement #2)

> **🆕 v1.1**: All UI work MUST include visual evidence

### Required Screenshots

| Gate | What to Capture | How to Verify |
|------|-----------------|---------------|
| UI-1 | [Page/component] | [Expected appearance] |
| UI-2 | [Interaction result] | [Expected behavior] |

### Verification Commands

```bash
# Start dev server
npm run dev

# Navigate to: [URL]
# Interact: [Steps]
# Capture: [What to screenshot/describe]
```

### Evidence Format

For each UI gate, provide:
```markdown
### UI-N: [Name] ✅

**URL**: [path]
**Action**: [what you did]
**Result**: [what happened]
**Evidence**: [Screenshot description or "Verified visually"]
```

---

## 🚨 SECTION 8: FAILURE HANDLING

### If [Failure Type]
1. [Step 1]
2. [Step 2]

### Rollback Strategy
```bash
git stash
# [recovery steps]
```

---

## 📊 SECTION 9: ATTRIBUTION TRACKING (Enhancement #3)

> **🆕 v1.1**: Track AI vs human contributions for accurate scoring

### At End of Execution, Report:

```markdown
## Attribution Summary

### Completed by AI (This Session)
| Artifact | Status | Notes |
|----------|--------|-------|
| [Name] | ✅ | [Any issues] |

### Requires Human Completion
| Artifact | Reason | Estimated Effort |
|----------|--------|------------------|
| [Name] | [Why not done] | [Time estimate] |

### Verification Performed
| Gate | Passed | Evidence |
|------|--------|----------|
| Gate 1 | ✅/❌ | [Evidence type] |
```

---

## 📤 SECTION 10: OUTPUT FORMAT

### Phase Completion Format

```markdown
## Phase N: [Title] — COMPLETE ✅

### Files Created/Modified:
- `path/to/file` — [description]

### Verification:
- [x] Gate N passed: [evidence]

### Issues Encountered:
- [issue] → [resolution]
```

### Final Summary Format

```markdown
# SPROMPT-NNNN Execution Complete

## Artifact Summary
| # | Artifact | Status | Attribution |
|---|----------|--------|-------------|
| 1 | [Name] | ✅/❌ | AI/Human |

## Gate Summary
| Gate | Status | Evidence |
|------|--------|----------|
| 1 | ✅/❌ | [Type] |

## Scores (Self-Assessment)
- Required Artifacts: N/N
- Optional Artifacts: N/N
- Gates Passed: N/N
- Visual Verification: ✅/❌

## Attribution
- AI Completed: N artifacts
- Human Required: N artifacts

## Known Limitations
- [limitation]

## Recommended Follow-ups
- [recommendation]
```

---

## 🎬 EXECUTION START

**You are now ready to execute this SPROMPT.**

1. Read all RAG context files first
2. Summarize key findings
3. Execute phases sequentially
4. Verify at each gate before proceeding
5. Capture visual evidence for UI work
6. Report attribution clearly

**Go.** 🚀

---

*SPROMPT Template v1.1 | Created: 2026-01-03 | Part of: AI Coding Manager (AICM)*
