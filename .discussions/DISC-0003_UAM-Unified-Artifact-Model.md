# DISC-0003: UAM — Unified Artifact Model (Umbrella)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0001 (Genesis)
> **Delegation Scope**: Umbrella for all methodology pillars — UAM, AIKH, P2RE, Tap-In, and cross-cutting concerns
> **Inherits Context**: `true`

---

## Summary

The **Unified Artifact Model (UAM)** is AICM's Pillar 1 — the deterministic traceability system that ensures every line of code can be traced back to a human decision through a chain of artifacts. This DISC examines what's working, what needs enhancement, and what's missing for UAM to be production-ready.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 9/10 (strongest pillar)
- **What's Good**: Six pillars defined, Primary Chain Model
- **What's Great**: Lifecycle states, quality scoring concept
- **Needs Enhancement**: CI validation
- **Missing**: Schema migration tools

---

## The Six Pillars (Established)

| Pillar | Artifact | Verb | Purpose | Lifecycle States |
| ------ | -------- | ---- | ------- | ---------------- |
| **EXPLORE** | DISC | Explore | Capture design conversation | `draft` → `active` → `resolved` |
| **DECIDE** | ADR | Decide | Record architectural WHY | `draft` → `accepted` → `superseded` |
| **DEFINE** | SPEC | Define | Specify behavioral WHAT | `draft` → `active` → `superseded` |
| **SHAPE** | Contract | Shape | Define data HOW | `active` → `deprecated` |
| **EXECUTE** | PLAN | Execute | Track implementation work | `draft` → `active` → `completed` |
| **GUIDE** | Guide | Guide | Document for production | `draft` → `active` → `deprecated` |

---

## Chain of Thought: What Makes UAM Work?

### Level 1: The Primary Chain

```text
Chat Log → DISC → ADR → SPEC → Contract → PLAN → Code
    │        │       │       │        │        │
    │        │       │       │        │        └── Implementation
    │        │       │       │        └── Data shapes
    │        │       │       └── Behavior specification
    │        │       └── Architectural decision
    │        └── Refined problem
    └── Raw conversation (source of truth)
```

### Level 2: Traceability Rules

Every artifact has:

1. **`source_*`** — Points to parent artifact (required)
2. **`resulting_artifacts[]`** — Points to children (populated as created)
3. **`related[]`** — Secondary connections (non-chain)
4. **`provenance`** — Evidence chain with confidence scores (auto-generated)

### Level 3: Skip Mechanism

Not all chains need every tier:

| Scenario | Skip Pattern | Rationale |
| -------- | ------------ | --------- |
| Minor fix | DISC → PLAN | No architectural change |
| Behavior change | DISC → SPEC | Existing ADR covers it |
| New feature | Full chain | Novel decision required |

---

## Multi-Signal Context Matching Architecture

A **core differentiator** of AICM is the ability to automatically discover and score relationships between artifacts using multi-signal matching. This is not simple keyword search — it's intelligent context correlation.

### What is an Embedding?

An **embedding** converts text into a **768-dimensional vector** where semantically similar content clusters together in "math space." This enables finding conceptually related documents even without shared keywords.

```text
"DISC workflow orchestration"  →  [0.23, -0.45, 0.67, ...]  ─┐
                                                              ├─ Close! (high similarity)
"Umbrella DISC management"     →  [0.21, -0.43, 0.69, ...]  ─┘

"Recipe for banana bread"      →  [-0.78, 0.32, -0.11, ...] ← Far away (low similarity)
```

### Multi-Signal Scoring Formula

Final confidence = weighted combination of **5 independent signals**:

| Signal | Weight | Source | Captures |
| ------ | ------ | ------ | -------- |
| **Semantic** | 50% | Embedding cosine similarity | Conceptual relevance |
| **Keyword** | 20% | Explicit keywords/tags field | Domain terminology |
| **Lexical** | 15% | Direct term overlap in content | Exact phrase matches |
| **Venue** | 10% | Publication source (papers) | Field credibility |
| **Author** | 5% | Author chain tracking | Academic provenance |

### GPU Acceleration (Apple Silicon)

Embedding generation uses **matrix multiplication** on large tensors — exactly what GPUs excel at:

| Device | Speed | Notes |
| ------ | ----- | ----- |
| CPU | ~50 texts/sec | Sequential, general-purpose |
| Apple MPS (M4 Max) | ~500+ texts/sec | Parallel on unified GPU |
| CUDA (RTX 5090) | ~1000+ texts/sec | Dedicated tensor cores |

### AIKH Database Architecture

| Database | Content | Embedding Coverage |
| -------- | ------- | ------------------ |
| `research.db` | 87 papers, 8762 chunks | ✅ Paper + chunk embeddings |
| `chatlogs.db` | 49 logs, 2190 turns | ✅ Turn + log-level embeddings |
| `artifacts.db` | 44 docs + 95 archived | ✅ Chunk embeddings |

### Implementation Status

- [x] Multi-signal scoring for research papers (semantic, keyword, lexical, venue, author)
- [x] Semantic search for chat logs with turn-level granularity
- [x] Archived artifacts table with embeddings
- [x] GPU-accelerated embedding generation (MPS)
- [x] Provenance YAML + context markdown generation
- [ ] Author chain tracking (placeholder)
- [ ] Citation graph integration
- [ ] Real-time incremental indexing

---

## Assessment: What's Good

### ✅ Six Pillars (EXCELLENT)

