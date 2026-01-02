# DISC-013: Quality Scoring System

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

Artifacts need objective quality metrics with real-time feedback during creation, displaying a percentage score that improves as fields are filled, with hover/click details for each criterion.

---

## Summary

Define the behavioral specification for how quality scores are calculated, displayed, and enforced across all artifact types (DISC, ADR, SPEC, CONTRACT, PLAN) within the DevTools workflow UI.

---

## Context

### Background

During DISC-011 (Umbrella: Unified Artifact Model), we created `quality_rubrics.py` which defines the **data shapes** for quality scoring:

- `CriterionScore`: Individual criterion with max_points, weight, is_required
- `ArtifactRubric`: Collection of criteria with computed percentage and grade
- `DISC_CRITERIA`, `ADR_CRITERIA`, etc.: Predefined criteria lists

However, the **behavioral questions** remain unanswered:

| Question | Status |
|----------|--------|
| When is score calculated? (real-time vs on-save) | `open` |
| What formula converts ScoreLevel → points? | `defined in contract` |
| How do weights affect total? | `defined in contract` |
| What triggers CI failure vs warning? | `open` |
| How does UI display scores? | `open` |

### Trigger

User suggested during DISC-011 that quality rubrics should be "baked into workflow evaluations" with "a %-score that improves or goes down based on the input" and "more info available on hover/click".

---

## Requirements

### Functional Requirements

> **⚠️ SHELL DOCUMENT**: Requirements below are placeholders. Actual requirements TBD during discussion.

- [ ] **FR-1**: Real-time score calculation as user fills fields
- [ ] **FR-2**: Percentage bar display with color gradient (red→yellow→green)
- [ ] **FR-3**: Letter grade display (A/B/C/D/F)
- [ ] **FR-4**: Hover tooltip showing individual criterion scores
- [ ] **FR-5**: Click-to-expand full rubric with improvement hints
- [ ] **FR-6**: CI integration for required criteria enforcement

### Non-Functional Requirements

> **⚠️ SHELL DOCUMENT**: NFRs below are placeholders.

- [ ] **NFR-1**: Score calculation must complete in <100ms for responsive UI
- [ ] **NFR-2**: Rubric display must be accessible (WCAG 2.1 AA)

---

## Scope

### In Scope

- Score calculation algorithm and timing
- UI display components (percentage bar, grade badge, tooltip, expanded view)
- CI validation integration
- API endpoints for scoring

### Out of Scope

- The rubric criteria themselves (already defined in `quality_rubrics.py`)
- DevTools UI framework choice (covered by ADR-0045)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should scoring happen on every keystroke or debounced? | `answered` | **Debounced (300ms)** - responsive without perf issues |
| Q-2 | Should CI block on grade < C, or just on required fields? | `answered` | **Block on required fields missing** - grade < C is warning only |
| Q-3 | Should scores be persisted or computed on-demand? | `answered` | **Hybrid with Score Provenance** - see extended discussion below |
| Q-4 | How should partial artifacts (mid-creation) display scores? | `answered` | **Live score with "incomplete" badge** until required fields filled |
| Q-5 | Should rubric changes auto-rescore all artifacts? | `answered` | **Yes, auto-rescore but LOG previous** - don't overwrite history |
| Q-6 | Where should score history be stored? | `answered` | **Embedded in artifact** for true provenance |
| Q-7 | Should we track WHO scored? | `answered` | **Yes** - enables AI vs human quality comparison |

---

## Options Considered

### Option A: Pure On-Demand (No Persistence)

**Pros**: SSOT, no sync issues  
**Cons**: Lose historical comparison, can't track improvement over time

### Option B: Persisted Scores (Separate Storage)

**Pros**: Full history, easy querying  
**Cons**: Sync issues, storage overhead, not true provenance

### Option C: Hybrid with Score Provenance Chain (SELECTED)

**Pros**:
- Computed on-demand (SSOT for current score)
- Embedded score history in artifact (true provenance)
- Content-addressed scoring enables AI experimentation
- Rubric versioning enables "rescore with new rubric" workflows

**Cons**:
- Slightly more complex implementation
- Artifact files grow with score history

---

## Decision

