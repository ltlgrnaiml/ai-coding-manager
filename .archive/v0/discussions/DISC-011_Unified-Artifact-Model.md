# DISC-011: Unified Artifact Model (UAM)

> **Status**: `active`
> **Created**: 2025-12-31
> **Updated**: 2025-12-31
> **Author**: Mycahya Eggleston
> **AI Session**: SESSION_021
> **Depends On**: None
> **Blocks**: None
> **Dependency Level**: L0
> 
> **🌂 UMBRELLA DISC**
> **Is Umbrella**: `true`
> **Child Discussions**:
> - DISC-012: Plan Artifact Structure & Lifecycle
> - DISC-013: Quality Scoring System
> - DISC-014: Primary Chain Validation
> - DISC-015: AI-Native Documentation Architecture

---

## Summary

Design a first-principles documentation strategy that provides deterministic, validated, lifecycle-managed artifacts with concrete inter-document links. This supersedes the fragmented "3-tier document model" (ADR-0016) and integrates with the AI Development Workflow (ADR-0043) to create a unified system called the **Unified Artifact Model (UAM)**.

---

## Context

### Background

The current documentation strategy is fragmented across multiple ADRs:
- **ADR-0010**: Defines Contracts as "Tier 0" foundation (conflicting tier numbering)
- **ADR-0043**: Defines "6-Tier Workflow" (T0-T5) for AI development (another tier system)

The artifact graph visualization revealed orphaned Contract and Plan nodes due to:
1. Missing edge extraction logic for Python contract files
2. Inconsistent cross-referencing patterns between artifacts
3. No formal bidirectional link fields in schemas

### Trigger

Artifact graph visualization showed most purple (Contract) and red (Plan) nodes disconnected, revealing documentation synchronization failures that undermine deterministic development.

---

## Requirements

### Functional Requirements

- [x] **FR-1**: Define a unified pillar model that encompasses all artifact types
- [x] **FR-2**: DISC must be the universal entry point for all non-bug work
- [x] **FR-3**: All artifacts must have lifecycle management with explicit status values
- [x] **FR-4**: Inter-document links must be directional, purposeful, and validated
- [x] **FR-5**: Bug fixes must track provenance to artifacts that introduced the bug
- [ ] **FR-6**: DISC schema must capture enough context to produce high-quality downstream artifacts
- [ ] **FR-7**: CI must validate all artifact schemas and links
- [ ] **FR-8**: DevTools UI must support "Convert to Umbrella" action (take one DISC and subdivide into children, or merge with existing DISCs)

### Non-Functional Requirements

- [x] **NFR-1**: Schema validation via Pydantic for CI automation
- [x] **NFR-2**: Lifecycle management must be as automated as possible
- [ ] **NFR-3**: DevTools workflow UI must guide users to create excellent documents with AI assistance
- [x] **NFR-4**: The documentation strategy itself must be well-documented (self-referential)

---

## Constraints

- **C-1**: Must integrate with existing ADR-0043 workflow execution (session management, fragment-based development)
- **C-2**: Must not break existing artifact scanning in `workflow_service.py`
- **C-3**: Must be solo-dev friendly (minimal overhead, maximum automation)
- **C-4**: Artifacts must remain as files on disk for AI/human shared access

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should ADRs track `source_discussions[]` for provenance? | `answered` | Optional field for provenance, primary direction is DISC→ADR via `resulting_artifacts` |
| Q-2 | When can DISC skip ADR and go directly to SPEC? | `answered` | When no architectural decision is needed (existing ADRs cover it, only behavior needs specification). Requires wizard confirmation + `skipped_tiers` field. |
| Q-3 | When can DISC skip ADR+SPEC and go directly to PLAN? | `answered` | For pure execution work like refactoring where behavior is unchanged. Requires wizard confirmation + `skipped_tiers` field. |
| Q-4 | Should BUG be a separate artifact type or reuse PLAN? | `answered` | Separate type in `.bugs/` with provenance links back to source artifacts |
| Q-5 | What fields are essential in the DISC schema? | `answered` | See finalized schema below - includes `problem_statement`, `scope_boundary`, `resulting_artifacts` with skip tracking |
| Q-6 | How to handle Multi-DISC → Multi-ADR complexity? | `answered` | Primary Chain Model: every child has ONE parent (1:1 upward), parent can have MANY children (1:N downward). Umbrella DISCs for broad topics. |
| Q-7 | How to enforce Primary Chain Model? | `answered` | Schema enforcement (`source_*` required), CI validation, UI wizard with skip confirmation, scope smell detection (>3 children warning) |
| Q-8 | Should we allow N:M relationships? | `answered` | No. Use "related" field for secondary connections, but primary chain is always 1:1 upward. Keeps graph as tree, not DAG. |
| Q-13 | When should a DISC become an umbrella? | `answered` | When problem_statement > 200 chars OR 3+ sub-topics emerge. See "Umbrella DISC Pattern (Formalized)" section. |
| Q-14 | How are child DISCs spawned? | `answered` | As SHELL documents with inherited context. See formalized section. |
| Q-15 | What context do children inherit? | `answered` | trigger, constraints, dependencies. Fresh: requirements, options, decisions. |
| Q-16 | Required umbrella header fields? | `answered` | 🌂 marker, Is Umbrella, Child Discussions list. Children need Parent Discussion. |
| Q-17 | CI validation for umbrella? | `answered` | ERROR: umbrella creates ADR before children done. WARNING: child missing parent ref. |
| Q-18 | Can umbrella skip tiers? | `answered` | Yes, if children produce ADRs. Umbrella can skip with rationale. |
| Q-19 | Umbrella quality scoring? | `answered` | Separate rubric for umbrella (delegation rationale, consolidated summary, etc.) |
| Q-20 | Deferred child handling? | `answered` | Umbrella can proceed. Note in Completion Gate. May produce partial_scope artifacts. |
| Q-21 | Can Contract exist without SPEC? | `answered` | Default NO. Requires `spec_skip_rationale` if no `source_spec`. See Artifact Pillar section. |
| Q-22 | Who can produce what artifacts? | `answered` | Children: SPEC (narrow) + Contract. Umbrella: ADR + SPEC (spanning) + PLAN. See ownership matrix. |
| Q-23 | Retroactive DISC adoption? | `answered` | Child keeps artifacts. Umbrella has `inherited_artifacts` field. |
| Q-24 | Policy DISC (ADR-only)? | `answered` | `is_policy: true` flag. Produces exactly 1 ADR, no downstream. |
| Q-25 | Nested umbrellas allowed? | `answered` | YES. Child can become umbrella. Grandparent tracks via child's `child_discussions`. Completion cascades. |
| Q-26 | Multiple ADRs from child? | `answered` | N/A - Children cannot produce ADRs (Q-22). Exception: `independent_decision: true` with rationale. |
| Q-27 | Sibling circular dependencies? | `answered` | ERROR. Siblings cannot have circular deps. Umbrella must mediate or split differently. |
| Q-28 | Late child addition? | `answered` | Allowed. Umbrella reopens (resolved→active). New child added to `child_discussions`. |
| Q-29 | Abandoned vs deferred child? | `answered` | Deferred = scope postponed. Abandoned = scope removed. Umbrella updates problem_statement if abandoned. |
| Q-30 | Score propagation timing? | `answered` | Umbrella rescored when: (1) child status changes, (2) consolidated summary updated, (3) manual trigger. |
| Q-31 | Should DISCs require expected_artifacts before ADR? | `answered` | Hybrid: SHOULD for standard DISCs (warning), MUST for umbrella (error), OPTIONAL for policy. See schema below. |

