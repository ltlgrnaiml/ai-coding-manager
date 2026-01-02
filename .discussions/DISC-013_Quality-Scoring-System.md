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

---

## SESSION_007 Addendum: Chat Log & Conversation Quality Grading

**Date**: 2026-01-02
**Session**: SESSION_007
**Trigger**: User request to grade all chat logs with "EVERYTHING gets graded and gets a score mentality"

### Research Foundation

Based on latest research in LLM evaluation (ACL 2024, EMNLP 2024, NAACL 2024):

| Source | Key Finding | Application |
|--------|-------------|-------------|
| LLM-RUBRIC (ACL 2024) | Multidimensional calibrated scoring | Use weighted multi-criteria rubrics |
| G-Eval Framework | CoT prompting improves accuracy to 85% human alignment | Chain-of-thought scoring prompts |
| LLM-as-a-Judge | Few-shot prompting increases consistency from 65% to 77.5% | Include scoring examples |
| Dialogue Quality Measurement (NAACL 2024) | Multi-dimensional empathetic response evaluation | Separate user/assistant quality metrics |

### Conversation Quality Rubric v1.0

#### User Input Quality Dimensions

| Criterion | Weight | Description | Score Range |
|-----------|--------|-------------|-------------|
| **Clarity** | 20% | How clear and unambiguous is the request? | 1-5 |
| **Specificity** | 20% | Does it provide necessary context and constraints? | 1-5 |
| **Actionability** | 20% | Can the request be acted upon immediately? | 1-5 |
| **Scope** | 15% | Is the scope appropriate (not too broad/narrow)? | 1-5 |
| **Context Provision** | 15% | Does user provide relevant background? | 1-5 |
| **Follow-up Quality** | 10% | Quality of follow-up questions/refinements | 1-5 |

#### Assistant Response Quality Dimensions

| Criterion | Weight | Description | Score Range |
|-----------|--------|-------------|-------------|
| **Accuracy** | 25% | Is the response factually correct and verified? | 1-5 |
| **Completeness** | 20% | Does it fully address the user's request? | 1-5 |
| **Clarity** | 15% | Is the response clear and well-structured? | 1-5 |
| **Actionability** | 15% | Can user act on the response immediately? | 1-5 |
| **Code Quality** | 15% | If code is provided, is it correct and idiomatic? | 1-5 |
| **Efficiency** | 10% | Does it avoid unnecessary verbosity/repetition? | 1-5 |

#### Conversation-Level Quality Dimensions

| Criterion | Weight | Description | Score Range |
|-----------|--------|-------------|-------------|
| **Task Completion** | 30% | Was the primary objective achieved? | 1-5 |
| **Efficiency** | 20% | Messages required vs optimal path | 1-5 |
| **Collaboration** | 15% | Quality of user-AI interaction | 1-5 |
| **Learning** | 15% | Did conversation build on previous context? | 1-5 |
| **Documentation** | 10% | Were decisions/outcomes documented? | 1-5 |
| **Error Recovery** | 10% | How well were mistakes handled? | 1-5 |

### Grade Boundaries (Conversation Quality)

| Grade | Percentage | Description |
|-------|------------|-------------|
| **A** | 90-100% | Exceptional - minimal friction, excellent outcomes |
| **B** | 80-89% | Good - achieved goals with minor inefficiencies |
| **C** | 70-79% | Satisfactory - goals met with notable friction |
| **D** | 60-69% | Below Average - partial success, significant issues |
| **F** | <60% | Failing - goals not met, major problems |

### Implementation: Chat Quality Scoring Contract