**Selected Option**: **Option C: Hybrid with Score Provenance Chain**

**Rationale**: 

1. **SSOT Principle**: Current score is always computed on-demand from current rubric + current content. No stale cached scores.

2. **Provenance for Experimentation**: By hashing rubric + content, we create verifiable score provenance that enables:
   - Comparing AI prompt effectiveness: "Prompt A produces 72% avg, Prompt B produces 86% avg"
   - Tracking rubric evolution: "Old rubric scored 85%, new stricter rubric scores 78%"
   - Validating scores: Given content + rubric, anyone can recompute and verify

3. **History Without Sync Issues**: Score history is embedded IN the artifact, not in a separate database. The artifact IS the audit log.

4. **Per ADR-0005**: Leverages existing content-addressed ID infrastructure (SHA-256).

---

## Extended Discussion: Score Provenance Chain

### The Core Concept

```text
┌─────────────────────────────────────────────────────────────┐
│                    SCORE PROVENANCE                         │
├─────────────────────────────────────────────────────────────┤
│  rubric_hash   = SHA256(rubric_definition)                  │
│  content_hash  = SHA256(artifact_scored_fields)             │
│  score_id      = SHA256(rubric_hash + content_hash)         │
│                                                             │
│  Result: Same rubric + same content = SAME score_id         │
│          (deterministic, verifiable, reproducible)          │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Hashed in the Rubric?

```python
rubric_hash = sha256({
    "version": "2025.12.01",
    "criteria": [...],  # The actual scoring rules
    "weights": {...},   # Point values
    "thresholds": {...} # Grade boundaries
})
```

**Key behavior**: If you tweak a weight from 4→5 points, `rubric_hash` changes → all scores are now "stale" and trigger auto-rescore.

### What Gets Hashed in the Content?

Only the **scored fields**, not metadata:

```python
content_hash = sha256({
    "problem_statement": "...",  # Scored
    "context": "...",            # Scored  
    "decision": "..."            # Scored
    # NOT: created_date, author, session_id (not scored)
})
```

### Rubric Evolution Behavior

When rubric changes (new `rubric_hash`):

1. **Auto-rescore**: All artifacts get rescored with new rubric
2. **Log previous**: Old score entry stays in `score_history[]`
3. **UI indication**: "Scored with rubric v2025.12.01 → v2025.12.02"
4. **Historical comparison**: "Was 85% on old rubric, now 78% on stricter rubric"

### Score History Embedding

Each artifact contains its score history:

```json
{
  "score_history": [
    {
      "score_id": "abc123...",
      "rubric_hash": "def456...",
      "rubric_version": "2025.12.01",
      "content_hash": "ghi789...",
      "raw_score": 28,
      "max_score": 32,
      "percentage": 87.5,
      "grade": "B",
      "computed_at": "2025-12-31T20:30:00Z",
      "computed_by": "ai:claude-sonnet-4",
      "superseded_by": "xyz999..."
    },
    {
      "score_id": "xyz999...",
      "rubric_hash": "new123...",
      "rubric_version": "2025.12.02",
      "content_hash": "ghi789...",
      "raw_score": 25,
      "max_score": 32,
      "percentage": 78.1,
      "grade": "C",
      "computed_at": "2025-12-31T21:00:00Z",
      "computed_by": "system",
      "superseded_by": null
    }
  ],
  "current_score": "xyz999..."
}
```

### AI Experimentation Use Case

This enables experiments like EXP-001 but for **content quality**:

```text
EXP-002: Which prompt produces better DISCs?

Prompt A: "Create a DISC for feature X"
Prompt B: "You are an architect. Create a DISC for feature X with clear requirements."