---

## Options Considered

### Option A: Extend 3-Tier Model

**Description**: Add Contracts and Plans as Tier 0 and Tier 4 to existing 3-tier model.

**Pros**:
- Minimal change to existing documentation
- Preserves ADR-0016

**Cons**:
- Tier numbering becomes confusing (Tier 0 vs Tier 1 vs T0 vs T1)
- Doesn't address DISC as entry point
- Guides tier still empty/unused

**Rejected because**: Creates more confusion, doesn't solve the fundamental issues.

### Option B: Unified Artifact Model (UAM) with Six Pillars

**Description**: Replace tier numbering with purpose-driven pillars: EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE.

**Pros**:
- No tier number confusion
- Each pillar has ONE job (clear mental model)
- DISC becomes formal entry point
- GUIDE pillar reserved for production (not needed during dev)
- Supports bidirectional traceability

**Cons**:
- Requires superseding ADR-0016
- Migration effort for existing docs

### Recommendation

**Option B (UAM with Six Pillars)** because it provides a clean mental model, eliminates tier confusion, and establishes DISC as the universal entry point for deterministic development.

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Adopt six-pillar model? | `decided` | Yes: EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE |
| D-2 | DISC as universal entry point? | `decided` | Yes, except for Bug Fix which has its own entry |
| D-3 | Supersede ADR-0016? | `decided` | Yes, create ADR-0048 to supersede it |
| D-4 | Add BUG as separate artifact type? | `decided` | Yes, with provenance tracking |
| D-5 | DISC schema fields? | `decided` | Finalized - see schema below with scope enforcement |
| D-6 | Primary Chain Model adoption? | `decided` | Yes - every child has ONE parent, parent can have MANY children |
| D-7 | Tier-skip mechanism? | `decided` | Wizard confirmation + `skipped_tiers` field with rationale |
| D-8 | Umbrella DISC pattern? | `decided` | Yes - `is_umbrella` flag + `child_discussions[]` for broad topics |

---

## Scope Definition

### In Scope

- Six-pillar model definition (EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE)
- DISC schema with required fields for excellence
- Lifecycle state machine for all artifact types
- Inter-document link validation requirements
- BUG artifact type with provenance tracking
- ADR-0048 to supersede ADR-0016

### Out of Scope

- Graph builder implementation fixes (separate task)
- Backfilling existing artifacts with new fields (separate task)
- CI validation scripts (separate task)
- DevTools UI changes (separate task)

---

## The Six Pillars

| Pillar | Artifact | Verb | Purpose | Lifecycle States |
|--------|----------|------|---------|------------------|
| **EXPLORE** | DISC | Explore | Capture design conversation | draft→active→completed/abandoned |
| **DECIDE** | ADR | Decide | Record architectural WHY | draft→active→superseded/deprecated |
| **DEFINE** | SPEC | Define | Specify behavioral WHAT | draft→active→superseded/deprecated |
| **SHAPE** | Contract | Shape | Define data HOW | active→deprecated |
| **EXECUTE** | PLAN | Execute | Track implementation work | draft→active→completed/blocked |
| **GUIDE** | Guide | Guide | Document for production | draft→active→deprecated |

Special case:
| **BUG** | Bug | Report | Track defects with provenance | reported→confirmed→fixing→fixed→verified |

---

## Workflow Entry Points

| Scenario | Entry Pillar | Valid Paths | Notes |
|----------|--------------|-------------|-------|
| **Architectural Change** | EXPLORE | DISC→ADR→SPEC→Contract→PLAN | Full path required |
| **New Feature (complex)** | EXPLORE | DISC→ADR→SPEC→Contract→PLAN | Full path |
| **New Feature (simple)** | EXPLORE | DISC→SPEC→Contract→PLAN | Skip ADR if no architecture decision |
| **Enhancement** | EXPLORE | DISC→SPEC→Contract→PLAN | Behavior change only |
| **Refactor** | EXPLORE | DISC→PLAN | Pure execution, no behavior change |
| **New Data Structure** | EXPLORE | DISC→Contract→PLAN | If patterns already established |
| **Bug Fix** | BUG | BUG→PLAN | Provenance links to source artifacts |
| **Production Docs** | GUIDE | Guide | Links to existing ADR/SPEC/Contract |

---

## Inter-Document Link Types

