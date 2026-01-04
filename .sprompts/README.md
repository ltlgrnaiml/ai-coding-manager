# SPROMPT — Super Prompts

> Part of: AI Coding Manager (AICM)

## What is an SPROMPT?

An **SPROMPT** (Super Prompt) is a comprehensive, self-contained prompt designed for **autonomous AI execution** of complex, multi-artifact development tasks.

Like SPLAN (Super Plan), SPROMPT is designed for large reasoning models capable of extended autonomous sessions.

## SPROMPT vs Regular Prompts

| Aspect | Regular Prompt | SPROMPT |
|--------|---------------|---------|
| **Scope** | Single task | Full artifact chain |
| **Context** | Minimal | Self-contained RAG |
| **Reasoning** | Implicit | Explicit CoT/ToT patterns |
| **Verification** | None | Gate checkpoints |
| **Duration** | Minutes | Hours |
| **Output** | Single artifact | Multiple artifacts + code |

## SPROMPT Structure (v1.1)

```
1. RAG CONTEXT           — Files to read first
2. ARTIFACT CHECKLIST    — 🆕 Required vs Optional items
3. CHAIN OF THOUGHT      — Problem decomposition
4. TREE OF THOUGHT       — Implementation paths
5. EXECUTION PLAN        — Phased task list
6. SPECIFICATIONS        — Types, APIs, props
7. VERIFICATION GATES    — Success criteria
8. VISUAL VERIFICATION   — 🆕 Screenshot/interaction evidence
9. FAILURE HANDLING      — Rollback strategies
10. ATTRIBUTION TRACKING — 🆕 AI vs Human contributions
11. OUTPUT FORMAT        — Expected deliverables
```

## v1.1 Enhancements (2026-01-03)

Based on SPROMPT-0001 execution analysis and meta-evaluation:

### Enhancement #1: Required vs Optional Artifact Checklist

**Problem**: Opus 4.1 created 11/14 artifacts but it was unclear which were critical.

**Solution**: Explicit checklist with completion thresholds:
- 🔴 **REQUIRED**: Must complete for passing grade
- 🟡 **OPTIONAL**: Bonus points, not blocking

### Enhancement #2: Visual Verification Protocol

**Problem**: Neither Opus 4.1 nor the grader actually tested the UI.

**Solution**: Mandatory visual evidence section:
- Screenshots or interaction descriptions
- Specific URLs and actions to test
- Evidence format for each UI gate

### Enhancement #3: Attribution Tracking

**Problem**: Grader's 94/100 score combined AI + human work.

**Solution**: Clear attribution reporting:
- "Completed by AI" list
- "Requires Human Completion" list
- Separate scores for accurate P2RE metrics

## When to Use SPROMPT

Use an SPROMPT when:

- Task spans multiple artifact types (DISC → ADR → SPEC → Code)
- Implementation requires architectural decisions
- Multiple components must integrate
- Verification is critical
- You want autonomous execution with minimal intervention

## Naming Convention

```
SPROMPT-NNNN_Brief-Description.md
```

## Current SPROMPTs

| ID | Title | Target | Status | Score |
|----|-------|--------|--------|-------|
| SPROMPT-0001 | The Rainstorm Implementation | DISC-0002 | `executed` | 85/100 (AI-only) |

## Templates

- `.templates/SPROMPT_TEMPLATE_v1.1.md` — Latest template with all enhancements

## Related DISCs

- **DISC-0011**: SPROMPT Execution Evaluation (grading rubric)
- **DISC-0012**: SPROMPT Meta-Evaluation (grading the grader)

---

*Created: 2026-01-03 | Updated: 2026-01-03 | Part of the P2RE ecosystem*
