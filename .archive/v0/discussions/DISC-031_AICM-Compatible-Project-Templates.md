# DISC-031: AICM-Compatible Project Repository Templates

> **Status**: `active`
> **Created**: 2026-01-03
> **Updated**: 2026-01-03
> **Author**: Mycahya Eggleston
> **AI Session**: SESSION_017
> **Depends On**: DISC-011 (UAM), DISC-0022 (AIKH)
> **Blocks**: None
> **Dependency Level**: L0

---

## Summary

Define the **minimum viable structure** for any project repository to be AICM-compatible, enabling immediate integration with the **Unified Artifact Model (UAM)** and **AI Knowledge Hub (AIKH)**. This includes three architectural tiers based on project complexity: **Lite**, **Standard**, and **Agentic** — ensuring new projects start with the right scaffolding from day one.

---

## Context

### Background

Currently, starting a new AI-assisted project requires manually setting up:
- Session tracking (`.sessions/`)
- Discussion documents (`.discussions/`)
- ADR storage (`.adrs/`)
- AGENTS.md rules
- Question tracking (`.questions/`)

This is error-prone and wastes valuable context window re-explaining structure to AI assistants.

### Trigger

User request: *"It will be nice to be able to open a brand new project and have ALL our UAM and AIKH framework already in place from the very start!"*

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Define CORE minimum files required for ANY AICM-compatible repo
- [ ] **FR-2**: Define three architecture tiers (Lite, Standard, Agentic) with increasing capabilities
- [ ] **FR-3**: Each tier must be a superset of the previous (additive, not alternative)
- [ ] **FR-4**: Provide `aicm init <tier>` command or script to scaffold new projects
- [ ] **FR-5**: AGENTS.md must be tier-aware (rules adjust based on project type)
- [ ] **FR-6**: AIKH connection must be configurable (local, remote, or disabled)
- [ ] **FR-7**: UAM artifacts must work immediately after scaffolding

### Non-Functional Requirements

- [ ] **NFR-1**: Scaffolding must complete in < 5 seconds
- [ ] **NFR-2**: No external dependencies required for Lite tier
- [ ] **NFR-3**: Documentation must be self-contained (no external links required to understand)
- [ ] **NFR-4**: CI/validation scripts included per tier

---

## Constraints

- **C-1**: Must work on Mac, Windows (WSL2), and Linux
- **C-2**: Must not assume Docker availability for Lite tier
- **C-3**: Must integrate with existing AICM backend when connected
- **C-4**: Files must remain human-readable (Markdown preferred)

---

## The Three Tiers

### Tier 1: LITE (Backend-Only / Scripts / Libraries)

**Use Case**: CLI tools, Python libraries, data pipelines, automation scripts — projects that will NEVER have a frontend.

**Directory Structure**:
```
project-root/
├── .adrs/                      # Architecture Decision Records
│   └── .templates/
│       └── ADR_TEMPLATE.json
├── .discussions/               # Design conversations
│   └── .templates/
│       └── DISC_TEMPLATE.md
├── .sessions/                  # AI session continuity
│   └── README.md
├── .questions/                 # Open questions tracker
│   └── README.md
├── contracts/                  # Pydantic schemas (if Python)
│   └── __init__.py
├── src/                        # Source code
│   └── __init__.py
├── tests/                      # Test suite
│   └── __init__.py
├── AGENTS.md                   # AI assistant rules (LITE version)
├── pyproject.toml              # Or package.json, Cargo.toml, etc.
├── README.md                   # Project documentation
└── .gitignore
```

**AGENTS.md Lite Features**:
- Session management rules
- SSOT enforcement
- No frontend-specific rules
- No Docker/containerization rules
- No AIKH integration (optional add-on)

**Files Count**: ~12 files/folders

---

### Tier 2: STANDARD (Full-Stack Applications)

**Use Case**: Web apps, APIs with frontends, desktop apps — projects needing UI + backend coordination.

**Adds to LITE**:
```
project-root/
├── ... (all LITE files) ...
├── .plans/                     # Execution plans
│   └── .templates/
│       └── PLAN_TEMPLATE.json
├── backend/                    # Backend service
│   ├── services/
│   └── main.py
├── frontend/                   # Frontend application
│   ├── src/
│   └── package.json
├── docker/                     # Container definitions
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf
├── docs/                       # Extended documentation
│   └── ARCHITECTURE.md
├── docker-compose.yml          # Local development stack
├── Makefile                    # Common commands
└── .env.example                # Environment template
```

