# DISC-017: AI Coding Management Hub (AICM)

> **Status**: `active`
> **Created**: 2026-01-01
> **Updated**: 2026-01-01
> **Author**: USER + AI
> **AI Session**: SESSION_022
> **Depends On**: DISC-011, DISC-015
> **Blocks**: None
> **Dependency Level**: L1

> **Parent Discussion**: DISC-011 (Unified Artifact Model - Grandparent Umbrella)
> **Delegation Scope**: Tooling and UI/UX for managing UAM artifacts with AI assistance
> **Inherits Context**: `true`

---

## Summary

Design the **AI Coding Management Hub (AICM)** - a web-based platform for:
1. **Managing UAM artifacts** (DISC, ADR, SPEC, Contract, PLAN, BUG, GUIDE) via workflow-driven UI
2. **AI-assisted development** with integrated chat, MCP tools, and full observability
3. **Self-propagating context** - "tap-in" to any project built with this tool and continue seamlessly

**Core Philosophy**: The USER monitors and evaluates AI output quality (traces, prompts, schema adherence) while AI does the heavy lifting. This is NOT an IDE extension - it's a dedicated management interface.

**Foundation**: The Unified Artifact Model (UAM) from DISC-011 provides the schema foundation. AICM is the **tooling layer** that makes UAM artifacts manageable and AI-accessible.

---

## Requirements

### Core UI (Two Main Tools)

- [ ] **FR-1**: Workflow Manager - artifact browser with sidebar, reader/editor split
- [ ] **FR-2**: AI Chat Window - integrated chat with MCP tool access, streaming responses
- [ ] **FR-3**: Observability Dashboard - LangChain/LangFuse/LangGraph trace viewer
- [ ] **FR-4**: Quality Evaluator - prompt quality, schema adherence, response evaluation

### Self-Propagating Context ("Tap-In")

- [ ] **FR-5**: Point UI at project folder → auto-load all artifacts → populate UI automatically
- [ ] **FR-6**: Any project built with AICM can be "tapped into" without re-ingesting
- [ ] **FR-7**: AI gets immediate context from previous sessions, no warmup cost
- [ ] **FR-8**: Export context as chunked prompts for external AI tools
- [ ] **FR-9**: Context API provides regimented access to artifacts, vectors, and session history

### Workflow Modes (Spectrum of AI Assistance)

- [ ] **FR-10**: **Manual Mode** - Human edits artifacts directly, no AI
- [ ] **FR-11**: **Prompt Gen Mode** - AI generates prompts for copy/paste to external tools
- [ ] **FR-12**: **Smart Link Mode** - Chat window linked to open workflow document, suggests improvements
- [ ] **FR-13**: **Section Improve Mode** - Review doc score → tweak AI prompt → choose better model for that section
- [ ] **FR-14**: **E2E Generation Mode** - Full AI document generation (single prompt, RAG, CoT+ToT, agentic)

### DISC-to-Workflow Pipeline

- [ ] **FR-15**: Generate DISC from chat discussion
- [ ] **FR-16**: Pass DISC to Agentic Workflows → auto-generate ADRs, SPECs, Contracts, PLANs
- [ ] **FR-17**: Workflow combinations are configurable and will evolve with industry

---

## Context Access API (Tap-In Protocol)

### What "Tap-In" Means

1. **Point UI at project folder** → AICM scans for UAM artifacts
2. **Auto-load all artifacts** → ADRs, SPECs, Contracts, Plans, DISCs, etc.
3. **Populate UI** → Sidebar shows artifact tree, reader shows content
4. **Chat has context** → AI can reference any loaded artifact
5. **Continue where you left off** → Previous session context is available

### API Layers (Proposed)

| Layer | Purpose | Access Pattern |
|-------|---------|----------------|
| **File Layer** | Raw UAM artifacts on disk | `.discussions/`, `.adrs/`, etc. |
| **Index Layer** | Artifact metadata + relationships | SQLite: `artifacts`, `edges` tables |
| **Vector Layer** | Semantic embeddings for RAG | SQLite: `embeddings` table (sqlite-vec) |
| **Session Layer** | Conversation history + checkpoints | SQLite: `sessions`, `messages` tables |
| **API Layer** | Unified access for AI tools | REST or MCP server |

### MCP Server Approach (Recommended for AI Integration)

