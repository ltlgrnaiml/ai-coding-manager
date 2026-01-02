# DISC-012: Plan Artifact Structure & Lifecycle

> **Status**: `resolved` (with addendum)
> **Created**: 2025-12-31
> **Updated**: 2025-12-31
> **Author**: Mycahya Eggleston
> **AI Session**: SESSION_021
> **Depends On**: None
> **Blocks**: None
> **Dependency Level**: L0
>
> **Parent Discussion**: DISC-011 (Umbrella: Unified Artifact Model)

---

## Problem Statement

The `.plans/` folder has inconsistent formats (JSON vs Markdown), empty template directories, and L3 chunking that was designed but never implemented. ADR-0043 defined PLAN structure without a source discussion, violating the Primary Chain Model.

---

## Summary

Define the canonical structure, format, and lifecycle for PLAN artifacts within the Unified Artifact Model. This includes resolving format inconsistencies, defining L1/L2/L3 granularity templates, and establishing clear lifecycle states and transitions.

---

## Context

### Background

ADR-0043 defined a 6-tier workflow with PLANs at T4, including three granularity levels:
- **L1 (Standard)**: Context + verification commands for premium models
- **L2 (Enhanced)**: L1 + constraints, hints, references for mid-tier models
- **L3 (Procedural)**: L2 + step-by-step instructions with code snippets for budget models

However, the implementation is inconsistent:

| Issue | Evidence |
|-------|----------|
| **Format mismatch** | PLAN-001 is JSON, PLAN-002 is Markdown |
| **Empty templates** | `.plans/.templates/` has 0 items |
| **Empty L3 folder** | `.plans/L3/` has 0 items despite documentation |
| **No source DISC** | ADR-0043 has no `source_discussion` field |

### Trigger

User observed during DISC-011 (UAM) discussion that the `.plans/` folder is "a complete mess" and asked to investigate what existing ADRs/DISCs say about PLANs.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Define ONE canonical format for PLAN files (JSON or Markdown, not both)
- [ ] **FR-2**: Create L1, L2, L3 templates in `.plans/.templates/`
- [ ] **FR-3**: Define PLAN lifecycle states (draft, active, completed, blocked, superseded)
- [ ] **FR-4**: Define state transition rules and gates
- [ ] **FR-5**: Define PLAN → Session relationship (how PLANs spawn SESSION files)
- [ ] **FR-6**: Define PLAN quality rubric for scoring

### Non-Functional Requirements

- [ ] **NFR-1**: Templates must be AI-parseable with clear section markers
- [ ] **NFR-2**: L3 chunking must work within 800-line context windows
- [ ] **NFR-3**: PLAN validation script must exist and be runnable

---

## Scope

### In Scope

- PLAN file format and schema
- PLAN lifecycle states and transitions
- L1/L2/L3 granularity definitions and templates
- PLAN quality rubric
- Relationship to SESSION files

### Out of Scope

- DevTools UI for PLAN management (covered by ADR-0045)
- CI validation scripts (implementation detail, not design)
- Migration of existing PLAN-001 and PLAN-002 (execution task)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should L3 be the default granularity? | `answered` | **YES** - L3 by default, UX selector for L1/L2 (higher cost warning) |
| Q-2 | Should non-conforming files be deprecated? | `answered` | **YES** - Expunge or refactor ALL non-conforming files, no orphans |
| Q-3 | How does PLAN status sync with milestone completion? | `answered` | **AUTO-SYNC** - Automate everything possible for docs |
| Q-4 | Should PLAN have a quality rubric? | `answered` | **YES** - "Everything Graded" is a CORE tenet (add to ADR-0048) |

---

## Options Considered

### Option A: JSON-Only Format

**Pros**:
- Schema validation via Pydantic
- Machine-readable for DevTools UI
- Consistent with ADR-0043 specification

**Cons**:
- Less human-readable
- Harder to edit manually
- Verbose for simple plans

### Option B: Markdown-Only Format

**Pros**:
- Human-readable and editable
- GitHub renders nicely
- Familiar to developers

**Cons**:
- No schema validation
- Harder to parse programmatically
- Inconsistent structure across authors

### Option C: Hybrid (JSON schema + Markdown EXECUTION.md)

**Pros**:
- JSON for machine-readable schema and status tracking
- Markdown EXECUTION.md for human-readable prompts and instructions
- Best of both worlds

