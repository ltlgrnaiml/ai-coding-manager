# DISC-014: Primary Chain Validation

> **Status**: `resolved`
> **Created**: 2025-12-31
> **Updated**: 2025-12-31
> **Author**: Mycahya Eggleston
> **AI Session**: SESSION_021
> **Depends On**: DISC-011
> **Blocks**: None
> **Dependency Level**: L1
>
> **Parent Discussion**: DISC-011 (Umbrella: Unified Artifact Model)

---

## Problem Statement

Every artifact must trace to a source (Primary Chain Model), but we need behavioral rules for validation, orphan detection, CI enforcement, and graph visualization of artifact relationships.

---

## Summary

Define the behavioral specification for Primary Chain validation: how artifacts are validated for proper source linking, how orphans are detected and reported, and how the artifact graph is constructed and visualized.

---

## Context

### Background

DISC-011 (Umbrella: Unified Artifact Model) established the **Primary Chain Model**:

> Every artifact has ONE primary parent (except DISC which is root). A parent can have MANY children (1:N fan-out).

The schemas now have required fields:
- `ADRSchema.source_discussion` (required)
- `ADRSchema.decision_statement` (required, max 200 chars)
- `DiscussionSchema.problem_statement` (required, max 200 chars)

However, the **validation behavior** is undefined:

| Question | Status |
|----------|--------|
| How are orphaned artifacts detected? | `open` |
| What CI errors vs warnings are raised? | `open` |
| How does the artifact graph extract edges? | `open` |
| How are tier-skips validated? | `open` |

### Trigger

Artifact graph visualization showed orphaned Contract and Plan nodes during DISC-011 discussion, revealing the need for proper edge extraction and validation logic.

---

## Requirements

### Functional Requirements

> **⚠️ SHELL DOCUMENT**: Requirements below are placeholders. Actual requirements TBD during discussion.

- [ ] **FR-1**: Detect artifacts missing required source_* fields
- [ ] **FR-2**: Detect tier-skips without skip_rationale
- [ ] **FR-3**: Detect orphaned artifacts (no parent, not DISC)
- [ ] **FR-4**: Generate artifact graph with proper edges
- [ ] **FR-5**: Provide CI validation script with clear error messages
- [ ] **FR-6**: Support "scope smell" warnings (DISC → >3 ADRs)

### Non-Functional Requirements

> **⚠️ SHELL DOCUMENT**: NFRs below are placeholders.

- [ ] **NFR-1**: Validation must complete in <5s for full repository scan
- [ ] **NFR-2**: Graph visualization must handle 100+ artifacts

---

## Scope

### In Scope

- Primary Chain validation rules
- Orphan detection algorithm
- CI validation script behavior
- Artifact graph edge extraction
- Error and warning message formats

### Out of Scope

- Schema field definitions (already in contracts)
- DevTools UI graph visualization (covered by ADR-0045)
- Migration of existing artifacts (execution task)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should validation be strict (block CI) or permissive (warn only)? | `answered` | **Graduated** - Required fields block CI, orphans/smells warn |
| Q-2 | How should Contract→ADR edges be extracted from Python docstrings? | `answered` | **Regex pattern**: `Per (ADR-\d+|DISC-\d+)` in docstring |
| Q-3 | Should orphan detection run on every commit or only on release? | `answered` | **Every commit** - catch drift early |
| Q-4 | How should umbrella DISCs affect validation (children must complete first)? | `answered` | **Block ADR creation** until children resolved/deferred |
| Q-5 | Should the artifact graph be auto-generated or manually curated? | `answered` | **Auto-generated** (per AUTO EVERYTHING philosophy) |
| Q-6 | Should validation produce a machine-readable report? | `answered` | **Yes, JSON** - enables dashboards, trend tracking |

---

## Options Considered

### Option A: Strict CI Enforcement

All validation errors block CI. No orphans allowed.

**Pros**: Maximum enforcement, no drift  
**Cons**: May block legitimate WIP commits

### Option B: Graduated Enforcement (SELECTED)

Required fields block CI. Orphans and scope smells are warnings.

**Pros**: Balances enforcement with flexibility  
**Cons**: Warnings may be ignored

### Option C: Per-Folder Configuration

Each folder's AGENTS.md configures strictness level.

**Pros**: Flexible per-domain  
**Cons**: Inconsistent enforcement, complexity

---

## Decision

**Selected Option**: **Option B: Graduated Enforcement**

**Rationale**:

