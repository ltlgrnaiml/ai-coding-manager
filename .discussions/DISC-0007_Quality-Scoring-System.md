# DISC-0007: Quality Scoring System (Cross-Cutting)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: Scoring rubrics, LLM-as-judge implementation, calibration, feedback loops
> **Inherits Context**: `true`

---

## Summary

The **Quality Scoring System** is a cross-cutting concern that spans all pillars. It enables automated evaluation of artifacts, prompts, and outputs — providing feedback loops for continuous improvement. Quality scores inform which artifacts are trustworthy and which need refinement.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 4/10
- **What's Good**: Rubrics conceptually defined
- **What's Great**: Clear value for improvement loops
- **Needs Enhancement**: Implementation
- **Missing**: LLM-as-judge integration

---

## What Gets Scored?

| Target | Scoring Method | Purpose |
|--------|----------------|---------|
| **DISCs** | Rubric-based | Ensure thorough exploration |
| **ADRs** | Rubric-based | Ensure clear decisions |
| **SPECs** | Rubric-based | Ensure complete behavior |
| **Prompts** | Output correlation | Identify effective prompts |
| **Responses** | User feedback + auto-eval | Train quality models |
| **Code** | Static analysis + tests | Ensure correctness |

---

## Scoring Approaches

### Approach 1: Rubric-Based (Artifacts)

```yaml
# Example DISC scoring rubric
disc_rubric:
  problem_statement:
    weight: 20
    criteria:
      - Clear problem definition (5)
      - Scope boundaries stated (5)
      - Success criteria defined (5)
      - Not duplicating other DISCs (5)
  
  context:
    weight: 15
    criteria:
      - Background provided (5)
      - Trigger identified (5)
      - Related work cited (5)
  
  exploration:
    weight: 25
    criteria:
      - Multiple options considered (10)
      - Pros/cons analyzed (10)
      - Recommendation justified (5)
  
  traceability:
    weight: 20
    criteria:
      - Source chat linked (10)
      - Resulting artifacts listed (10)
  
  completeness:
    weight: 20
    criteria:
      - All required sections filled (10)
      - Open questions resolved or deferred (5)
      - Resolution documented (5)
```

### Approach 2: LLM-as-Judge (Content Quality)

```python
async def score_with_llm(
    content: str,
    rubric: Rubric,
    judge_model: str = "claude-3-haiku-20240307"
) -> Score:
    """Use cheap LLM to evaluate against rubric."""
    
    prompt = f"""
    Evaluate the following content against this rubric:
    
    RUBRIC:
    {rubric.to_prompt()}
    
    CONTENT:
    {content}
    
    Score each criterion from 0-5 with brief justification.
    Output as JSON.
    """
    
    response = await llm.chat(
        messages=[{"role": "user", "content": prompt}],
        model=judge_model,
        max_tokens=500
    )
    
    return Score.from_json(response.content)
```

### Approach 3: User Feedback (Responses)

- Thumbs up/down on AI responses
- Implicit signals (copy, edit, retry)
- Explicit ratings (1-5 stars)

---

## Calibration Challenge

**Problem**: LLM judges can be biased or inconsistent.

**Solution**: Human-in-the-loop calibration

```
┌─────────────────────────────────────────────────────────────────┐
│                    CALIBRATION LOOP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Human scores sample artifacts                               │
│                       │                                         │
│                       ▼                                         │
│  2. LLM scores same artifacts                                   │
│                       │                                         │
│                       ▼                                         │
│  3. Compare human vs LLM scores                                 │
│                       │                                         │
│         ┌─────────────┴─────────────┐                          │
│         ▼                           ▼                           │
│    HIGH AGREEMENT            LOW AGREEMENT                      │
│    (use LLM judge)           (refine prompts)                   │
│                                                                 │
│  4. Periodic recalibration (monthly)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Considerations

| Judge Model | Cost per 1K tokens | Speed | Quality |
|-------------|-------------------|-------|---------|
| Claude 3.5 Sonnet | $3.00 / $15.00 | Fast | Excellent |
| Claude 3 Haiku | $0.25 / $1.25 | Fastest | Good |
| GPT-4o-mini | $0.15 / $0.60 | Fast | Good |
| Gemini Flash | $0.075 / $0.30 | Fastest | Good |

**Recommendation**: Use Haiku/Flash for routine scoring, Sonnet for calibration.

---

## Implementation Plan

### Phase 1: Rubric Definition

- [ ] Define DISC scoring rubric (YAML)
- [ ] Define ADR scoring rubric
- [ ] Define SPEC scoring rubric
- [ ] Create rubric validation

### Phase 2: LLM-as-Judge

- [ ] Implement `score_with_llm()` function
- [ ] Integrate with artifact save workflow
- [ ] Store scores in artifact metadata

### Phase 3: Calibration

- [ ] Build human scoring interface
- [ ] Implement comparison analysis
- [ ] Create prompt refinement workflow

### Phase 4: Feedback Loop

- [ ] Track score trends over time
- [ ] Surface low-scoring artifacts
- [ ] Suggest improvements

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | Which LLM for scoring? | `open` | Haiku/Flash for routine, Sonnet for calibration |
| Q-2 | When to score? | `open` | On save + periodic batch |
| Q-3 | Where to store scores? | `open` | Artifact metadata + scoring DB |
| Q-4 | Score threshold for "good"? | `open` | 70% = acceptable, 85% = good, 95% = excellent |
| Q-5 | How to handle score disagreement? | `open` | Human override + recalibration |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0013 | Quality Scoring Rubrics | Rubric definitions |
| ADR-0014 | LLM-as-Judge Integration | Scoring implementation |
| ADR-0015 | Calibration Protocol | Human-AI alignment |

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0003 (UAM) | `parent` | `active` | Scoring applies to UAM artifacts |
| DISC-0005 (P2RE) | `soft` | `pending` | Scores stored in traces |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:
- Rubric-based vs LLM-based scoring
- Calibration challenge and solution
- Cost optimization for high-volume scoring
- Integration with artifact workflow

**Key Insights**:
- Use cheap models for routine scoring
- Human calibration is essential
- Scores enable improvement feedback loops

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for rubrics, LLM-as-judge, calibration)

---

*DISC-0007 | Child of DISC-0003 | SESSION_0017*