| Link Type | Direction | From | To | Purpose | Validation |
|-----------|-----------|------|-----|---------|------------|
| `creates` | Forward | DISC | ADR, SPEC, PLAN | Generative | Target must exist |
| `implements` | Bidirectional | Contract | ADR, SPEC | Enforcement | Both must exist |
| `specifies` | Bidirectional | ADR | SPEC | Elaboration | Both must exist |
| `depends_on` | Forward | Any | Any | Prerequisite | Target must be active |
| `supersedes` | Forward | New | Old | Replacement | Old.status → superseded |
| `provenance` | Backward | BUG | ADR, SPEC, Contract | Root cause | Target must exist |
| `documents` | Forward | GUIDE | ADR, SPEC, Contract | Explanation | Target must exist |

---

## Primary Chain Model

### Core Principle

**Every artifact has ONE primary parent** (except DISC which is the root).
**A parent can have MANY children** (1:N fan-out is valid).

This keeps the artifact graph as a **tree** (or forest), not a complex DAG with cycles.

### Cardinality Rules

| Pattern | Valid? | Enforcement | Example |
|---------|--------|-------------|---------|
| 1 DISC → 1 ADR | ✅ Default | No special handling | Most common case |
| 1 DISC → N ADRs | ✅ Valid | Warn if N > 3 (scope smell) | Focused DISC, multiple decision facets |
| 1 DISC → N SPECs | ✅ Valid | Requires `skipped_tiers: ["adr"]` | Skip ADR when architecture exists |
| 1 DISC → N Contracts | ✅ Valid | Requires `skipped_tiers: ["adr", "spec"]` | Data-only changes |
| 1 DISC → N PLANs | ✅ Valid | Requires `skipped_tiers: ["adr", "spec", "contract"]` | Refactoring work |
| Umbrella DISC → Child DISCs | ✅ Valid | `is_umbrella: true` | Broad explorations |
| N DISCs → 1 ADR | ⚠️ Rare | One `primary`, others `related` | Convergent decisions |

### Visual Representation

```
DISC-011 (Primary Chain: every child points UP to ONE parent)
│
├── creates → ADR-0048 (source_discussion: DISC-011) ✓
│               │
│               └── specifies → SPEC-004 (source_adr: ADR-0048) ✓
│                                 │
│                                 └── shapes → Contract-A (source_spec: SPEC-004) ✓
│
├── creates → ADR-0049 (source_discussion: DISC-011) ✓
│
└── creates → SPEC-005 (source_discussion: DISC-011, skipped_tiers: ["adr"]) ✓
```

### Umbrella DISC Pattern

For legitimately broad topics, use an umbrella structure:

```
DISC-006 (Umbrella: Knowledge Archive System)
├── is_umbrella: true
├── child_discussions:
│     ├── DISC-003 (Langchain Integration)
│     ├── DISC-004 (PII Sanitization)  
│     └── DISC-005 (Embedding Model Selection)
│
└── resulting_artifacts:
      └── ADR-0046 (synthesizes all children)
```

**Umbrella Rules**:

1. Umbrella DISC cannot produce ADRs until children are resolved
2. Child DISCs have `parent_discussion: DISC-006`
3. Umbrella's `resulting_artifacts` may reference child results

---

## Tier-Skip Mechanism

When DISC goes directly to SPEC, Contract, or PLAN (skipping intermediate tiers):

### Required Fields in ResultingArtifact

```python
class ResultingArtifact(BaseModel):
    type: Literal["adr", "spec", "contract", "plan"]
    id: str
    title: str
    status: str = "draft"
    relationship: Literal["creates", "contributes_to"] = "creates"
    
    # SKIP TRACKING (new)
    skipped_tiers: list[Literal["adr", "spec", "contract"]] = []
    skip_rationale: str | None = None  # Required if skipped_tiers not empty
```

### Wizard Confirmation Flow

The DevTools UI must confirm tier skips:

1. User selects artifact type to create from DISC
2. If not ADR (the default), wizard asks for skip rationale
3. Rationale is stored in `skip_rationale` field
4. CI validates that `skip_rationale` exists when `skipped_tiers` is non-empty

---

## Scope Enforcement Rules

### The "One Thing" Rule

Every document answers ONE question:

| Pillar | The ONE Question | Scope Test |
|--------|------------------|------------|
| DISC | "What problem are we solving?" | ONE sentence problem statement |
| ADR | "What architectural choice did we make?" | ONE sentence decision statement |
| SPEC | "What behavior does this feature exhibit?" | ONE user-observable behavior |
| Contract | "What is the shape of this data?" | ONE logical entity |
| PLAN | "What work needs to be done?" | ONE shippable increment |

### Schema Enforcement

```python
# In DISC schema
problem_statement: str = Field(
    ...,
    min_length=20,
    max_length=200,  # Forces conciseness
    description="ONE sentence describing the problem"
)

# In ADR schema  
decision_statement: str = Field(
    ...,
    min_length=20,
    max_length=200,  # ONE sentence
    description="We will [verb] [choice] because [reason]"
)
```

### CI Validation Rules

| Rule | Trigger | Severity |
|------|---------|----------|
| Missing `source_*` field | Non-DISC artifact without parent | Error |
| `problem_statement` > 200 chars | DISC scope too broad | Warning |
| `decision_statement` has multiple sentences | ADR covers >1 decision | Warning |
| DISC produces >3 ADRs | Scope smell | Warning |
| `skipped_tiers` non-empty but `skip_rationale` empty | Missing justification | Error |
| Orphaned artifact (no parent, not DISC) | Broken chain | Error |

---

## Finalized DISC Schema

