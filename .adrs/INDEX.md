# ADR Index: AI Dev Orchestrator

> Architecture Decision Records for the AI-assisted development framework.

## Core ADRs

| ID | Title | Status |
|----|-------|--------|
| ADR-0001 | AI Development Workflow Orchestration | Active |
| ADR-0002 | AI-Assisted Development Patterns | Active |
| ADR-0003 | 3-Tier Document Model | Active |
| ADR-0004 | Plan Granularity Levels (L1/L2/L3) | Active |
| ADR-0005 | Contract Discipline (Pydantic SSOT) | Active |

## ADR Structure

Each ADR answers the question: **"WHY did we make this decision?"**

```
.adrs/
├── INDEX.md           # This file
├── AGENTS.md          # AI instructions for ADRs
├── core/              # Core framework ADRs
│   └── ADR-XXXX.json
└── .templates/
    └── ADR_TEMPLATE.json
```

## Creating an ADR

ADRs are created when an architectural decision needs to be recorded:

1. Copy `.templates/ADR_TEMPLATE.json`
2. Fill in context, decision, consequences
3. Update this INDEX.md
4. Link from relevant SPECs

## ADR Lifecycle

```
draft → active → deprecated/superseded
```

- **Draft**: Under discussion
- **Active**: Current decision
- **Deprecated**: No longer relevant
- **Superseded**: Replaced by newer ADR