**Cons**:
- Two files to maintain
- Sync issues between JSON and Markdown

---

## Decision

**Selected Option**: **Option D: L3-First with Auto-Sync**

**Rationale**: 
1. EXP-001 proved L3 reduces stochastic variation by 50%+ and enables budget models to match premium quality
2. L3-first maximizes cost-effectiveness (Haiku + L3 = sweet spot)
3. Auto-sync reduces manual documentation overhead ("documenting how we document")
4. Universal grading ensures consistent quality across all artifacts

**Key Decisions**:
- **L3 Default**: All new PLANs use L3 granularity by default
- **UX Selector**: DevTools UI shows granularity picker with cost implications
- **Auto-Sync**: INDEX.json status auto-updates from chunk completion
- **Everything Graded**: Quality rubric mandatory for ALL artifacts (CORE tenet)
- **No Orphans**: All non-conforming files migrated or removed

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status | Skipped Tiers |
|---------------|----|-------|--------|---------------|
| ADR Update | ADR-0048 | Add "Everything Graded" CORE tenet | `pending` | - |
| Migration List | See below | Non-conforming files to review | `active` | - |
| SPEC | SPEC-TBD | PLAN Auto-Sync Behavior | `pending` | - |

### Non-Conforming Files (Migration Required)

| File | Issue | Action |
|------|-------|--------|
| `.plans/PLAN-001_DevTools-Workflow-Manager.md` | Empty file (0 bytes) | **DELETE** |
| `.plans/PLAN-002_Knowledge-Archive-Implementation.md` | Root-level Markdown, should be L3 JSON | **MIGRATE to L3 structure** |

> **Note**: PLAN-001 and PLAN-002 already have L3 chunks in `.plans/L3/`. The root-level files are redundant or non-conforming.

---

## Conversation Log

### 2025-12-31 - SESSION_021

**Topics Discussed**:
- Identified `.plans/` folder inconsistencies during DISC-011 umbrella conversion
- User asked to investigate PLAN structure as child discussion
- Found ADR-0043 lacks source_discussion (violates UAM Primary Chain)
- **CORRECTION**: Templates and L3 structure DO exist and are well-organized
- Reviewed EXP-001 findings: L3 reduces variation 50%+, budget models match premium

**Decisions Made**:
- Q-1: L3 by default, UX selector for alternatives with cost warning
- Q-2: Expunge/refactor all non-conforming files, no orphans
- Q-3: Auto-sync INDEX.json from chunk completion
- Q-4: "Everything Graded" added as CORE tenet to ADR-0048

---

## Resolution

**Resolution Date**: 2025-12-31
**Resolution Type**: `design_complete`
**Outcome**: L3-first approach adopted with auto-sync and universal grading. Migration list created for non-conforming files.

---

## Quality Score

**Status**: `COMPLETE` - Discussion held, decisions recorded

---

## Addendum: PLAN Management Details (SESSION_021 Continued)

### Additional Questions Answered

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-A1 | Where should master PLAN file live? | `answered` | **Inside `L3/PLAN-XXX/`** - no root-level files |
| Q-A2 | What happens to completed PLANs? | `answered` | **Archive to `_archive/`** - NEVER delete |
| Q-A3 | How to handle mid-dev adjustments? | `answered` | **Amendment pattern with guardrails** - see below |

---

### DISC Flexibility Philosophy

**Decision**: DISCs use **Structured Flexibility**

```text
DISC Structure:
├── HEADER (STRICT)       # Status, dates, dependencies - machine-readable
├── PROBLEM (STRICT)      # Clear problem_statement required
├── DISCUSSION (FLEXIBLE) # Conversation log, exploration, tangents OK
├── DECISION (STRICT)     # Clear outcome required before resolution
└── ARTIFACTS (STRICT)    # What was created as result
```

**Rationale**: DISCs are records of back-and-forth exchange/progression. Forcing rigid format everywhere loses valuable context. But key sections (header, problem, decision, artifacts) must be strict for machine-readability and quality scoring.

---

### Amendment Pattern with Guardrails

#### Amendment Types

| Type | Use When | Audit Trail |
|------|----------|-------------|
| `scope_expansion` | Need more milestones | List milestones added + rationale |
| `scope_reduction` | Scope cut | List milestones removed + rationale |
| `reorder` | Priority changed | New order + rationale |
| `split` | Milestone too big | Original → split milestones |
| `merge` | Milestones too granular | Merged milestones → new |

