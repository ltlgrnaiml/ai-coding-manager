# ADRs Directory - AI Coding Guide

> **Scope**: Architecture Decision Records authoring and maintenance.

---

## What are ADRs?

ADRs (Architecture Decision Records) document the **WHY** behind architectural decisions.

**Tier Position**: Tier 1 (between Contracts and SPECs)

```text
Tier 0: Contracts (SSOT)     ← Data structures (Pydantic)
Tier 1: ADRs (WHY)           ← THIS DIRECTORY
Tier 2: SPECs (WHAT)         ← Implementation specs
Tier 3: Guides (HOW)         ← How-to guides
```

---

## Directory Structure

```text
.adrs/
├── INDEX.md              # ADR index (master list)
├── AGENTS.md             # AI instructions (this file)
├── ADR-XXXX_title.json   # Individual ADRs
└── .templates/
    └── ADR_TEMPLATE.json
```

---

## ADR Naming Convention

Format: `ADR-{NNNN}_{title-kebab-case}.json`

Examples:
- `ADR-0001_ai-development-workflow.json`
- `ADR-0002_knowledge-archive-rag-system.json`

---

## ADR Schema

All ADRs follow this structure:

```json
{
  "id": "ADR-0001",
  "title": "AI Development Workflow",
  "status": "active",
  "date": "2025-12-31",
  "context": {"description": "...", "problem": "..."},
  "decision": {"summary": "...", "details": {...}},
  "consequences": {"positive": [...], "negative": [...]},
  "guardrails": [{"id": "...", "rule": "..."}],
  "tags": ["workflow", "ai-assisted"]
}
```

---

## ADR Status Lifecycle

```text
draft → active → deprecated/superseded
```

| Status | Meaning |
|--------|---------|
| `draft` | Under discussion, not yet approved |
| `active` | Current and enforced |
| `deprecated` | No longer recommended |
| `superseded` | Replaced by newer ADR |

---

## Rules for ADR Content

1. **No code snippets** - ADRs explain WHY, not HOW
2. **Reference SPECs** - Use `implementation_specs` for the WHAT
3. **Reference Contracts** - Don't duplicate Pydantic models
4. **Keep focused** - One decision per ADR
5. **Document alternatives** - Show what was considered

---

## Creating a New ADR

1. Check `INDEX.md` for the next available ADR number
2. Create JSON file following the schema
3. Update `INDEX.md` with the new entry
4. Create corresponding SPEC if implementation details needed

---

## Core ADRs (Origin: engineering-tools)

| ID | Title | Original |
|----|-------|----------|
| ADR-0001 | AI Development Workflow | ADR-0043 |
| ADR-0002 | Knowledge Archive & RAG | ADR-0047 |
| ADR-0003 | AI-Assisted Dev Patterns | ADR-0034 |
| ADR-0004 | Observability & Debugging | ADR-0037 |
| ADR-0005 | Contract Discipline | ADR-0010 |
| ADR-0006 | 3-Tier Document Model | ADR-0016 |
