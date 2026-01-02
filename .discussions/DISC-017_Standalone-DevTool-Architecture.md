# DISC-017: AI Coding Management Hub (AICM)

> **Status**: `active`
> **Created**: 2026-01-01
> **Updated**: 2026-01-01
> **Author**: USER + AI
> **AI Session**: SESSION_022
> **Depends On**: DISC-011, DISC-015, DISC-016
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

## Context

### Background

We have been building an extensive documentation strategy through:
- **DISC-011**: Unified Artifact Model (UAM) - the grandparent umbrella
- **DISC-006**: Knowledge Archive RAG System (nested umbrella, adopted by DISC-011)
- **DISC-015**: AI-Native Documentation Architecture
- **DISC-016**: AI Context Prompt Generator

This work has produced contracts, ADRs, and specifications for:
- Artifact schemas (DISC, ADR, SPEC, PLAN, Contract)
- Quality scoring systems
- Semantic linking and chunking
- RAG-based context retrieval
- Prompt generation

**Current Problem**: All this tooling is embedded within the `engineering-tools` monorepo. There's no clear path for:
- Using this system in other projects
- Sharing the documentation infrastructure as a reusable tool
- Allowing external AI assistants to "tap into" a project's knowledge base

### Trigger

USER request: Need a **SOLID system** for documenting and developing code, with a **solid UI/UX** for managing documentation and code. Key requirements:
1. **Web UI** similar to existing DevTools Workflow page (which USER loves)
2. **Two core tools**: Workflow Manager + AI Chat Window
3. **AI Chat with MCP** and full tool access directly in the UI
4. **Not IDE-integrated** - USER doesn't code directly, monitors AI output
5. **Observability views**: LangChain, LangFuse, LangGraph traces
6. **Self-propagating**: Projects built with this tool can be "tapped into" later
7. **Edge-case tools**: Like AI Context Prompt Generator (DISC-016) for scenarios where direct code access isn't possible

---

## Requirements

### Functional Requirements

**Core UI (Two Main Tools)**:
- [ ] **FR-1**: Workflow Manager - artifact browser with sidebar, reader/editor split (like current DevToolsPage)
- [ ] **FR-2**: AI Chat Window - integrated chat with MCP tool access, streaming responses
- [ ] **FR-3**: Observability Dashboard - LangChain/LangFuse/LangGraph trace viewer
- [ ] **FR-4**: Quality Evaluator - prompt quality, schema adherence, response evaluation

**Self-Propagating Context ("Tap-In")**:
- [ ] **FR-5**: Point UI at project folder → auto-load all artifacts → populate UI automatically
- [ ] **FR-6**: Any project built with AICM can be "tapped into" without re-ingesting
- [ ] **FR-7**: AI gets immediate context from previous sessions, no warmup cost
- [ ] **FR-8**: Export context as chunked prompts for external AI tools (DISC-016)
- [ ] **FR-9**: Context API provides regimented access to artifacts, vectors, and session history

**Workflow Modes (Spectrum of AI Assistance)**:
- [ ] **FR-10**: **Manual Mode** - Human edits artifacts directly, no AI
- [ ] **FR-11**: **Prompt Gen Mode** - AI generates prompts for copy/paste to external tools
- [ ] **FR-12**: **Smart Link Mode** - Chat window linked to open workflow document, suggests improvements
- [ ] **FR-13**: **Section Improve Mode** - Review doc score → tweak AI prompt → choose better model for that section
- [ ] **FR-14**: **E2E Generation Mode** - Full AI document generation (single prompt, RAG, CoT+ToT, agentic)

**DISC-to-Workflow Pipeline**:
- [ ] **FR-15**: Generate DISC from chat discussion
- [ ] **FR-16**: Pass DISC to Agentic Workflows → auto-generate ADRs, SPECs, Contracts, PLANs
- [ ] **FR-17**: Workflow combinations are configurable and will evolve with industry

**Development Integration**:
- [ ] **FR-18**: AI integration at core: code, docs, CI pipeline all have hooks
- [ ] **FR-19**: Memory, context, prompt improvement workflows built-in
- [ ] **FR-20**: Scaffold new projects with full UAM documentation structure
- [ ] **FR-21**: Build OTHER projects using this tool (meta-tooling)

### Non-Functional Requirements