Results:
┌──────────┬───────────────┬─────────────┐
│ Prompt   │ Avg Score     │ Std Dev     │
├──────────┼───────────────┼─────────────┤
│ A        │ 72% (C)       │ 12%         │
│ B        │ 86% (B)       │ 5%          │ ← Less variation too!
└──────────┴───────────────┴─────────────┘
```

### Scorer Tracking

The `computed_by` field tracks WHO scored:

| Value | Meaning |
|-------|--------|
| `system` | Auto-computed on save/CI |
| `ai:claude-sonnet-4` | AI assistant during creation |
| `ai:grok-fast-1` | Different AI model |
| `human:mycahya` | Human review override |

This enables:
- "AI scored 85%, human disagreed → 72%" analysis
- Model comparison: "Sonnet produces higher self-scores than Haiku"
- Trust calibration: "AI scores correlate 0.87 with human scores"

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status | Skipped Tiers |
|---------------|----|-------|--------|---------------|
| Contract | `shared/contracts/devtools/quality_rubrics.py` | Quality Rubrics (v2025.12.01) | `active` | - |
| Contract | `shared/contracts/devtools/score_provenance.py` | Score Provenance Chain | `pending` | - |
| ADR Update | ADR-0048 | Add score provenance guardrails | `pending` | - |
| SPEC | `[TBD]` | Quality Scoring System Behavior | `pending` | - |

---

## Conversation Log

### 2025-12-31 - SESSION_021

**Topics Discussed**:
- User requested quality rubrics be integrated into workflow UI
- Created `quality_rubrics.py` contract with criteria definitions
- Identified need for SPEC to define behavioral aspects
- Created as child of DISC-011 umbrella

**Q-1 through Q-4 Answered**:
- Q-1: Debounced 300ms (AI recommendation accepted)
- Q-2: Block on required fields, warn on grade < C (AI recommendation accepted)
- Q-3: Extended discussion → Hybrid with Score Provenance Chain
- Q-4: Live score with "incomplete" badge (AI recommendation accepted)

**Q-3 Extended Discussion (The Fun Part!)**:

User asked: "It would be very useful for later experimentation to know what AI prompts returned better results, but we would need to version and somehow hash the results such that they could be validated to come from the specific grading rubric?"

This triggered exploration of **Score Provenance Chain** concept:
- Content-addressed scoring (per ADR-0005)
- Rubric versioning with hash
- Embedded score history for true provenance
- AI experimentation correlation

**Additional Questions Answered**:
- Q-5: Auto-rescore on rubric change, but LOG previous (don't overwrite)
- Q-6: Embedded in artifact for true provenance
- Q-7: Yes, track WHO scored (system/ai/human)

User quote: "These are the great details which make reviewing decisions later so rewarding!"

---

## Resolution

**Resolution Date**: 2025-12-31
**Resolution Type**: `design_complete`
**Outcome**: Hybrid scoring with Score Provenance Chain adopted. Enables content-addressed scoring for reproducibility, embedded history for true provenance, and AI experimentation correlation. Contract `score_provenance.py` to be created.

---

## Quality Score

**Status**: `COMPLETE` - Discussion held, decisions recorded with extended nuance.

---

## Proposed Contract: ScoreProvenance

```python
class ScoreProvenance(BaseModel):
    """Per ADR-0005: Content-addressed score provenance.
    
    Enables:
    - Reproducible scoring (same content + rubric = same score_id)
    - Rubric evolution tracking (rescore with new rubric, keep history)
    - AI experimentation (correlate prompt → quality)
    - Trust calibration (AI vs human score comparison)
    """
    
    score_id: str           # SHA256(rubric_hash + content_hash)
    rubric_hash: str        # SHA256 of rubric definition
    rubric_version: str     # Human-readable: "2025.12.01"
    content_hash: str       # SHA256 of scored fields only
    raw_score: int          # Points earned
    max_score: int          # Points possible
    percentage: float       # raw/max * 100
    grade: Grade            # A/B/C/D/F
    computed_at: datetime
    computed_by: str        # "system" | "ai:model-name" | "human:username"
    superseded_by: str | None  # score_id of newer score, if any


class ScoreHistory(BaseModel):
    """Embedded score history for artifact provenance."""
    
    score_history: list[ScoreProvenance] = []
    current_score: str | None  # score_id of latest
    
    def add_score(self, score: ScoreProvenance) -> None:
        """Add new score, mark previous as superseded."""
        if self.current_score:
            # Find and mark old score as superseded
            for s in self.score_history:
                if s.score_id == self.current_score:
                    s.superseded_by = score.score_id
        self.score_history.append(score)
        self.current_score = score.score_id
```

---

*This DISC was converted from shell to resolved during SESSION_021.*
