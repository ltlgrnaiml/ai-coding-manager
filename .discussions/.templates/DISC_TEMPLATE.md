# DISC-{NNN}: {Title}

> **Status**: `draft` | `active` | `resolved` | `abandoned`
> **Created**: {YYYY-MM-DD}
> **Updated**: {YYYY-MM-DD}
> **Author**: {Name}
> **AI Session**: SESSION_{XXX}
> **Depends On**: {DISC-XXX, DISC-YYY} | None
> **Blocks**: {DISC-ZZZ} | None
> **Dependency Level**: L0 | L1 | L2 | ...

<!-- ============================================================
     UMBRELLA FIELDS: Add this section if is_umbrella: true
     ============================================================ -->
<!--
> **🌂 UMBRELLA DISC**
> **Is Umbrella**: `true`
> **Child Discussions**:
> - DISC-XXX: {Title}
> - DISC-YYY: {Title}
-->

<!-- ============================================================
     CHILD FIELDS: Add this section if this is a child of an umbrella
     ============================================================ -->
<!--
> **Parent Discussion**: DISC-{XXX} ({Parent Title})
> **Delegation Scope**: {What specific aspect this child addresses}
> **Inherits Context**: `true`
-->

---

## Summary

<!-- One paragraph describing what this discussion is about -->

{Brief description of the feature, enhancement, or topic being discussed}

---

## Context

<!-- Why are we having this discussion? What triggered it? -->

### Background

{Describe the current state and why change is needed}

### Trigger

{What event or need triggered this discussion?}

---

## Requirements

<!-- What must the solution achieve? Use natural language. -->

### Functional Requirements

- [ ] **FR-1**: {Requirement description}
- [ ] **FR-2**: {Requirement description}
- [ ] **FR-3**: {Requirement description}

### Non-Functional Requirements

- [ ] **NFR-1**: {Performance, security, maintainability, etc.}
- [ ] **NFR-2**: {Requirement description}

---

## Constraints

<!-- Hard limits that cannot be violated -->

- **C-1**: {Constraint description}
- **C-2**: {Constraint description}

---

## Open Questions

<!-- Questions that need answers before proceeding -->

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | {Question text} | `open` / `answered` | {Answer if resolved} |
| Q-2 | {Question text} | `open` / `answered` | {Answer if resolved} |

---

## Options Considered

<!-- If architectural decision needed, document options here -->

### Option A: {Name}

**Description**: {How this option works}

**Pros**:
- {Advantage 1}
- {Advantage 2}

**Cons**:
- {Disadvantage 1}
- {Disadvantage 2}

### Option B: {Name}

**Description**: {How this option works}

**Pros**:
- {Advantage 1}

**Cons**:
- {Disadvantage 1}

### Recommendation

{Which option is recommended and why}

---

## Decision Points

<!-- Key decisions that need to be made -->

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | {Decision description} | `pending` / `decided` | {Outcome if decided} |
| D-2 | {Decision description} | `pending` / `decided` | {Outcome if decided} |

---

## Scope Definition

<!-- What is in scope and out of scope for this work -->

### In Scope

- {Item 1}
- {Item 2}

### Out of Scope

- {Item 1 - reason}
- {Item 2 - reason}

---

## Cross-DISC Dependencies

<!-- Document dependencies on other DISCs (per ADR-0043 disc_dependency_management) -->

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-{XXX} | `FS` / `FF` / `SS` / `soft` | `pending` / `stub` / `resolved` | {Milestones} | {Notes} |

### Stub Strategy (if applicable)

<!-- Document stubs used when dependencies aren't resolved -->

| DISC | Stub Location | Stub Behavior |
|------|---------------|---------------|
| DISC-{XXX} | `path/to/stub.py` | {What the stub does} |

---

## Resulting Artifacts

<!-- Link to artifacts created from this discussion -->

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-{XXXX} | {Title} | `draft` / `active` |
| SPEC | SPEC-{XXX} | {Title} | `draft` / `active` |
| Contract | `shared/contracts/{path}` | {Description} | `created` |
| Plan | PLAN-{XXX} | {Title} | `draft` / `active` |

---

## Conversation Log

<!-- Key points from AI ↔ Human discussion (auto-updated by AI) -->

### {YYYY-MM-DD} - SESSION_{XXX}

**Topics Discussed**:
- {Topic 1}
- {Topic 2}

**Key Insights**:
- {Insight 1}
- {Insight 2}

**Action Items**:
- [ ] {Action 1}
- [ ] {Action 2}

---

## Resolution

<!-- Filled when discussion is resolved -->

**Resolution Date**: {YYYY-MM-DD}

**Outcome**: {Summary of what was decided/created}

**Next Steps**:
1. {Step 1}
2. {Step 2}

---

## Quality Score

<!-- Per ADR-0048: Quality rubric scoring for artifact completeness -->

**Status**: `[PENDING]` - Score calculated after required fields populated

---

<!-- ============================================================
     AI INSTRUCTIONS: SHELL vs REAL DOCUMENT
     ============================================================

     SHELL DOCUMENT (when creating as placeholder):
     
     When creating a DISC as a shell placeholder (e.g., during umbrella conversion
     or when spawning child discussions before the actual conversation happens):
     
     1. Set Status to `draft` (not `active`)
     2. Fill problem_statement from available context (required, max 200 chars)
     3. Fill Context/Background from existing evidence
     4. Add placeholder requirements with ⚠️ SHELL DOCUMENT marker
     5. Add relevant Open Questions with status `open`
     6. Leave Decision section with [TO BE DECIDED] placeholder
     7. Set Quality Score to [SHELL - NOT SCORED]
     8. Add HTML comment at bottom with AI SHELL MARKER
     
     SHELL INDICATORS (for AI detection):
     - Status is 'draft'
     - Requirements marked with ⚠️ SHELL DOCUMENT  
     - Decision has [TO BE DECIDED]
     - Quality Score shows [SHELL - NOT SCORED]
     - AI SHELL MARKER comment exists
     
     CONVERTING SHELL TO REAL:
     
     When USER engages with shell discussion:
     1. Change Status to `active`
     2. Review and confirm problem_statement with USER
     3. Remove ⚠️ SHELL DOCUMENT markers from requirements
     4. Work through Open Questions with USER
     5. Record Decision with rationale
     6. Calculate Quality Score using rubric
     7. Remove AI SHELL MARKER comment
     
     UMBRELLA DISC PATTERN:
     
     When converting a DISC to umbrella (broad scope needs subdivision):
     1. Add to header:
        > **🌂 UMBRELLA DISC**
        > **Is Umbrella**: `true`
        > **Child Discussions**: DISC-XXX, DISC-YYY, ...
     2. Create child DISCs as shells with:
        > **Parent Discussion**: DISC-{parent} (Umbrella: {parent_title})
     3. Umbrella cannot produce ADRs until children are completed/deferred
     4. Child discussions inherit context from parent
     
     ============================================================ -->

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model) | See `.discussions/README.md` for usage instructions*