- Clear mental model (one artifact per pillar)
- Purpose-driven naming (EXPLORE, DECIDE, DEFINE, etc.)
- Eliminates tier number confusion from old model

### ✅ Primary Chain Model (EXCELLENT)

- 1:1 upward relationship (every child has ONE parent)
- 1:N downward relationship (parent can have MANY children)
- Tree structure, not DAG (simpler reasoning)

### ✅ Lifecycle States (GOOD)

- Each artifact type has defined states
- Transitions are explicit
- Status visible in file headers

### ✅ Umbrella DISC Pattern (GOOD)

- Complex topics decompose into children
- Scope delegation with inheritance
- Prevents monolithic documents

---

## Assessment: What Needs Enhancement

### 🟡 Schema Validation (INCOMPLETE)

**Current State**: Pydantic schemas exist but CI doesn't enforce them.

**Enhancement Needed**:

- [ ] CI job that validates all artifacts on PR
- [ ] Pre-commit hook for local validation
- [ ] Error messages with fix suggestions

**Proposed Validation Flow**:

```text
git commit
    │
    ▼
pre-commit hook
    │
    ├── Validate DISC schema
    ├── Validate ADR schema
    ├── Validate link integrity
    └── Check lifecycle constraints
    │
    ▼
PASS → commit proceeds
FAIL → block with helpful message
```

### 🟡 Quality Scoring Integration (STUB)

**Current State**: Rubrics defined in archived DISC-013 but not implemented.

**Enhancement Needed**:

- [ ] Connect scoring to artifact creation
- [ ] Automated scoring on save
- [ ] Quality trend tracking

### 🟡 Cross-Reference Validation (PARTIAL)

**Current State**: Links exist in files but not validated.

**Enhancement Needed**:

- [ ] Validate `source_*` references exist
- [ ] Validate `resulting_artifacts` are consistent
- [ ] Detect orphaned artifacts

---

## Assessment: What's Missing

### 🔴 Schema Migration Tools (MISSING)

**Problem**: As schemas evolve, existing artifacts become invalid.

**Needed**:

- Migration scripts for schema changes
- Version field in each artifact
- Backward compatibility policy

**Proposed Solution**:

```python
# migrations/disc_v1_to_v2.py
def migrate(artifact: dict) -> dict:
    """Migrate DISC from v1 to v2 schema."""
    artifact['schema_version'] = '2.0'
    artifact['source_chat'] = artifact.pop('trigger_chat', None)
    return artifact
```

### 🔴 Artifact Graph Builder (INCOMPLETE)

**Problem**: Visualization exists but edge extraction is broken.

**Needed**:

- Fix Python contract parsing
- Extract links from all artifact types
- Real-time graph updates

### 🔴 DevTools Integration (MISSING)

**Problem**: No UI for artifact management.

**Needed**:

- Artifact creation wizard
- Link suggestion based on content
- Scope smell detection (>3 children warning)

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
| -- | -------- | ------ | --------------- |
| Q-1 | Should artifacts be JSON or Markdown? | `open` | Markdown for readability, JSON frontmatter for schema |
| Q-2 | How to handle artifact deletion? | `open` | Soft delete with `status: archived` |
| Q-3 | What's the validation strategy for links? | `open` | Pre-commit + CI with link checker |
| Q-4 | How to version schemas? | `open` | SemVer in schema, migration scripts |
| Q-5 | Should we enforce naming conventions? | `open` | Yes: `{TYPE}-{NNNN}_{Slug}.md` |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
| ------ | ----- | ----- |
| ADR-0001 | Unified Artifact Model Adoption | Adopts UAM as the standard |
| ADR-0002 | Artifact Schema Versioning | Migration strategy |
| ADR-0003 | Link Validation Requirements | CI/pre-commit rules |

---

## Implementation Priorities

### P1: CI Validation (Week 1)

- [ ] Create `scripts/validate_artifacts.py`
- [ ] Add to GitHub Actions workflow
- [ ] Test with existing artifacts

### P2: Pre-commit Hooks (Week 2)

- [ ] Install pre-commit framework
- [ ] Create local validation hook
- [ ] Document developer setup

### P3: Schema Migration (Week 3)

- [ ] Define migration file format
- [ ] Create v0 → v1 migration for archived artifacts
- [ ] Test migration round-trip

---

## Dependencies

| Dependency | Type | Status | Notes |
| ---------- | ---- | ------ | ----- |
| DISC-0004 (AIKH) | `child` | `active` | AI Knowledge Hub |
| DISC-0005 (P2RE) | `child` | `active` | Prompt-to-Response Evaluator |
| DISC-0006 (Tap-In) | `child` | `active` | Session continuity |
| DISC-0007 (Quality) | `child` | `active` | Quality scoring system |
| DISC-0008 (Artifact Gen) | `child` | `active` | Generation pipelines |
| DISC-0009 (AI Chat) | `child` | `active` | Chat integration |
| DISC-0010 (SPLAN) | `child` | `active` | Super-Plan orchestration |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:

- Deep analysis of UAM pillar strengths and gaps
- Schema validation strategy identified as priority
- Migration tools needed for schema evolution
- Three ADRs proposed for core decisions

**Key Insights**:
- UAM is conceptually strong (9/10) but needs tooling
- CI validation is the quickest win
- Schema versioning prevents technical debt

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for UAM adoption, schema versioning, validation)

---

*DISC-0003 | UAM Umbrella | Child of DISC-0001 | SESSION_0017*