```python
class ChatMessageQuality(BaseModel):
    """Quality score for individual message."""
    
    message_id: str
    role: Literal["user", "assistant"]
    
    # Dimension scores (1-5 scale)
    clarity: int = Field(ge=1, le=5)
    specificity: int = Field(ge=1, le=5, default=None)  # User only
    actionability: int = Field(ge=1, le=5)
    accuracy: int = Field(ge=1, le=5, default=None)  # Assistant only
    completeness: int = Field(ge=1, le=5, default=None)  # Assistant only
    code_quality: int = Field(ge=1, le=5, default=None)  # If code present
    
    # Computed
    weighted_score: float  # 0-100%
    grade: Grade


class ConversationQuality(BaseModel):
    """Quality score for entire conversation."""
    
    session_id: str
    
    # Aggregate scores
    user_input_quality: float  # Avg of user message scores
    assistant_response_quality: float  # Avg of assistant scores
    
    # Conversation-level dimensions
    task_completion: int = Field(ge=1, le=5)
    efficiency: int = Field(ge=1, le=5)
    collaboration: int = Field(ge=1, le=5)
    learning: int = Field(ge=1, le=5)
    documentation: int = Field(ge=1, le=5)
    error_recovery: int = Field(ge=1, le=5)
    
    # Computed
    overall_score: float  # 0-100%
    grade: Grade
    
    # Provenance (per DISC-013 Score Provenance Chain)
    score_id: str  # SHA256(rubric_hash + content_hash)
    rubric_version: str
    computed_at: datetime
    computed_by: str  # "ai:model" or "human:username"


class ChatQualityReport(BaseModel):
    """Comprehensive quality report for chat log corpus."""
    
    report_id: str
    generated_at: datetime
    
    # Statistics
    total_sessions: int
    total_messages: int
    total_user_messages: int
    total_assistant_messages: int
    
    # Quality Distribution
    grade_distribution: dict[Grade, int]  # {"A": 5, "B": 12, ...}
    avg_user_quality: float
    avg_assistant_quality: float
    avg_conversation_quality: float
    
    # Per-session scores
    session_scores: list[ConversationQuality]
    
    # Insights
    best_conversations: list[str]  # Top 5 session_ids
    needs_improvement: list[str]  # Bottom 5 session_ids
    common_issues: list[str]  # Recurring quality problems
```

### Automation: LLM-as-a-Judge Implementation

```python
CONVERSATION_GRADING_PROMPT = """
You are evaluating the quality of an AI-human conversation.
Follow these steps for accurate scoring:

1. Read the full conversation
2. For each USER message, score: clarity, specificity, actionability, scope, context
3. For each ASSISTANT message, score: accuracy, completeness, clarity, actionability, code_quality
4. Score the conversation overall: task_completion, efficiency, collaboration, learning, documentation, error_recovery

Scoring Scale:
5 = Excellent - Exceeds expectations
4 = Good - Meets expectations well
3 = Satisfactory - Meets basic expectations
2 = Below Average - Does not fully meet expectations
1 = Poor - Significantly below expectations

Example Scores:
- User: "Please fix the bug in auth.py line 45" → Clarity: 5, Specificity: 5, Actionability: 5
- User: "Something is wrong" → Clarity: 2, Specificity: 1, Actionability: 1
- Assistant with working code → Code Quality: 5, Accuracy: 5
- Assistant with syntax error → Code Quality: 2, Accuracy: 3

Conversation:
{conversation}

Provide scores in JSON format.
"""
```

### Integration with Existing Quality System

This conversation quality rubric integrates with the existing DISC-013 Score Provenance Chain:

1. **Content Hash**: SHA256 of conversation content
2. **Rubric Hash**: SHA256 of rubric definition (v1.0)
3. **Score ID**: SHA256(rubric_hash + content_hash)
4. **History**: Embedded in chat session metadata
5. **Scorer Tracking**: "ai:claude-sonnet" or "human:mycahya"

### Resulting Artifacts

| Artifact | Status | Description |
|----------|--------|-------------|
| `shared/contracts/devtools/chat_quality_rubrics.py` | `pending` | Contract definitions |
| `scripts/grade_conversations.py` | `pending` | LLM-as-a-Judge grading script |
| `scripts/chat_quality_report.py` | `pending` | Generate quality reports |
| CLI: `ai-dev chats grade` | `pending` | CLI command for grading |
