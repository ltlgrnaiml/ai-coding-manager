# ADR Index: AI Dev Orchestrator

> Architecture Decision Records for the AI-assisted development framework.
> 
> **Origin**: Core ADRs extracted and adapted from engineering-tools (2025-12-31).

## Core ADRs

| ID | Title | Status | Origin |
|----|-------|--------|--------|
| ADR-0001 | AI Development Workflow Orchestration | Active | eng-tools ADR-0043 |
| ADR-0002 | Knowledge Archive & RAG System | Active | eng-tools ADR-0047 |
| ADR-0003 | AI-Assisted Development Patterns | Active | eng-tools ADR-0034 |
| ADR-0004 | Observability & Debugging First | Active | eng-tools ADR-0037 |
| ADR-0005 | Type-Safety & Contract Discipline | Active | eng-tools ADR-0010 |
| ADR-0006 | 3-Tier Document Model | Active | eng-tools ADR-0016 |
| ADR-0049 | Code Attribution & Intellectual Property Policy | Active | SESSION_011 |

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