1. **Required fields are non-negotiable**: Missing `source_discussion`, `source_adr`, `problem_statement`, `decision_statement` → CI blocks. These are the PRIMARY CHAIN.

2. **Orphans are warnings, not blockers**: Legacy artifacts or WIP may legitimately lack parents temporarily. Flag them, don't block.

3. **Scope smells are advisory**: DISC → >3 ADRs suggests scope creep, but isn't always wrong. Warn and let human decide.

4. **Auto-everything for graph**: Per user's philosophy, artifact graph auto-generates from source_* fields and docstring patterns.

---

## Validation Rules

| Rule | Severity | Trigger |
|------|----------|--------|
| Missing `source_discussion` on ADR | **ERROR** | Blocks CI |
| Missing `source_adr` on SPEC (no skip_rationale) | **ERROR** | Blocks CI |
| Missing required fields (problem_statement, decision_statement) | **ERROR** | Blocks CI |
| Tier-skip without rationale | **ERROR** | Blocks CI |
| Umbrella DISC with incomplete children trying to create ADR | **ERROR** | Blocks CI |
| Orphaned artifact (no parent, not DISC) | **WARNING** | Report only |
| Scope smell: DISC → >3 ADRs | **WARNING** | Report only |
| Contract missing `Per ADR-XXXX` in docstring | **WARNING** | Report only |

---

## Edge Extraction Patterns

```python
# Contract docstrings - regex: r'Per (ADR-\d+|DISC-\d+)'
"""Per ADR-0010: Contracts as SSOT."""  # → Edge to ADR-0010

# PLAN references - JSON field
"source_references": ["DISC-011", "ADR-0048"]  # → Edges

# Markdown links - regex: r'\[(ADR-\d+|DISC-\d+)\]'
"See [ADR-0043](../adrs/ADR-0043.json)"  # → Edge to ADR-0043

# DISC dependencies
"depends_on": ["DISC-001", "DISC-002"]  # → Edges
```

---

## Validation Output Format

```json
{
  "validation_run": {
    "timestamp": "2025-12-31T20:45:00Z",
    "commit": "abc123",
    "total_artifacts": 47,
    "errors": 2,
    "warnings": 5
  },
  "errors": [
    {
      "artifact": "ADR-0049",
      "rule": "missing_source_discussion",
      "message": "ADR-0049 missing required field 'source_discussion'"
    }
  ],
  "warnings": [
    {
      "artifact": "shared/contracts/dat/profile.py",
      "rule": "orphaned_contract",
      "message": "Contract has no 'Per ADR-XXXX' reference in docstring"
    }
  ],
  "graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status | Skipped Tiers |
|---------------|----|-------|--------|---------------|
| Contract | `shared/contracts/devtools/discussion.py` | DiscussionSchema (v2025.12.03) | `active` | - |
| Contract | `shared/contracts/adr_schema.py` | ADRSchema (v2025.12.01) | `active` | - |
| ADR Update | ADR-0048 | Add validation rules guardrails | `pending` | - |
| SPEC | `[TBD]` | Primary Chain Validation Behavior | `pending` | - |
| Script | `tools/validate_primary_chain.py` | CI validation script | `pending` | - |

---

## Conversation Log

### 2025-12-31 - SESSION_021

**Topics Discussed**:
- Identified orphaned artifacts in graph visualization
- Established Primary Chain Model in DISC-011
- Updated schemas with required source_* fields
- Created as child of DISC-011 umbrella to define validation behavior

**Decisions Made (AI recommendations accepted)**:
- Q-1: Graduated enforcement - required fields block, orphans warn
- Q-2: Regex pattern `Per (ADR-\d+|DISC-\d+)` for docstring extraction
- Q-3: Every commit validation to catch drift early
- Q-4: Block ADR creation until umbrella children resolved/deferred
- Q-5: Auto-generated artifact graph (per AUTO EVERYTHING)
- Q-6: JSON validation report for dashboards/trends

**Validation Rules Defined**:
- 5 ERROR rules (block CI)
- 3 WARNING rules (report only)
- Edge extraction patterns for contracts, PLANs, and markdown

---

## Resolution

**Resolution Date**: 2025-12-31
**Resolution Type**: `design_complete`
**Outcome**: Graduated enforcement adopted with 5 ERROR rules (block CI) and 3 WARNING rules (report only). Auto-generated artifact graph with JSON validation reports. Edge extraction via regex patterns.

---

## Quality Score

**Status**: `COMPLETE` - Discussion held, all decisions recorded.

---

---

*This DISC was converted from shell to resolved during SESSION_021.*
