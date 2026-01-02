# SESSION_010: Research Agent System Discussion

> **Date**: 2026-01-02
> **Focus**: DISC-0021 - Automated Research Paper Agent System
> **Status**: `completed`

---

## Objectives

1. Create DISC-0021 for automated research paper agent system
2. Document initial architecture and requirements
3. Identify open questions for user input
4. **[Added]** Incorporate user answers and deep research

---

## Progress

- [x] Claimed SESSION_010
- [x] Created DISC-0021 with comprehensive discussion template
- [x] Documented multi-agent architecture proposal
- [x] Defined functional and non-functional requirements
- [x] Identified open questions and decision points
- [x] User answered all 6 open questions
- [x] Deep research: Relevance scoring (SPECTER2, Semantic Scholar metrics)
- [x] Deep research: Git branch policies (GitHub feature flags, branch protection)
- [x] Updated DISC-0021 with research findings

---

## Key Decisions Made

1. **Human-in-the-loop ALWAYS** with tiered step-down as trust improves
2. **xAI Grok** as initial LLM provider
3. **World citation rankings** for paper source prioritization
4. **Present all options** for conflicting recommendations, record feedback
5. **Git branch + feature flag policy** for safe upgrades
6. **SPECTER2 + citation metrics** for relevance scoring

---

## Research Findings Summary

### Relevance Scoring (Q-2)
- **SPECTER2** (Allen AI): State-of-the-art scientific paper embeddings
- **Semantic Scholar metrics**: Citation velocity, acceleration, influential citations
- Composite score combining citation metrics + embedding similarity + recency

### Safe Upgrade Policy (Q-6)
- **Branch protection**: Required PRs, approvals, status checks, linear history
- **Feature flags**: Instant rollback, gradual rollout, dark shipping
- **Trust levels**: Configurable autonomy based on change risk
- **Exclusion rules**: Protected paths, patterns, skip conditions

---

## Handoff Notes

DISC-0021 is **complete and active**. Next steps:
1. Draft ADR for Research Agent Architecture
2. Define Pydantic contracts for Paper, Insight, Recommendation
3. Prototype Discovery Agent with Semantic Scholar API
4. Design exclusion rules schema (`.aicm/upgrade-policy.yaml`)
5. Implement feature flag integration

---

*Session completed per AGENTS.md Rule 14*