- [ ] **NFR-1**: Zero-config for basic usage (auto-detects project structure)
- [ ] **NFR-2**: UI renders in <2s on modern hardware
- [ ] **NFR-3**: Works offline for core features (LLM calls require network)
- [ ] **NFR-4**: Portable across Windows, macOS, Linux
- [ ] **NFR-5**: Clear extension API for custom artifact types
- [ ] **NFR-6**: Real-time streaming for AI responses
- [ ] **NFR-7**: Trace storage doesn't bloat over time (retention policies)

---

## Constraints

- **C-1**: Must not require users to restructure their existing codebase
- **C-2**: Must support existing UAM artifact schemas (no breaking changes)
- **C-3**: Must work without requiring a running backend server for core operations
- **C-4**: Database format must be human-readable (SQLite, JSON, or Markdown-based)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | What is the primary distribution format? | `leaning` | Python package + Web UI (Option A) |
| Q-2 | Should the UI be web-based or desktop? | `answered` | Web-based (localhost), may package as Electron later |
| Q-3 | What is the context database format? | `answered` | SQLite + sqlite-vec (already implemented in PLAN-002) |
| Q-4 | How does an external AI "tap in"? | `open` | See "Context Access API" section below |
| Q-5 | Should this be a monorepo tool or project-agnostic? | `open` | Leaning project-agnostic with UAM as portable schema |
| Q-6 | How do we handle project-specific customizations? | `open` | |
| Q-7 | What is the Context Access API structure? | `open` | Needs dedicated exploration - see below |
| Q-8 | How do we host this tool? | `open` | Feature-dependent, may need dedicated DISC |

---

## Options Considered

### Option A: Expand Current Stack (FastAPI + React + SQLite)

**Description**: Build on existing `engineering-tools` architecture. Expand DevToolsPage into full Management Hub. Add AI Chat component. MCP server for external AI integration.

**Pros**:
- **Fastest path** - leverages existing codebase (DevToolsPage, workflow service, knowledge archive)
- Already have: artifact CRUD, graph visualization, prompt generation, RAG
- React + TailwindCSS + Lucide already working well
- SQLite + embeddings already implemented (PLAN-002)

**Cons**:
- Python backend required for all deployments
- Web UI needs server process running

### Option B: Electron/Tauri Desktop App

**Description**: Package web UI as desktop app with embedded backend.

**Pros**:
- Single installable application
- No separate server process visible to user
- Can bundle Python runtime

**Cons**:
- Larger distribution size
- Platform-specific builds
- Electron memory overhead

### Option C: Full Rewrite (Rust + Tauri)

**Description**: Native performance, single binary.

**Pros**:
- Smallest binary, fastest startup
- No runtime dependencies

**Cons**:
- Massive rewrite effort
- Loses all existing Python tooling
- **Not recommended for solo-dev**

### Recommendation

**Option A** - Expand current stack. Rationale:
1. USER already loves the DevToolsPage UI
2. All backend infrastructure exists (knowledge archive, workflow service, LLM integration)
3. Fastest path to working product
4. Can always package as Electron later if needed

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Primary distribution format | `leaning` | Python package + Web UI (Option A) |
| D-2 | UI technology choice | `leaning` | React + TailwindCSS (existing stack) |
| D-3 | Context database format | `decided` | SQLite + sqlite-vec (already implemented) |
| D-4 | AI integration protocol | `leaning` | MCP Server for external AI tap-in |
| D-5 | Project structure | `pending` | Monorepo vs separate package | |

---

## Scope Definition

### In Scope

- Core DevTool architecture design
- Distribution strategy
- UI/UX requirements
- Context database design
- AI assistant integration protocol
- Project scaffolding/initialization

### Out of Scope

- Specific artifact schemas (covered by DISC-011, DISC-012, etc.)
- RAG implementation details (covered by DISC-006)
- Prompt generation logic (covered by DISC-016)
- Quality scoring algorithms (covered by DISC-013)

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-011 | `FF` | `active` | Schema definitions | UAM provides artifact schemas |
| DISC-006 | `FF` | `active` | RAG integration | Knowledge Archive provides context retrieval |
| DISC-015 | `soft` | `draft` | Semantic linking | AI-Native docs informs chunking |
| DISC-016 | `soft` | `draft` | Prompt export | Context generator informs AI integration |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-00XX | DevTool Distribution Architecture | `pending` |
| SPEC | SPEC-00XX | DevTool Core Behavior | `pending` |
| Contract | `shared/contracts/devtool/` | DevTool Contracts | `pending` |
| Plan | PLAN-00X | DevTool Implementation | `pending` |

---

## Conversation Log

### 2026-01-01 - SESSION_022

