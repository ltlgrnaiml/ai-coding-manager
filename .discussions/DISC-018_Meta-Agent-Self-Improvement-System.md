# DISC-018: Meta-Agent Self-Improvement System

> **Status**: `deferred`
> **Created**: 2026-01-01
> **Updated**: 2026-01-01
> **Author**: USER + AI
> **AI Session**: SESSION_022
> **Depends On**: DISC-017
> **Blocks**: None
> **Dependency Level**: L2

> **Parent Discussion**: DISC-017 (Standalone DevTool Architecture)
> **Delegation Scope**: Agent self-improvement, swapping, and classification systems
> **Inherits Context**: `true`

---

## Summary

Design a system where **agents can improve, swap, and classify other agents**. This is a "much later" discussion per USER request, but captured now to preserve the vision.

**Core Concept**: Meta-level agent orchestration where:
- Agents evaluate other agents' performance
- Agents can swap in better-performing agents for specific tasks
- Agents classify and route work to specialized agents
- Continuous improvement loop based on quality metrics

---

## Context

### Background

As the AI Coding Management Hub (DISC-017) matures, we'll have:
- Multiple AI agents working on different tasks
- Quality scoring systems (DISC-013)
- Observability data (traces, prompts, responses)
- Performance metrics per agent/model

This creates the foundation for meta-agent systems that can:
- Analyze which agents perform best for which tasks
- Automatically route work to optimal agents
- Improve agent prompts based on performance data
- Swap underperforming agents with better alternatives

### Trigger

USER quote: "Just wait till we get to the agents working to improve/swap/classify other agents!"

Tagged for later discussion but captured to preserve vision.

---

## Requirements

### Functional Requirements (Preliminary)

- [ ] **FR-1**: Agent Performance Tracker - metrics per agent per task type
- [ ] **FR-2**: Agent Classifier - categorize agents by strengths/weaknesses
- [ ] **FR-3**: Agent Router - route tasks to optimal agent based on classification
- [ ] **FR-4**: Agent Improver - suggest/apply prompt improvements based on performance
- [ ] **FR-5**: Agent Swapper - hot-swap agents when better alternatives available
- [ ] **FR-6**: Meta-Agent Orchestrator - coordinate all of the above

### Non-Functional Requirements (Preliminary)

- [ ] **NFR-1**: Must not create infinite loops (meta-agent improving itself)
- [ ] **NFR-2**: Human approval required for significant changes
- [ ] **NFR-3**: Full audit trail of all agent modifications
- [ ] **NFR-4**: Rollback capability for agent changes

---

## Constraints

- **C-1**: Must build on DISC-017 infrastructure first
- **C-2**: Requires quality scoring system (DISC-013) to be operational
- **C-3**: Requires observability data (LangFuse traces)
- **C-4**: Human-in-the-loop for critical decisions

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | What metrics define "agent performance"? | `open` | |
| Q-2 | How do we prevent runaway self-improvement? | `open` | |
| Q-3 | What's the minimum viable meta-agent? | `open` | |
| Q-4 | How do we handle agent versioning? | `open` | |
| Q-5 | Should improvements be automatic or human-approved? | `open` | |

---

## Options Considered

*To be explored when this discussion is activated.*

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Activation timeline | `deferred` | After DISC-017 complete |
| D-2 | Scope of meta-agent capabilities | `pending` | |
| D-3 | Human-in-the-loop requirements | `pending` | |

---

## Scope Definition

### In Scope (When Activated)

- Agent performance tracking
- Agent classification/categorization
- Task routing optimization
- Prompt improvement suggestions
- Agent hot-swapping

### Out of Scope

- Fully autonomous self-modification (always human-in-loop)
- Hardware/infrastructure optimization
- Cost optimization (separate concern)

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-017 | `FS` | `active` | All | Must have DevTool Hub first |
| DISC-013 | `FS` | `resolved` | Performance metrics | Quality scoring required |
| DISC-006 | `soft` | `active` | Context retrieval | Knowledge archive for agent memory |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | TBD | Meta-Agent Architecture | `deferred` |
| SPEC | TBD | Agent Performance Metrics | `deferred` |
| Contract | TBD | AgentPerformance, AgentClassification | `deferred` |
| Plan | TBD | Meta-Agent Implementation | `deferred` |

---

## Conversation Log

### 2026-01-01 - SESSION_022

**Topics Discussed**:
- USER mentioned "agents improving/swapping/classifying agents" as future vision
- Requested this be tagged for later discussion
- Created as deferred DISC to capture intent

**Key Insights**:
- This is the logical evolution of the AI Coding Management Hub
- Requires foundation work (DISC-017) to be complete first
- USER is excited about this direction ("I am having the most fun ever")

**Action Items**:
- [x] Create DISC-018 as placeholder
- [ ] Revisit after DISC-017 reaches MVP
- [ ] Research existing meta-agent frameworks (AutoGPT, AgentGPT, etc.)

---

## Resolution

**Resolution Date**: DEFERRED

**Outcome**: Captured for future exploration

**Next Steps**:
1. Complete DISC-017 (AI Coding Management Hub)
2. Implement quality scoring (DISC-013)
3. Gather observability data
4. Revisit this DISC when foundation is ready

---

## Quality Score

**Status**: `[DEFERRED - NOT SCORED]`

---

## References (For Future Research)

- AutoGPT - recursive self-improvement attempts
- BabyAGI - task-driven autonomous agents
- AgentGPT - web-based agent orchestration
- LangChain Agents - tool-using LLM agents
- CrewAI - multi-agent collaboration
- [Xu-2025] A-Mem: Agentic Memory for LLM Agents (memory patterns)

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*

<!-- AI DEFERRED MARKER: This DISC is intentionally deferred per USER request.
     Activate when DISC-017 reaches MVP status. -->