```python
class DiscussionSchema(BaseModel):
    """Discussion artifact schema - universal entry point for non-bug work.
    
    Per DISC-011: Unified Artifact Model (UAM)
    - DISC is universal entry point (except Bug Fix)
    - Primary Chain Model: every child has ONE parent
    - Scope enforcement via problem_statement max_length
    """
    
    # === IDENTITY (Required) ===
    id: str = Field(..., pattern=r"DISC-\d{3}")
    title: str = Field(..., min_length=10, max_length=100)
    status: DiscussionStatus  # draft, active, completed, abandoned, deferred
    
    # === PROVENANCE (Required) ===
    created_date: str  # ISO-8601
    updated_date: str  # ISO-8601
    author: str
    session_id: str | None  # SESSION_XXX if AI-assisted
    
    # === SCOPE ENFORCEMENT (New - Required) ===
    problem_statement: str = Field(
        ...,
        min_length=20,
        max_length=200,  # Forces focused scope
        description="ONE sentence: What problem are we solving?"
    )
    
    # === CONTEXT (Required) ===
    summary: str = Field(..., min_length=50)
    trigger: str = Field(..., min_length=20)
    
    # === UMBRELLA PATTERN (Optional) ===
    is_umbrella: bool = False  # True if coordinating child DISCs
    parent_discussion: str | None = None  # If child of umbrella
    child_discussions: list[str] = []  # If umbrella, list child DISC IDs
    
    # === REQUIREMENTS (Optional but encouraged) ===
    functional_requirements: list[Requirement] = []
    non_functional_requirements: list[Requirement] = []
    constraints: list[str] = []
    
    # === EXPLORATION (Optional) ===
    open_questions: list[OpenQuestion] = []
    options_considered: list[Option] = []
    
    # === DECISION (Required for completion) ===
    recommendation: str | None = None
    decision: str | None = None
    decision_rationale: str | None = None
    
    # === SCOPE (Optional) ===
    in_scope: list[str] = []
    out_of_scope: list[str] = []
    
    # === DEPENDENCIES (For multi-DISC work) ===
    depends_on: list[str] = []  # DISC-XXX
    blocks: list[str] = []  # DISC-XXX
    dependency_level: int = 0  # L0, L1, L2...
    
    # === OUTPUTS (Required for completion) ===
    resulting_artifacts: list[ResultingArtifact] = []
    
    # === RESOLUTION (Required for completion) ===
    resolution_type: ResolutionType | None = None
    resolution_date: str | None = None
    resolution_notes: str | None = None


class ResultingArtifact(BaseModel):
    """Artifact produced by this discussion."""
    
    type: Literal["adr", "spec", "contract", "plan"]
    id: str
    title: str
    status: str = "draft"
    relationship: Literal["creates", "contributes_to"] = "creates"
    
    # TIER-SKIP TRACKING
    skipped_tiers: list[Literal["adr", "spec", "contract"]] = []
    skip_rationale: str | None = None  # Required if skipped_tiers not empty
```

### Completion Requirements

A DISC can only transition to `completed` status when:
1. `decision` field is populated (what was decided)
2. `resulting_artifacts` has at least one entry (what was created)
3. `resolution_type` is set (how it closed)
4. All `open_questions` are either `answered` or `deferred`
5. If `is_umbrella`, all `child_discussions` must be `completed` or `deferred`

---

## Quality Score (Self-Evaluation)

**Overall: 88.1% (Grade: B)** - Good, minor improvements possible

| Criterion | Weight | Score | Points | Notes |
|-----------|--------|-------|--------|-------|
| Problem Statement | 2.0x | STRONG | 6/6 | Focused, actionable problem definition |
| Context & Background | 1.5x | STRONG | 4.5/4.5 | Rich ADR references (0016, 0043, 0010) |
| Options Analysis | 1.5x | ADEQUATE | 5/7.5 | 2 options, could add more depth |
| Requirements Capture | 1.0x | ADEQUATE | 2.7/4 | FRs implicit, NFRs not explicit |
| Open Questions | 1.0x | STRONG | 3/3 | Q-1 through Q-12 tracked |
| Scope Definition | 1.0x | STRONG | 3/3 | Clear in/out of scope |
| Project Awareness | 1.0x | STRONG | 4/4 | Cites existing contracts and ADRs |

**CI Status**: ✅ PASS (all required criteria > 0)

**Areas for Improvement**:
- Add explicit NFRs (performance, maintainability targets)
- Deepen options analysis with more alternatives

---

## Cross-DISC Dependencies

None for this discussion.

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status | Skipped Tiers |
|---------------|----|-------|--------|---------------|
| Contract | `shared/contracts/devtools/discussion.py` | DiscussionSchema (v2025.12.03) | `active` | spec |
| Contract | `shared/contracts/devtools/bug.py` | BugSchema (v2025.12.01) | `active` | spec |
| Contract | `shared/contracts/adr_schema.py` | ADRSchema (v2025.12.01) | `active` | spec |
| Contract | `shared/contracts/devtools/quality_rubrics.py` | Quality Rubrics (v2025.12.01) | `active` | spec |
| ADR | ADR-0048 | Unified Artifact Model | `active` | - |

**Skip Rationale**: Contracts updated directly from DISC because schema changes are self-documenting
via docstrings and Pydantic field descriptions. No separate SPEC needed for data shape definitions.

---

## Conversation Log

### 2025-12-31 - SESSION_021

**Topics Discussed**:
- Root cause analysis of orphaned artifact graph nodes
- Evaluation of current 3-tier model limitations
- First-principles documentation strategy redesign
- Six-pillar model (EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE)
- DISC as universal entry point
- Bidirectional vs unidirectional link requirements
- Bug fix special case with provenance tracking
- DISC schema field requirements
- Multi-DISC → Multi-ADR cardinality complexity
- Primary Chain Model (every child has ONE parent)
- Tier-skip mechanism with wizard confirmation
- Umbrella DISC pattern for broad topics
- Scope enforcement via "One Thing" rule
- CI validation rules for chain integrity

**Key Insights**:
- Tier numbering across ADR-0016, ADR-0010, ADR-0043 is inconsistent and confusing
- Guides (Tier 3) never materialized because solo-dev doesn't need HOW-TO docs during development
- DISC should be universal entry point to capture context before any implementation
- Bug fixes are special because they need long-lived provenance tracking
- Contracts reference ADRs in docstrings (`Per ADR-XXXX:`) but graph builder doesn't extract them
- Primary Chain = 1:1 upward (child→parent), 1:N downward (parent→children)
- N:M complexity avoided by keeping graph as tree, not DAG
- Tier-skip requires explicit rationale (wizard + CI validation)
- Umbrella pattern handles legitimately broad topics without scope violation
- Industry best practices (AWS, Microsoft, adr.github.io) confirm "one decision per ADR"