#### Amendment Validation Checklist (REQUIRED)

Before approving ANY amendment, must answer:

```markdown
## Amendment Validation
- [ ] Does this relate to the ORIGINAL DISC scope? (If no → new DISC)
- [ ] Does this introduce NEW architectural decisions? (If yes → need ADR)
- [ ] Does this require NEW data contracts? (If yes → need Contract)
- [ ] Does this change SPEC'd behavior? (If yes → need SPEC update)
- [ ] Is total scope expansion <30%? (If no → consider new PLAN)
```

**Key Rule**: If ANY validation checkbox fails, amendment is REJECTED and proper workflow is triggered.

#### Amendment Escalation Rules

| Amendment Type | Guardrail | Escalation Trigger |
|----------------|-----------|-------------------|
| **Add 1-3 milestones** | OK if related to original DISC scope | If unrelated → new DISC |
| **Add 4+ milestones** | PAUSE - review scope | Likely needs new DISC |
| **Architectural change** | NOT allowed via amendment | MUST create ADR |
| **New data shape** | NOT allowed via amendment | MUST create Contract |
| **Change to validated behavior** | NOT allowed via amendment | MUST update SPEC |

#### Amendment Schema

```json
{
  "amendment_id": "A1",
  "date": "2025-12-31",
  "session": "SESSION_021",
  "type": "scope_expansion",
  "description": "Added M13-M14 for quality scoring integration",
  "milestones_affected": {
    "added": ["M13", "M14"],
    "removed": [],
    "modified": []
  },
  "validation_checklist": {
    "relates_to_original_scope": true,
    "introduces_architectural_change": false,
    "requires_new_contracts": false,
    "changes_spec_behavior": false,
    "scope_expansion_under_30_percent": true
  },
  "rationale": "Score provenance feature emerged from DISC-013"
}
```

---

### Complete PLAN Folder Structure

#### Root Structure

```text
.plans/
├── .templates/             # L1, L2, L3 templates
│   ├── PLAN_TEMPLATE_L1.json
│   ├── PLAN_TEMPLATE_L2.json
│   ├── PLAN_TEMPLATE_L3.json
│   ├── EXECUTION_L1.md
│   ├── EXECUTION_L2.md
│   └── EXECUTION_L3.md
├── L1/                     # Active L1 plans
│   └── PLAN-XXX/
│       ├── INDEX.json
│       ├── EXECUTION.md
│       └── PLAN-XXX_L1.json
├── L2/                     # Active L2 plans
│   └── PLAN-XXX/
│       ├── INDEX.json
│       ├── EXECUTION.md
│       └── PLAN-XXX_L2.json
├── L3/                     # Active L3 plans (DEFAULT)
│   └── PLAN-XXX/
│       ├── INDEX.json          # Master metadata + amendments[]
│       ├── EXECUTION.md        # Human-readable session log
│       └── PLAN-XXX_L3_M*.json # Milestone chunks
├── _archive/               # Completed plans (NEVER deleted)
│   └── PLAN-001/
├── INDEX.md                # Active plan index
├── AGENTS.md               # AI instructions
└── README.md               # Human documentation
```

**Rule**: NO root-level PLAN files. Everything lives in `L{1,2,3}/PLAN-XXX/` folders.

---

### Schema Definitions

#### INDEX.json (Universal - All Levels)

```json
{
  "$schema": "plan_index_schema.json",
  "__version__": "2025.12.01",
  "plan_id": "PLAN-001",
  "title": "DevTools Workflow Manager",
  "granularity": "L3",
  "status": "active",
  "source_references": ["DISC-001", "ADR-0045"],
  "created": "2025-12-28",
  "updated": "2025-12-31",
  
  "milestones": {
    "total": 12,
    "completed": 10,
    "current": "M11"
  },
  
  "amendments": [],
  
  "execution_history": [
    {
      "session": "SESSION_015",
      "model": "claude-sonnet-4",
      "milestones_completed": ["M01", "M02"],
      "date": "2025-12-28"
    }
  ],
  
  "acceptance_criteria": {
    "mvp": [],
    "full": []
  },
  
  "score_history": []
}
```

#### L3 Milestone Chunk Schema