**Topics Discussed**:
- USER has invested heavily in documentation strategy (DISC-011 umbrella)
- Core need: Standalone DevTool that can be imported OR tap into existing context
- Non-negotiable: SOLID system + solid UI/UX

**Key Insights**:
- Current tooling is monorepo-embedded
- Need portability without sacrificing functionality
- AI integration ("tap-in") is a first-class requirement

**Action Items**:
- [x] ~~Discuss distribution format preferences~~ → Leaning Option A
- [x] ~~Discuss UI technology preferences~~ → Expand current React UI
- [ ] Define what "tap-in" means operationally

---

### 2026-01-01 - SESSION_022 (Continued)

**Refined Vision from USER**:

1. **UI/UX**: Similar to DevToolsPage (which USER loves). Two core tools:
   - **Workflow Manager**: Artifact browser, reader/editor split
   - **AI Chat Window**: MCP + full tool access in UI
   
2. **User Role**: USER monitors AI, doesn't code directly. Evaluates:
   - Trace quality (LangChain, LangFuse, LangGraph)
   - Prompt quality and schema adherence
   - Response evaluation

3. **Integrations**:
   - AI built into core of code, docs, CI - everything
   - Memory, context, prompt improvement as easy as possible
   - Self-propagating: "tap-in" to continue development without warmup
   - Edge-case tools (DISC-016 AI Context Prompt Generator)

4. **Meta-Tooling**: This project helps build OTHER projects

5. **Future**: Agents improving/swapping/classifying agents → **DISC-018** (tagged for later)

**Key Quote**: "I am having the most fun ever FYI"

**Action Items**:
- [x] Define "tap-in" protocol → Context Access API section above
- [ ] Decide: spawn DISC-019 (Context API) as child?
- [ ] Decide: spawn DISC-020 (Chat Component) as child?
- [ ] Decide: spawn DISC-021 (Hosting) as child?
- [ ] Design AI Chat component with MCP integration
- [ ] Plan observability dashboard (LangFuse integration)
- [x] Create DISC-018 for meta-agent system (deferred) ✓

**USER Vision Captured**:

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

4. **AICM Name**: AI Coding Management (proposed short name)

---

## Context Access API (Tap-In Protocol)

This section explores how external AI assistants (or the built-in chat) access project context.

### What "Tap-In" Means (Refined)

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

If we expose AICM as an MCP server, AI assistants can call tools like:

```
- aicm_list_artifacts(type?, status?) → ArtifactSummary[]
- aicm_get_artifact(id) → ArtifactContent
- aicm_search_context(query, max_tokens?) → RAGContext
- aicm_get_session_history(session_id?) → SessionMessages[]
- aicm_create_disc(title, problem_statement) → DISC
- aicm_generate_artifact(disc_id, target_type, mode) → Artifact
```

### REST API Approach (For Web UI)

The web UI would use REST endpoints (already partially implemented in `devtools_service.py`):

```
GET  /api/aicm/artifacts
GET  /api/aicm/artifacts/{id}
GET  /api/aicm/artifacts/{id}/prompt?target_type=spec
POST /api/aicm/artifacts
PUT  /api/aicm/artifacts/{id}
GET  /api/aicm/context/search?query=...
GET  /api/aicm/sessions
POST /api/aicm/chat
```

### Open Question: Dedicated DISC for Context API?

This API design may warrant its own DISC (DISC-019?) to fully specify:
- Endpoint contracts
- Authentication/authorization (local vs remote)
- Rate limiting for LLM calls
- Caching strategies
- Vector index management

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
|-------------|--------------------|
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

## Recommended New DISCs

Based on this discussion's scope, I recommend spawning:

| Proposed DISC | Scope | Rationale |
|---------------|-------|----------|
| **DISC-019**: Context Access API | Endpoint design, auth, caching | Q-7 needs deep exploration |
| **DISC-020**: AICM Chat Component | Chat UI, MCP integration, streaming | FR-2 is complex enough for own DISC |
| **DISC-021**: Hosting & Deployment | Local vs cloud, packaging | Q-8 is feature-dependent |

**Note**: These should be children of DISC-017 if we convert to umbrella, OR siblings if scope remains focused.

---

## Resolution

**Resolution Date**: {YYYY-MM-DD}

**Outcome**: {Summary of what was decided/created}

**Next Steps**:
1. {Step 1}
2. {Step 2}

---

## Quality Score

**Status**: `[PENDING]` - Score calculated after required fields populated

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model) | See `.discussions/README.md` for usage instructions*