**Action Items**:
- [x] Create DISC-011 (this file)
- [x] Update DiscussionSchema in Pydantic with new fields
- [x] Update INDEX.md with DISC-011
- [ ] Create ADR-0048 to supersede ADR-0016
- [ ] Update workflow_service.py to extract Contract→ADR edges
- [ ] Create CI validation script for chain integrity

---

## Open Questions (Resolved)

| ID | Question | Status | Decision |
|----|----------|--------|----------|
| Q-9 | Should we create BUG schema now or defer? | `answered` | **Create now** — nail it down as part of UAM |
| Q-10 | Should existing DISCs be backfilled with `problem_statement`? | `answered` | **Yes, break them** — all docs must comply, validation pass required |
| Q-11 | Should ADR schema require `source_discussion` field? | `answered` | **Yes, break them** — full Primary Chain enforcement |
| Q-12 | CI validation: error vs warning for scope smells? | `answered` | **STRICT (Error)** — greenfield, do it right first time, per-folder AGENTS.md enforcement |

### Enforcement Philosophy (User Confirmed)

> "We are greenfield and do not shy from breaking changes. I WANT ALL DOCS to be fully aligned 
> with whatever the new proposal provides us after decision time. Part of our execution will be 
> to validate EVERY SINGLE EXISTING DOCUMENT meets both the technical, structural, and content 
> requirements/rules. Only then will I be satisfied."

**Implications**:
1. All schemas enforce required fields (no optional fallbacks)
2. CI validation is STRICT (errors, not warnings)
3. Every existing artifact must be migrated to comply
4. AGENTS.md per-folder rules enforce content guidelines
5. No new code changes until documentation is validated

---

## Artifact Pillar Distinction Matrix

This table defines the critical distinction between ALL artifact types in the UAM. Essential reading for understanding what each file type is responsible for.

### The Six Pillars: Complete Comparison

| Aspect | DISC (EXPLORE) | ADR (DECIDE) | SPEC (DEFINE) | Contract (SHAPE) | PLAN (EXECUTE) | GUIDE |
|--------|----------------|--------------|---------------|------------------|----------------|-------|
| **Question Answered** | "What problem are we solving?" | "What architectural choice did we make?" | "What behavior should this exhibit?" | "What shape must this data have?" | "What work needs to be done?" | "How do I use this in production?" |
| **Format** | Markdown | JSON | JSON | Python (Pydantic) | JSON + Markdown | Markdown |
| **Audience** | Humans (exploratory) | Humans (decision record) | Humans first, machines second | Machines first, humans second | AI + Humans | End users |
| **Executable?** | No | No | No (but testable) | Yes (runtime validation) | Yes (task tracking) | No |
| **Contains** | Problem, options, decisions, questions | Decision statement, rationale, consequences | Requirements, examples, edge cases, acceptance criteria | Fields, types, validators, defaults | Tasks, milestones, verification commands | Steps, examples, troubleshooting |
| **When Created** | At problem discovery | When decision needed | Before implementation | During implementation | Before coding | After feature stable |
| **Purpose** | Capture design conversation | Record architectural WHY | Agreement on behavior | Enforcement of structure | Track implementation | Enable production use |
| **Lifecycle** | draft→active→resolved | draft→accepted→superseded | draft→active→superseded | active→deprecated | draft→active→completed | draft→active→deprecated |

### Dependency Chain Rules

| From | To | Relationship | Required? | Notes |
|------|-----|-------------|-----------|-------|
| **ADR** | DISC | `source_discussion` | YES | Every ADR traces to a DISC |
| **SPEC** | ADR | `source_adr` | YES* | *Or `source_discussion` with `skip_rationale` |
| **Contract** | SPEC | `source_spec` | YES* | *Or `skip_rationale` (see Q-22 below) |
| **PLAN** | Any | `source_references` | YES | Can reference DISC, ADR, SPEC, or Contract |
| **GUIDE** | Any | `documents` | YES | References what it documents |

### Q-21: No Contract Without SPEC Rule

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-21 | Can a Contract exist without a SPEC? | `answered` | **Default: NO.** Every Contract should have a SPEC explaining the behavior it enforces. Exception: Simple internal DTOs can skip SPEC with `spec_skip_rationale` field. CI validates this field exists when no `source_spec` present. |

**Schema Addition**:
```python
class ContractMetadata(BaseModel):
    """Metadata for contracts (in docstring or separate file)."""
    
    source_spec: str | None = None  # SPEC-XXXX
    spec_skip_rationale: str | None = None  # Required if source_spec is None
    
    @model_validator(mode="after")
    def require_spec_or_rationale(self) -> Self:
        if not self.source_spec and not self.spec_skip_rationale:
            raise ValueError("Contract must have source_spec OR spec_skip_rationale")
        return self
```

**Valid Skip Rationales**:
- "Internal DTO for module X, self-documenting via Pydantic field descriptions"
- "Generated contract from external schema (OpenAPI import)"
- "Trivial enum with no behavioral complexity"

---

## Umbrella Artifact Ownership Rules

### Q-22: Who Can Produce What Artifacts?

| Artifact Type | Standalone DISC | Child DISC | Umbrella DISC | Rule |
|---------------|-----------------|------------|---------------|------|
| **ADR** | ✅ Yes | ❌ No | ✅ Yes | ADRs are strategic; umbrella synthesizes architectural decisions |
| **SPEC (narrow)** | ✅ Yes | ✅ Yes | ❌ No | Child owns behavior specific to its delegation scope |
| **SPEC (spanning)** | ✅ Yes | ❌ No | ✅ Yes | Umbrella owns behavior that spans multiple children |
| **Contract** | ✅ Yes | ✅ Yes | ✅ Yes | Anyone who needs the data shape |
| **PLAN** | ✅ Yes | ✅ Yes | ✅ Yes | Execution can be coordinated at any level |

### The "Spanning Test" for SPECs

When a child DISC wants to create a SPEC, ask:

> "Does this SPEC describe behavior that touches OTHER children of the same umbrella?"

- **YES** → Umbrella must produce the SPEC (escalate to parent)
- **NO** → Child can produce the SPEC