```json
{
  "$schema": "plan_l3_chunk_schema.json",
  "chunk_id": "PLAN-001_L3_M01",
  "milestone": "M01",
  "title": "Project Setup",
  "status": "completed",
  
  "context": [
    "FILE: gateway/services/devtools_service.py",
    "ARCHITECTURE: DevTools uses service layer pattern"
  ],
  
  "tasks": [
    {
      "id": "T01",
      "description": "Create devtools route file",
      "status": "completed",
      "verification_hint": "grep 'devtools' gateway/routes/__init__.py"
    }
  ],
  
  "hints": ["Use existing route patterns from knowledge.py"],
  "constraints": ["DO NOT modify existing routes", "MUST use Pydantic models"],
  
  "acceptance_criteria": [
    "AC-M01-1: Route file exists and is registered"
  ]
}
```

#### L2 Plan Schema (Single File with Enhanced Context)

```json
{
  "$schema": "plan_l2_schema.json",
  "plan_id": "PLAN-XXX",
  "granularity": "L2",
  
  "milestones": [
    {
      "id": "M01",
      "title": "Project Setup",
      "tasks": [],
      "context": [],
      "hints": [],
      "constraints": []
    }
  ]
}
```

#### L1 Plan Schema (Minimal for Premium Models)

```json
{
  "$schema": "plan_l1_schema.json",
  "plan_id": "PLAN-XXX",
  "granularity": "L1",
  
  "milestones": [
    {
      "id": "M01",
      "title": "Project Setup",
      "tasks": []
    }
  ]
}
```

---

### PLAN Validation Rules

| Rule | Severity | Trigger |
|------|----------|--------|
| Missing `source_references` | **ERROR** | Blocks CI |
| Missing INDEX.json | **ERROR** | Blocks CI |
| Amendment without validation_checklist | **ERROR** | Blocks CI |
| Amendment validation_checklist has `false` | **ERROR** | Blocks CI - escalate |
| Root-level PLAN file (not in L{1,2,3}/) | **ERROR** | Blocks CI |
| Milestone without acceptance_criteria | **WARNING** | Report only |
| L3 chunk >800 lines | **WARNING** | Report only |
| No EXECUTION.md | **WARNING** | Report only |

---

### PLAN Quality Rubric

| Criterion | Max Points | Weight | Description |
|-----------|------------|--------|-------------|
| **source_references** | 4 | 1.5 | Links to DISC/ADR that spawned this PLAN |
| **clear_milestones** | 4 | 1.5 | Each milestone has title + tasks + ACs |
| **acceptance_criteria** | 4 | 2.0 | MVP and full ACs defined |
| **execution_log** | 4 | 1.0 | EXECUTION.md updated with progress |
| **amendment_audit** | 4 | 1.5 | Amendments have rationale + checklist |
| **task_granularity** | 4 | 1.0 | Tasks verifiable, not too broad |
| **context_provided** | 4 | 1.0 | (L2/L3) Sufficient context for execution |

**Grade Thresholds**: A ≥90%, B ≥80%, C ≥70%, D ≥60%, F <60%

---

### Archival Policy

| Rule | Behavior |
|------|----------|
| **When to archive** | Status = `completed` AND all milestones done |
| **Archive action** | Move entire folder to `.plans/_archive/PLAN-XXX/` |
| **Retention** | **FOREVER** (disk is cheap, history is valuable) |
| **Git behavior** | Committed to repo (part of project history) |

**Why Never Delete?**
- Provenance: Score history, execution logs, session references
- Learning: "How did we approach X last time?"
- Audit: "When was this feature implemented?"
- Experimentation: Compare plan quality across time

---

### Addendum Conversation Log

**2025-12-31 - SESSION_021 (Continued)**

User asked about PLAN folder structure, archival/deletion, and mid-dev adjustments.

Key insight from user: "We have a lot of information contained in the DISC and it is a record of a back and forth exchange/progression, so I think it should have some flexibility."

Decisions made:
- Q-A1: Master PLAN inside `L3/PLAN-XXX/` (no root files)
- Q-A2: Never delete - archive to `_archive/`
- Q-A3: Amendment pattern with guardrails and escalation rules
- DISC flexibility: Structured Flexibility (strict header/problem/decision, flexible discussion)
- Amendment validation checklist is REQUIRED and blocks CI if any check fails

---

*Addendum added during SESSION_021 to address PLAN management details not covered in original discussion.*