**AGENTS.md Standard Features**:
- All LITE rules
- Docker-first deployment rules
- Frontend/backend coordination
- Port conventions (backend: 8100, frontend: 3100)
- Build verification commands

**Files Count**: ~25 files/folders

---

### Tier 3: AGENTIC (AI-Native Applications)

**Use Case**: AI assistants, autonomous agents, LLM-integrated systems — projects with deep AI behavior baked in.

**Adds to STANDARD**:
```
project-root/
├── ... (all STANDARD files) ...
├── .research_papers/           # Academic paper archive
│   └── .gitkeep
├── .search_prompts/            # Curated search strategies
│   └── README.md
├── .experiments/               # A/B tests, evaluations
│   └── README.md
├── backend/
│   └── services/
│       ├── llm/                # LLM adapter layer
│       │   ├── __init__.py
│       │   └── multi_provider.py
│       ├── knowledge/          # AIKH integration
│       │   ├── __init__.py
│       │   └── rag_service.py
│       └── memory/             # Conversation memory
│           ├── __init__.py
│           └── session_memory.py
├── prompts/                    # Prompt templates
│   ├── system/
│   └── user/
├── evals/                      # LLM evaluation suite
│   ├── datasets/
│   └── metrics/
├── .aikh/                      # Local AIKH cache
│   └── config.yaml
└── AGENTIC_PATTERNS.md         # AI-specific patterns
```

**AGENTS.md Agentic Features**:
- All STANDARD rules
- LLM provider abstraction rules
- Prompt version control
- Evaluation-before-deploy requirements
- AIKH synchronization protocols
- Memory/context management patterns
- Observability requirements (P2RE traces)

**Files Count**: ~40+ files/folders

---

## Minimum CORE Requirements (All Tiers)

Every AICM-compatible repo MUST have:

| Item | Purpose | Location |
|------|---------|----------|
| **AGENTS.md** | AI assistant behavior rules | `/AGENTS.md` |
| **Sessions folder** | AI continuity tracking | `/.sessions/` |
| **Discussions folder** | Design conversation capture | `/.discussions/` |
| **ADRs folder** | Architecture decisions | `/.adrs/` |
| **Questions folder** | Open question tracking | `/.questions/` |
| **README.md** | Project overview | `/README.md` |
| **Git initialization** | Version control | `/.git/` |

**7 items = AICM-compatible minimum**

---

## AGENTS.md Tier Variants

### Lite AGENTS.md (Essential Rules Only)

```markdown
# AI Coding Rules (Lite)

> **Project Type**: Lite (Backend/Library/Script)
> **AIKH Integration**: Disabled
> **Docker**: Not Required

## Rule 0 — Quality Over Speed
[Same as global]

## Rule 1 — Session Continuity  
[Same as global - sessions, handoffs]

## Rule 2 — SSOT
[Simplified - .adrs, .discussions, .sessions, .questions only]

## Rule 3 — Before Starting Work
1. Check `.sessions/` for recent logs
2. Read any open `.questions/`
3. Claim session number
4. Begin work

## Rule 4 — Code Quality
[Same as global - type hints, docstrings, tests]
```

### Standard AGENTS.md (Adds Full-Stack)

```markdown
# AI Coding Rules (Standard)

> **Project Type**: Standard (Full-Stack Application)
> **AIKH Integration**: Optional
> **Docker**: Required

[All Lite rules, plus:]

## Rule 5 — Docker-First Development
- All code changes must be verified in Docker
- Never test locally without container verification
- Port conventions: backend=8100, frontend=3100

## Rule 6 — Frontend/Backend Coordination
- API changes require contract updates first
- Frontend never assumes backend shape without contract
- Breaking changes require version bump

## Rule 7 — Build Verification
Before finishing session:
- `docker compose build` must succeed
- `docker compose up` must start cleanly
```

### Agentic AGENTS.md (Adds AI Patterns)

```markdown
# AI Coding Rules (Agentic)

> **Project Type**: Agentic (AI-Native System)
> **AIKH Integration**: Required
> **Docker**: Required
> **Observability**: Required

[All Standard rules, plus:]

## Rule 8 — LLM Provider Abstraction
- Never hardcode provider-specific code
- All LLM calls through unified adapter
- Provider selection via configuration

## Rule 9 — Prompt Version Control
- All prompts stored in `/prompts/`
- Prompts are code — version controlled
- No inline prompt strings > 100 chars

## Rule 10 — Evaluation Before Deploy
- New LLM features require eval dataset
- Regression tests for prompt changes
- Document eval results in session file

## Rule 11 — AIKH Synchronization
- Research papers cached in `.research_papers/`
- Concepts synchronized to local `.aikh/`
- Context enrichment enabled for AI prompts

## Rule 12 — Memory Management
- Conversation memory architecture documented
- Session continuity across AI conversations
- Context window optimization strategies
```