### Why Children Cannot Produce ADRs

ADRs are **architectural decisions**. In an umbrella pattern:

1. Children EXPLORE facets of a problem
2. Children may discover WHAT behavior is needed (SPEC)
3. Children may define data shapes (Contract)
4. But the architectural WHY must be synthesized at umbrella level

**Exception**: If a child's exploration reveals an architectural decision that is:
- Completely independent of other children
- Does not affect umbrella's overall architecture

Then child can produce ADR with `independent_decision: true` flag and rationale.

### Q-23: Retroactive Adoption (Existing DISC Becomes Child)

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-23 | What happens when existing DISC with artifacts becomes a child? | `answered` | **Option C**: Child keeps its artifacts. Umbrella has `inherited_artifacts` field listing pre-adoption artifacts. Future artifacts follow ownership rules above. |

**Schema**:
```python
# In umbrella DISC
inherited_artifacts: list[InheritedArtifact] = []

class InheritedArtifact(BaseModel):
    from_child: str  # DISC-XXX
    artifacts: list[str]  # ["ADR-0046", "SPEC-002"]
    adoption_date: str  # ISO-8601
    adoption_rationale: str
```

### Q-24: Policy DISC Pattern (ADR-Only Output)

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-24 | How to handle DISCs that only produce an ADR? | `answered` | **Policy DISC** pattern. `is_policy: true` flag. Produces exactly 1 ADR, no downstream artifacts. Special workflow entry point. |

**Schema**:
```python
class DiscussionSchema(BaseModel):
    # ... existing fields ...
    
    is_policy: bool = False  # True if DISC produces ADR-only
    policy_scope: Literal["process", "convention", "constraint"] | None = None
```

**CI Validation**:
- ERROR: `is_policy: true` AND produces SPEC/Contract/PLAN
- ERROR: `is_policy: true` AND produces != 1 ADR
- WARNING: DISC produces only ADR without `is_policy: true`

**Workflow Entry Point Addition**:

| Scenario | Entry Pillar | Valid Paths | Notes |
|----------|--------------|-------------|-------|
| **Policy/Guideline** | EXPLORE | DISC→ADR | `is_policy: true`, no downstream |

---

## Umbrella DISC Pattern (Formalized)

This section formalizes ALL aspects of the Umbrella DISC pattern. DISC-011 itself is the canonical example.

### Q-13 through Q-20: Umbrella Pattern Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-13 | When should a DISC become an umbrella? | `answered` | When problem_statement would exceed 200 chars OR when 3+ distinct sub-topics emerge during discussion. Conversion via "Split to Umbrella" wizard action. |
| Q-14 | How are child DISCs spawned? | `answered` | As SHELL documents (status: `draft`) with inherited context. Shell has `⚠️ SHELL DOCUMENT` markers until USER engages. |
| Q-15 | What context do children inherit from parent? | `answered` | **Inherited**: `trigger`, `constraints`, cross-DISC dependencies. **Referenced**: problem_statement (child narrows it). **Fresh**: own requirements, options, decisions. |
| Q-16 | What are required umbrella header fields? | `answered` | `🌂 UMBRELLA DISC` visual marker, `Is Umbrella: true`, `Child Discussions: [list]`. Children need `Parent Discussion: DISC-XXX`. |
| Q-17 | What CI validation for umbrella pattern? | `answered` | ERROR: Umbrella creates ADR before all children resolved/deferred. WARNING: Child missing `parent_discussion`. ERROR: `is_umbrella: true` but `child_discussions` empty. |
| Q-18 | Can umbrella skip tiers if children produce ADRs? | `answered` | Yes. If child produces ADR-001, umbrella can produce SPEC-001 with `skipped_tiers: ["adr"]` and `skip_rationale: "Architecture decided in child DISC-XXX → ADR-001"`. |
| Q-19 | How is umbrella quality scored? | `answered` | Umbrella scored on: (1) problem_statement clarity, (2) delegation rationale, (3) consolidated decision summary, (4) artifact lineage completeness. Children scored individually. |
| Q-20 | What happens if a child is deferred? | `answered` | Umbrella can proceed. Deferred child noted in Completion Gate. Umbrella's resulting artifacts may have `partial_scope: true` with rationale linking to deferred child. |

### Umbrella Schema Fields (Complete)

```python
# In parent (umbrella) DISC
is_umbrella: bool = True
child_discussions: list[str] = ["DISC-012", "DISC-013", "DISC-014"]
umbrella_completion_gate: UmbrellaCompletionGate  # NEW

# In child DISC
parent_discussion: str = "DISC-011"
delegation_scope: str = "What specific aspect this child addresses"  # NEW
inherits_context: bool = True  # NEW
```

### Umbrella Completion Gate Schema

```python
class UmbrellaCompletionGate(BaseModel):
    """Tracks umbrella readiness for resolution."""
    
    all_children_resolved: bool = False
    child_status: dict[str, Literal["draft", "active", "resolved", "deferred"]]
    deferred_children: list[str] = []
    deferred_rationale: str | None = None
    consolidated_decisions_exist: bool = False
    artifact_lineage_complete: bool = False
    ready_for_resolution: bool = False  # Computed from above
```

### Umbrella Lifecycle

```
1. DISC created as normal (draft → active)
2. Scope grows beyond 200 chars OR 3+ sub-topics emerge
3. USER triggers "Convert to Umbrella" wizard
4. Wizard creates child SHELL DISCs with inherited context
5. Each child activated when USER engages
6. Children resolve independently
7. Umbrella consolidates decisions when all children done
8. Umbrella produces synthesizing artifacts (ADR/SPEC/PLAN)
9. Umbrella resolves
```

### Umbrella Quality Rubric (Addition to quality_rubrics.py)

| Criterion | Weight | Description | Max Points |
|-----------|--------|-------------|------------|
| Problem Statement | 2.0x | Clear, focused parent scope | 6 |
| Delegation Rationale | 1.5x | Why each child was separated | 4.5 |
| Child Tracking | 1.0x | Status table maintained | 3 |
| Context Inheritance | 1.0x | Children properly reference parent | 3 |
| Consolidated Summary | 1.5x | All child decisions synthesized | 4.5 |
| Artifact Lineage | 1.0x | Complete mapping of all outputs | 3 |
| Completion Gate | 1.0x | Checklist complete and accurate | 3 |

