# DISC-0010: SPLAN — Super-Plan Orchestration System

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `The Rainstorm Workflow Session`
> **Session**: SESSION_0018
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: Git branching strategy, parallel workstream coordination, integration gates, SPLAN artifact definition

---

## Summary

**SPLAN (Super-Plan)** is a meta-orchestration artifact that coordinates multiple parallel PLANs within a single family of artifacts. When building complex systems like AI Coding Manager in-place, multiple workstreams must proceed in parallel while maintaining integration points and shared prerequisites.

**One SPLAN per artifact family.** A "family" is defined as all artifacts spawned from a single Umbrella DISC hierarchy.

---

## Problem Statement

**How do we coordinate parallel development of a complex system while maintaining a working product at each step?**

The in-place build strategy (DISC-0001 Addendum A) requires:

1. Multiple features developed simultaneously
2. Clear dependency ordering
3. Integration checkpoints
4. No broken states on main branch

Standard PLANs are linear. We need a **Super-Plan** to orchestrate the graph.

---

## Chain of Thought: What IS an SPLAN?

```text
PLAN = Linear sequence of tasks for one feature
     → Task 1 → Task 2 → Task 3 → Done

SPLAN = Directed acyclic graph of PLANs for one product initiative
      ┌─ PLAN-A ─────────────────────┐
      │                               │
      ├─ PLAN-B ───────┐              ├─ Integration ─→ Main
      │                │              │
      └─ PLAN-C ───────┴──────────────┘
```

### SPLAN Properties

| Property | Description |
|----------|-------------|
| **Scope** | One artifact family (rooted at Umbrella DISC) |
| **Uniqueness** | Exactly one SPLAN per family |
| **Contains** | References to child PLANs, not task details |
| **Tracks** | Dependencies, integration gates, branch strategy |

---

## Git Branching Strategy for In-Place Development

### Branch Structure

```text
main (protected)
│
├── develop (integration branch)
│   │
│   ├── feature/rainstorm-ui
│   │   └── commits...
│   │
│   ├── feature/splan-schema
│   │   └── commits...
│   │
│   ├── feature/workflow-builder
│   │   └── commits...
│   │
│   └── (merge back to develop when feature complete)
│
└── (develop merges to main after integration tests pass)
```

### Branch Rules

| Branch | Protection | Merge Requirements |
|--------|------------|-------------------|
| `main` | Protected | CI pass, integration tests, code review |
| `develop` | Semi-protected | Unit tests pass, no conflicts |
| `feature/*` | Open | Work in progress |
| `hotfix/*` | Fast-track | Critical fixes only, minimal review |

### Integration Gates

```text
Feature Complete
      │
      ▼
┌─────────────────┐
│  Unit Tests     │ ──✗──→ Fix in feature branch
└────────┬────────┘
         │ ✓
         ▼
┌─────────────────┐
│  Merge to       │
│  develop        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Integration    │ ──✗──→ Fix in develop
│  Tests          │
└────────┬────────┘
         │ ✓
         ▼
┌─────────────────┐
│  Merge to main  │
└─────────────────┘
```

---

## SPLAN Schema Draft

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETE = "complete"

@dataclass
class PlanReference:
    """Reference to a child PLAN within the SPLAN."""
    plan_id: str  # e.g., "PLAN-0010"
    title: str
    status: PlanStatus
    branch: str  # Git branch name
    depends_on: list[str]  # List of plan_ids this depends on
    blocks: list[str]  # List of plan_ids this blocks

@dataclass
class IntegrationGate:
    """Checkpoint where multiple PLANs must integrate."""
    gate_id: str
    name: str
    required_plans: list[str]
    validation: str  # Description of what must pass
    target_date: datetime | None

@dataclass
class SPLAN:
    """Super-Plan: Orchestrates multiple PLANs for a product initiative."""
    splan_id: str  # e.g., "SPLAN-0001"
    title: str
    umbrella_disc: str  # Root DISC this SPLAN serves
    
    # Child PLANs
    plans: list[PlanReference]
    
    # Integration points
    gates: list[IntegrationGate]
    
    # Git strategy
    main_branch: str = "main"
    integration_branch: str = "develop"
    
    # Metadata
    created: datetime
    updated: datetime
    status: PlanStatus
```

---

## SPLAN for AI Coding Manager Build

### SPLAN-0001: AI Coding Manager v1.0

**Umbrella**: DISC-0002 (AI Coding Manager Product Definition)

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    SPLAN-0001: AI Coding Manager v1.0               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PHASE 1: Foundation                                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │ PLAN-0010     │  │ PLAN-0011     │  │ PLAN-0012     │           │
│  │ SPLAN Schema  │  │ Rainstorm UI  │  │ Workflow      │           │
│  │ & Tooling     │  │ Entry Page    │  │ Builder Core  │           │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘           │
│          │                  │                  │                    │
│          └──────────────────┼──────────────────┘                    │
│                             │                                       │
│                             ▼                                       │
│                    ══════════════════                               │
│                    ║ GATE 1: UI MVP ║                               │
│                    ══════════════════                               │
│                             │                                       │
│  PHASE 2: Integration                                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │
│  │ PLAN-0013     │  │ PLAN-0014     │  │ PLAN-0015     │           │
│  │ Chat Window   │  │ Auto-Discovery│  │ Prompt        │           │
│  │ Integration   │  │ Engine        │  │ Generation    │           │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘           │
│          │                  │                  │                    │
│          └──────────────────┼──────────────────┘                    │
│                             │                                       │
│                             ▼                                       │
│                    ══════════════════                               │
│                    ║ GATE 2: E2E    ║                               │
│                    ══════════════════                               │
│                             │                                       │
│                             ▼                                       │
│                       [ RELEASE ]                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | Where does SPLAN file live? | `open` | `.plans/SPLAN-NNNN.md` |
| Q-2 | How to visualize SPLAN graph? | `open` | Mermaid in markdown + UI view |
| Q-3 | How to enforce gate requirements? | `open` | CI checks on develop→main |
| Q-4 | Can SPLAN be auto-generated? | `open` | Yes, from Umbrella DISC structure |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0022 | SPLAN Artifact Format | Schema, file location, lifecycle |
| ADR-0023 | Git Branching Strategy | Branch structure, protection rules |
| ADR-0024 | Integration Gate Requirements | CI/CD pipeline integration |

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0003 (UAM) | `parent` | `active` | Part of UAM methodology |
| DISC-0002 (Rainstorm) | `sibling` | `active` | Rainstorm may use SPLAN |

---

## Conversation Log

### 2026-01-03 - SESSION_0018

**Topics Discussed**:

- Need for parallel development coordination
- Git branching strategy for in-place builds
- SPLAN as one-per-family orchestrator
- Integration gates to ensure quality

**Key Insights**:

- Standard PLANs are linear; SPLAN is a DAG
- One SPLAN per artifact family prevents confusion
- Gates are the integration checkpoints

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for SPLAN format, git strategy, integration gates)

---

*DISC-0010 | Child of DISC-0003 | SESSION_0018*