---

## AIKH Integration Modes

| Mode | Description | Configuration |
|------|-------------|---------------|
| **Disabled** | No AIKH features | `aikh.enabled: false` |
| **Local** | SQLite cache only, no sync | `aikh.mode: local` |
| **Remote** | Full sync with AICM server | `aikh.mode: remote`, `aikh.server: url` |
| **Hybrid** | Local cache + periodic sync | `aikh.mode: hybrid`, `aikh.sync_interval: 1h` |

**Configuration File** (`.aikh/config.yaml`):
```yaml
aikh:
  enabled: true
  mode: hybrid
  server: http://localhost:8100
  sync_interval: 1h
  cache_path: .aikh/cache.db
  
  features:
    context_enrichment: true
    paper_search: true
    concept_autocomplete: true
```

---

## Scaffolding CLI

### Proposed Command

```bash
# Initialize Lite project
aicm init my-new-tool --tier lite

# Initialize Standard project
aicm init my-webapp --tier standard

# Initialize Agentic project
aicm init my-agent --tier agentic

# Upgrade existing project
aicm upgrade --to standard
```

### Script Alternative (No CLI Dependency)

```bash
# Download and run scaffold script
curl -sSL https://aicm.dev/init.sh | bash -s -- --tier lite --name my-project

# Or use Python
python -m aicm.scaffold --tier standard --name my-webapp
```

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should we include `.github/` workflows in Standard/Agentic? | `open` | |
| Q-2 | Should contracts be in `/contracts/` or `/shared/contracts/`? | `open` | |
| Q-3 | Should Lite include Makefile or keep it truly minimal? | `open` | |
| Q-4 | How to handle language-specific variations (Python vs TS vs Rust)? | `open` | |
| Q-5 | Should AIKH config be `.aikh/config.yaml` or `.aicm.yaml`? | `open` | |
| Q-6 | Should we provide VS Code workspace settings templates? | `open` | |

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Adopt three-tier model? | `pending` | |
| D-2 | AGENTS.md tier variants? | `pending` | |
| D-3 | Scaffolding mechanism (CLI vs script)? | `pending` | |
| D-4 | AIKH integration modes? | `pending` | |

---

## Scope Definition

### In Scope

- Directory structure definitions for all three tiers
- AGENTS.md variants per tier
- AIKH integration configuration
- Scaffolding script/CLI design
- Minimum viable file set definition

### Out of Scope

- CI/CD pipeline definitions (separate DISC)
- Language-specific tooling (covered by templates)
- AIKH server implementation (DISC-0022)
- IDE extension development (separate effort)

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-011 (UAM) | `FS` | `resolved` | Template structure | UAM defines artifact types |
| DISC-0022 (AIKH) | `soft` | `active` | Agentic tier | AIKH config schema needed |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | TBD | AICM-Compatible Project Standards | `pending` |
| Contract | TBD | ProjectTemplateSchema | `pending` |
| Script | TBD | aicm-scaffold.py | `pending` |

---

## Conversation Log

### 2026-01-03 - SESSION_017

**Topics Discussed**:
- User wants new projects to have UAM/AIKH framework from the start
- Three architecture tiers based on project needs identified
- Minimum core requirements for AICM compatibility
- AGENTS.md should be tier-aware
- AIKH integration should be configurable

**Key Insights**:
- Not all projects need frontend (Lite tier)
- Not all projects need AI integration (Standard tier)
- Agentic tier is the full AICM experience
- 7 items define the absolute minimum for AICM compatibility
- Scaffolding should be fast and dependency-free for Lite

**Action Items**:
- [ ] Finalize tier definitions with user feedback
- [ ] Create AGENTS.md templates for each tier
- [ ] Design scaffolding script
- [ ] Define AIKH config schema

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD

**Next Steps**:
1. Review and refine tier definitions
2. Answer open questions
3. Create ADR for project template standards
4. Implement scaffolding script

---

## Quality Score

**Status**: `[PENDING]` - Score calculated after required fields populated

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