**Umbrella-specific CI Checks**:
- ERROR: `is_umbrella: true` AND `child_discussions` empty
- ERROR: Umbrella creates ADR before children complete
- WARNING: Child missing `parent_discussion` back-reference
- WARNING: Umbrella missing consolidated decision summary

### Template Update Required

The `DISC_TEMPLATE.md` needs visible umbrella fields (not just comments):

```markdown
<!-- UMBRELLA FIELDS (add if is_umbrella: true) -->
> **🌂 UMBRELLA DISC**
> **Is Umbrella**: `true`
> **Child Discussions**:
> - DISC-XXX: {Title}
> - DISC-YYY: {Title}

<!-- CHILD FIELDS (add if has parent) -->
> **Parent Discussion**: DISC-XXX ({Parent Title})
> **Delegation Scope**: {What this child addresses}
> **Inherits Context**: `true`
```

---

## Umbrella: Child Discussion Status

| Child DISC | Title | Status | Key Decisions |
|------------|-------|--------|---------------|
| **DISC-012** | Plan Artifact Structure & Lifecycle | `resolved` | L3-first, Auto-sync, Never delete, Amendment guardrails |
| **DISC-013** | Quality Scoring System | `resolved` | Score Provenance Chain, Embedded history, AI experimentation |
| **DISC-014** | Primary Chain Validation | `resolved` | Graduated enforcement, Auto-graph, JSON validation |

### Delegation Rationale

| Child | Why Separated | Scope Boundary |
|-------|---------------|----------------|
| **DISC-012** | PLAN artifact complexity required focused discussion on folder structure, L1/L2/L3 templates, lifecycle states, and mid-dev amendments | Owns: `.plans/` structure, amendment rules, archival policy |
| **DISC-013** | Quality scoring has its own behavioral complexity (timing, persistence, provenance) | Owns: Scoring algorithm, rubric versioning, Score Provenance Chain |
| **DISC-014** | Validation rules and graph extraction needed detailed spec | Owns: CI validation rules, edge extraction patterns, error vs warning |

---

## Umbrella: Consolidated Decision Summary

### From DISC-011 (Umbrella)

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Six-pillar model | EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE | Replaces confusing tier numbering |
| Primary Chain Model | 1:1 upward, 1:N downward | Keeps graph as tree, not DAG |
| DISC as entry point | Universal except bugs | Captures context before implementation |
| BUG as separate type | `.bugs/` with provenance | Long-lived tracking back to source artifacts |
| Tier-skip mechanism | Wizard + rationale | Flexibility without losing audit trail |
| Umbrella pattern | `is_umbrella` + `child_discussions[]` | Handles broad topics |

### From DISC-012 (Plan Artifact)

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Default granularity | L3 (Procedural) | EXP-001 proved 50%+ variance reduction |
| Folder structure | `L{1,2,3}/PLAN-XXX/` | No root-level files |
| Completed PLANs | Archive to `_archive/` | NEVER delete |
| Mid-dev adjustments | Amendment pattern | Validation checklist prevents scope creep |
| DISC flexibility | Structured Flexibility | Strict header/decision, flexible discussion |

### From DISC-013 (Quality Scoring)

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Calculation timing | Debounced 300ms | Responsive without perf issues |
| CI blocking | Required fields only | Grade < C is warning |
| Persistence | Hybrid on-demand + embedded | SSOT + audit trail |
| Rubric changes | Auto-rescore, LOG previous | Never overwrite history |
| Scorer tracking | system/ai:model/human | Enables trust calibration |

### From DISC-014 (Validation)

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Enforcement level | Graduated | Required fields error, orphans warn |
| Edge extraction | Regex patterns | `Per (ADR-\d+|DISC-\d+)` in docstrings |
| Validation frequency | Every commit | Catch drift early |
| Graph generation | Auto-generated | Per AUTO EVERYTHING philosophy |
| Output format | JSON | Enables dashboards and trends |

---

## Umbrella: Consolidated Artifact Lineage

### Primary Chain Tree

```
DISC-011 (Umbrella: Unified Artifact Model)
├── ADR-0048 (Unified Artifact Model) ← Umbrella produces
│   ├── SPEC-0050 (DISC Schema) ← Umbrella owns (spanning)
│   │   ├── DiscussionSchema (Contract)
│   │   ├── UmbrellaCompletionGate (Contract)
│   │   ├── InheritedArtifact (Contract)
│   │   └── BugSchema (Contract)
│   │
│   ├── SPEC-0051 (Quality Scoring) ← DISC-013 owns (narrow)
│   │   ├── QualityScore (Contract) [existing]
│   │   └── ScoreProvenance (Contract)
│   │
│   ├── SPEC-0052 (Validation Rules) ← DISC-014 owns (narrow)
│   │   └── ValidationResult (Contract)
│   │
│   └── SPEC-0053 (PLAN Structure) ← DISC-012 owns (narrow)
│       └── PlanSchema (Contract) [existing]
│
├── DISC-012 (Child: Plan Artifact) → delegates SPEC-0053
├── DISC-013 (Child: Quality Scoring) → delegates SPEC-0051
├── DISC-014 (Child: Validation) → delegates SPEC-0052
│
└── PLAN-002 (UAM Implementation) ← Umbrella produces
```

### Artifact Status Matrix