```
- aicm_list_artifacts(type?, status?) → ArtifactSummary[]
- aicm_get_artifact(id) → ArtifactContent
- aicm_search_context(query, max_tokens?) → RAGContext
- aicm_get_session_history(session_id?) → SessionMessages[]
- aicm_create_disc(title, problem_statement) → DISC
- aicm_generate_artifact(disc_id, target_type, mode) → Artifact
```

---

## UAM as AICM Foundation

### The Relationship

```
DISC-011 (UAM) = Schema Foundation
    │
    ├── Six Pillars: EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE
    ├── Primary Chain Model: Every artifact has ONE parent
    ├── Lifecycle States: draft → active → resolved/superseded
    ├── Quality Scoring: Rubrics for artifact completeness
    └── CI Validation: Schema + link enforcement

DISC-017 (AICM) = Tooling Layer
    │
    ├── UI/UX for managing UAM artifacts
    ├── AI Chat for generating artifacts
    ├── Workflow Engine for artifact pipelines
    ├── Observability for AI quality monitoring
    └── Context API for "tap-in" capability
```

### What AICM Inherits from UAM

| UAM Concept | AICM Implementation |
|-------------|---------------------|
| Six Pillars | Artifact type tabs in UI |
| Primary Chain | Graph visualization, parent linking |
| DISC as entry point | Chat → DISC generation |
| Quality Scoring | Score display, improvement suggestions |
| Tier-skip mechanism | Workflow wizard with skip confirmation |
| Umbrella pattern | "Convert to Umbrella" action |

### What AICM Adds

| AICM Feature | Not in UAM |
|--------------|------------|
| AI Chat integration | UAM is schema-only |
| Prompt generation modes | UAM doesn't specify tooling |
| Observability dashboard | UAM doesn't specify monitoring |
| Context API / tap-in | UAM is file-based |
| Multi-project support | UAM is single-project |

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | What is the primary distribution format? | `leaning` | Python package + Web UI |
| Q-2 | Should the UI be web-based or desktop? | `answered` | Web-based (localhost), may package as Electron later |
| Q-3 | What is the context database format? | `answered` | SQLite + sqlite-vec |
| Q-4 | How does an external AI "tap in"? | `open` | See Context Access API section |
| Q-5 | Should this be a monorepo tool or project-agnostic? | `open` | Leaning project-agnostic with UAM as portable schema |
| Q-6 | How do we handle project-specific customizations? | `open` | |
| Q-7 | What is the Context Access API structure? | `open` | Needs dedicated exploration |
| Q-8 | How do we host this tool? | `open` | Feature-dependent |

---

## Migration Strategy

### From engineering-tools to ai-coding-manager

This AICM repo is a **new standalone repo** that will:
1. Receive migrated assets from engineering-tools (contracts, UI patterns, services)
2. Treat ALL migrated code as **100% fungible** - needs refactoring
3. Track every file with "needs_refactor" status
4. Require manual review for any file NOT modified during development

### High-Value Assets to Migrate

| Component | Source | Value |
|-----------|--------|-------|
| 33 Workflow Components | `apps/homepage/frontend/src/components/workflow/` | ⭐⭐⭐⭐⭐ |
| Knowledge Services (RAG) | `gateway/services/knowledge/` | ⭐⭐⭐⭐⭐ |
| Workflow Service | `gateway/services/workflow_service.py` | ⭐⭐⭐⭐ |
| DevTools Service | `gateway/services/devtools_service.py` | ⭐⭐⭐⭐ |
| LLM Service | `gateway/services/llm_service.py` | ⭐⭐⭐⭐ |

---

## Conversation Log

### 2026-01-01 - SESSION_022

**Vision Captured**:

1. **Workflow Modes** (spectrum of AI assistance):
   - Manual human edits
   - AI Prompt generation for copy/paste
   - Smart link between chat and open workflow document
   - Section improvement (review score → tweak prompt → better model)
   - Full E2E AI generation (RAG, CoT+ToT, agentic workflows)

2. **DISC-to-Workflow Pipeline**:
   - Chat discussion → Generate DISC
   - DISC → Agentic Workflows → Auto-generate downstream artifacts
   
3. **Continuous Evolution**:
   - Workflow combinations are infinite
   - Will evolve based on industry norms
   - "Tap-in" enables adapting tool continuously

4. **AICM Name**: AI Coding Management (adopted short name)

---

*Migrated from engineering-tools on 2026-01-01*
