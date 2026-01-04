# DISC-0008: Artifact Generation Pipelines (Cross-Cutting)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: DISC→ADR→SPEC→Contract→PLAN automation, prompt engineering, validation gates
> **Inherits Context**: `true`

---

## Summary

**Artifact Generation Pipelines** define how AI assists in creating UAM artifacts from conversations. This is the automation layer that transforms informal chat into formal, validated documentation — enabling the "methodology-as-software" promise.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 3/10
- **What's Good**: Chain concept clear
- **What's Great**: High value proposition
- **Needs Enhancement**: Prompt engineering
- **Missing**: Full implementation

---

## The Generation Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                 ARTIFACT GENERATION PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CHAT LOG                                                       │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────┐                                            │
│  │  DISC GENERATOR │ ◄── Extract problem, context, options      │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  VALIDATION     │ ◄── Schema check, quality score            │
│  │  GATE           │                                            │
│  └────────┬────────┘                                            │
│           │ ✓                                                   │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  ADR GENERATOR  │ ◄── Extract decision, rationale            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  VALIDATION     │                                            │
│  │  GATE           │                                            │
│  └────────┬────────┘                                            │
│           │ ✓                                                   │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │  SPEC GENERATOR │ ◄── Extract behavior, contracts            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           ▼                                                     │
│       (continues...)                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Generation Modes (Workflow Spectrum)

| Mode | Description | Human Involvement | Use Case |
|------|-------------|-------------------|----------|
| **Manual** | Human writes everything | 100% | Learning, sensitive decisions |
| **Prompt Gen** | AI suggests, human edits | 80% | Standard workflow |
| **Smart Link** | AI auto-links artifacts | 60% | High-volume work |
| **Section Improve** | AI enhances sections | 40% | Refinement |
| **E2E Generation** | AI generates full chain | 20% | Well-understood patterns |

---

## Prompt Engineering: DISC Generation

### Input Requirements
- Source chat log content
- User's explicit topic/problem
- Existing artifact context (if any)

### Prompt Template
```
You are an expert at extracting structured discussions from conversations.

TASK: Generate a DISC document from the following chat log.

CHAT LOG:
{chat_content}

USER TOPIC: {topic}

EXISTING CONTEXT:
{context}

Generate a DISC following this structure:
1. Summary (2-3 sentences)
2. Problem Statement (clear, scoped)
3. Context (background, trigger)
4. Requirements (functional, non-functional)
5. Options Considered (at least 2)
6. Open Questions (if any)

Output as valid Markdown with YAML frontmatter.
```

### Validation Criteria
- [ ] Has required sections
- [ ] Problem statement is specific
- [ ] At least 2 options considered
- [ ] Links back to source chat
- [ ] Quality score > 70%

---

## Prompt Engineering: ADR Generation

### Input Requirements
- Source DISC content
- Decision point identified
- Options with pros/cons

### Prompt Template
```
You are an expert at documenting architectural decisions.

TASK: Generate an ADR from the following DISC.

SOURCE DISC:
{disc_content}

DECISION POINT: {decision}

Generate an ADR following this structure:
1. Title (decision statement)
2. Status (draft/accepted)
3. Context (why this decision)
4. Decision (what was decided)
5. Consequences (positive, negative, risks)

Output as valid Markdown.
```

---

## Validation Gates

### Gate 1: Schema Validation
```python
def validate_schema(artifact: dict, artifact_type: str) -> ValidationResult:
    """Validate artifact against Pydantic schema."""
    schema = get_schema(artifact_type)
    try:
        schema.model_validate(artifact)
        return ValidationResult(passed=True)
    except ValidationError as e:
        return ValidationResult(passed=False, errors=e.errors())
```

### Gate 2: Quality Scoring
```python
def validate_quality(artifact: str, min_score: float = 0.7) -> ValidationResult:
    """Ensure artifact meets quality threshold."""
    score = score_with_llm(artifact)
    if score.total >= min_score:
        return ValidationResult(passed=True, score=score)
    return ValidationResult(passed=False, score=score, suggestions=score.improvements)
```

### Gate 3: Link Integrity
```python
def validate_links(artifact: dict) -> ValidationResult:
    """Ensure all referenced artifacts exist."""
    missing = []
    for link in extract_links(artifact):
        if not artifact_exists(link):
            missing.append(link)
    return ValidationResult(passed=len(missing) == 0, missing=missing)
```

---

## Human-in-the-Loop Workflows

### Review Before Commit
```
Generate → Preview → Edit → Approve → Commit
                ↑
                └── Reject → Regenerate
```

### Confidence Thresholds
| Confidence | Action |
|------------|--------|
| > 90% | Auto-commit with notification |
| 70-90% | Require human review |
| < 70% | Manual edit required |

---

## Implementation Priorities

### Phase 1: DISC Generation
- [ ] Implement DISC prompt template
- [ ] Create generation endpoint
- [ ] Add validation gate
- [ ] Test with real chat logs

### Phase 2: ADR Generation
- [ ] Implement ADR prompt template
- [ ] Chain from DISC
- [ ] Validate decision capture

### Phase 3: Full Chain
- [ ] SPEC generation
- [ ] Contract generation (code)
- [ ] PLAN generation
- [ ] End-to-end tests

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | Which model for generation? | `open` | Sonnet for quality, Haiku for drafts |
| Q-2 | Auto-commit threshold? | `open` | 90% confidence + quality > 85% |
| Q-3 | How to handle generation failures? | `open` | Retry with refined prompt, then manual |
| Q-4 | Prompt versioning? | `open` | Store in `/prompts/` with semver |
| Q-5 | How to measure generation quality? | `open` | Human-AI comparison studies |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0016 | Artifact Generation Architecture | Pipeline design |
| ADR-0017 | Prompt Template Management | Versioning, testing |
| ADR-0018 | Validation Gate Requirements | Gates and thresholds |

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0003 (UAM) | `parent` | `active` | Generates UAM artifacts |
| DISC-0007 (Quality) | `hard` | `pending` | Quality gates use scoring |
| DISC-0009 (AI Chat) | `soft` | `pending` | Generation triggered from chat |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:
- Generation chain from chat to code
- Workflow spectrum (Manual → E2E)
- Validation gates at each step
- Human-in-the-loop workflows

**Key Insights**:
- Confidence thresholds determine automation level
- Quality scoring is prerequisite for auto-commit
- Prompt engineering is the critical success factor

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for generation architecture, prompts, validation)

---

*DISC-0008 | Child of DISC-0003 | SESSION_0017*