| Artifact | Type | Status | Producer | Parent |
|----------|------|--------|----------|--------|
| **ADR-0048** | ADR | `active` | DISC-011 (Umbrella) | DISC-011 |
| **SPEC-0050** | SPEC | `pending` | DISC-011 (Umbrella) | ADR-0048 |
| **SPEC-0051** | SPEC | `pending` | DISC-013 (Child) | ADR-0048 |
| **SPEC-0052** | SPEC | `pending` | DISC-014 (Child) | ADR-0048 |
| **SPEC-0053** | SPEC | `pending` | DISC-012 (Child) | ADR-0048 |
| **DiscussionSchema** | Contract | `pending` | DISC-011 | SPEC-0050 |
| **UmbrellaCompletionGate** | Contract | `pending` | DISC-011 | SPEC-0050 |
| **InheritedArtifact** | Contract | `pending` | DISC-011 | SPEC-0050 |
| **BugSchema** | Contract | `pending` | DISC-011 | SPEC-0050 |
| **QualityScore** | Contract | `existing` | DISC-013 | SPEC-0051 |
| **ScoreProvenance** | Contract | `pending` | DISC-013 | SPEC-0051 |
| **ValidationResult** | Contract | `pending` | DISC-014 | SPEC-0052 |
| **PlanSchema** | Contract | `existing` | DISC-012 | SPEC-0053 |
| **PLAN-002** | PLAN | `pending` | DISC-011 (Umbrella) | DISC-011 |

---

## Umbrella: Completion Gate

This umbrella can be marked `resolved` when:

- [x] All child discussions are `resolved` or `deferred`
  - [x] DISC-012: `resolved`
  - [x] DISC-013: `resolved`
  - [x] DISC-014: `resolved`
- [x] Consolidated decision summary exists (above)
- [x] Consolidated artifact lineage exists (above)
- [ ] All `pending` artifacts created:
  - [ ] `score_provenance.py` contract
  - [ ] `validate_primary_chain.py` script
- [x] No open questions remain in umbrella (Q-1 to Q-12 answered)

**Current Status**: Ready for resolution pending artifact creation.

---

## Resolution

**Resolution Date**: 2025-12-31

**Outcome**: Unified Artifact Model (UAM) adopted with Six Pillars, Primary Chain Model, and supporting infrastructure. Three child discussions resolved with comprehensive decisions on PLAN management, quality scoring, and validation rules.

**Remaining Implementation** (For PLAN Execution):

### Schema Updates
1. Update Pydantic schemas with new fields:
   - `spec_skip_rationale` in Contract metadata
   - `is_policy` and `policy_scope` in DiscussionSchema
   - `inherited_artifacts` in DiscussionSchema (for umbrella adoption)
   - `independent_decision` flag for child ADR exceptions
   - `UmbrellaCompletionGate` model
   - `InheritedArtifact` model

### CI Validation Updates
2. Update CI validation scripts with new rules:
   - Contract without `source_spec` AND without `spec_skip_rationale`: ERROR
   - Sibling DISCs with circular `depends_on`: ERROR
   - Policy DISC produces != 1 ADR: ERROR
   - Policy DISC produces SPEC/Contract/PLAN: ERROR
   - Child DISC produces ADR without `independent_decision: true`: ERROR

### Backfill Tasks
3. Backfill existing contracts with `source_spec` or `spec_skip_rationale`
4. Create Policy DISCs for orphan policy ADRs (ADR-0011, ADR-0018, ADR-0031, etc.)

### Pending Artifact Creation
5. Create `score_provenance.py` contract per DISC-013
6. Create `validate_primary_chain.py` script per DISC-014
7. Migrate non-conforming files per DISC-012

---

## P2: Orphan ADR Migration Tasks

**To be executed during PLAN implementation:**

### High Priority (Partial Supersession)

| ADR | Action | Notes |
|-----|--------|-------|
| **ADR-0043** | ✅ REBALANCED | Refactored to own EXECUTION only (L1/L2/L3, sessions, fragments). Artifact model moved to ADR-0048. |
| **ADR-0010** | ✅ REALIGNED | "Tier 0" → "SHAPE pillar" terminology per UAM. |

### Standard Migration (Add source_discussion)

All 33 orphan ADRs need `source_discussion` field. Options:
1. **Retroactive DISC**: Create shell DISCs for groups of related ADRs
2. **Pre-UAM marker**: Add `source_discussion: "pre-uam"` with note
3. **Individual review**: Examine each for multiple concerns (violates "One Thing" rule)

**Orphan ADR List (for PLAN execution)**:

```text
CORE DOMAIN (25):
- ADR-0001_guided-workflow-fsm-orchestration
- ADR-0005_deterministic-content-addressed-ids
- ADR-0007_swagger-driven-e2e-validation
- ADR-0009_audit-trail-timestamps
- ADR-0010_type-safety-contract-discipline
- ADR-0011_docs-as-code-engineering-tenets
- ADR-0013_cross-platform-concurrency
- ADR-0017_hybrid-semver-contract-versioning
- ADR-0018_cross-cutting-guardrails
- ADR-0026_dataset-lineage-tracking
- ADR-0027_pipeline-error-handling
- ADR-0029_unified-rendering-engine
- ADR-0030_api-versioning-and-endpoint-naming
- ADR-0031_documentation-lifecycle-management
- ADR-0032_http-error-response-contracts
- ADR-0033_http-request-idempotency-semantics
- ADR-0034_ai-assisted-development-patterns
- ADR-0035_automated-documentation-pipeline
- ADR-0036_contract-driven-test-generation
- ADR-0037_observability-and-debugging-first
- ADR-0038_single-command-development-environment
- ADR-0039_ci-cd-pipeline-for-data-and-code
- ADR-0040_deployment-automation
- ADR-0043_ai-development-workflow (PARTIAL SUPERSEDE)
- ADR-0044_frontend-iframe-integration-pattern

DAT DOMAIN (8):
- ADR-0003_stage-graph-configuration
- ADR-0004_optional-context-preview-stages
- ADR-0006_stage-id-configuration
- ADR-0008_table-availability
- ADR-0012_profile-driven-extraction-and-adapters
- ADR-0014_cancellation-semantics-parse-export
- (plus 2 more in .adrs/dat/)

DEVTOOLS DOMAIN (1):
- ADR-0028_devtools-page-architecture
```

### Examination Checklist (Per ADR)

During migration, check each ADR for:
- [ ] Multiple unrelated decisions (violates "One Thing" rule) → split
- [ ] Missing required fields per ADR-0048 schema → add
- [ ] References to superseded ADR-0016 tier model → update to Six Pillars
- [ ] Orphan SPECs or Contracts downstream → trace and link

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
