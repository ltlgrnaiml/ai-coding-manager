# AI Dev Orchestrator - TODO & Roadmap

> Extracted from engineering-tools on December 30-31, 2025

---

## Origin & Motivation

This project was born from **EXP-001: L1 vs L3 Plan Granularity Experiment**, which tested 8 AI models across two plan granularity levels to determine optimal cost/quality tradeoffs.

Additionally, it extracts the **full AI workflow infrastructure** from engineering-tools including:
- **xAI/Grok integration** with LangChain-compatible adapters
- **RAG system** with SQLite-backed knowledge archive
- **Phoenix observability** for LLM call tracing
- **Enhanced RAG** with query enhancement and LLM re-ranking

### Key Findings That Motivated This Project

1. **L3 plans reduce stochastic variation by 50%+** - Budget models match premium quality
2. **All 8 models achieved 100% task completion** - Plan structure matters more than model
3. **3-6x cost savings** possible with structured plans on cheaper models
4. **L2 (middle ground) identified** - Constraints without full procedures

### The Vision

Create a **standalone framework** for structured AI-assisted code development that:
- Helps developers get consistent, high-quality code from AI assistants
- Provides tiered plan granularity (L1/L2/L3) matched to model capability
- Enables A/B testing of AI models with reproducible experiments
- Tracks session continuity across AI conversations
- **Full xAI/Grok integration** with structured output
- **RAG-powered knowledge retrieval** for context-aware generation
- **Phoenix observability** for debugging and cost tracking

---

## Current State (What's Done)

### ✅ Core Infrastructure

- [x] Project structure created (`src/ai_dev_orchestrator/`)
- [x] `AGENTS.md` - Global AI instructions
- [x] `README.md` - Getting started guide with feature examples
- [x] `pyproject.toml` - Full dependencies with optional extras
- [x] `.gitignore` - Standard Python ignores

### ✅ LLM Module (`src/ai_dev_orchestrator/llm/`)

- [x] `service.py` - xAI integration with structured output generation
  - [x] Pydantic schema validation with retry logic
  - [x] SQLite logging for all API calls
  - [x] Cost estimation and usage tracking
  - [x] Model management (10+ Grok models)
- [x] `xai_langchain.py` - LangChain-compatible XAIChatModel
- [x] `rag_chain.py` - RAG chain with knowledge archive integration

### ✅ Knowledge Module (`src/ai_dev_orchestrator/knowledge/`)

- [x] `database.py` - SQLite schema with FTS5 and vector storage
- [x] `search_service.py` - FTS, vector, and hybrid search (RRF)
- [x] `embedding_service.py` - sentence-transformers with auto-fallback
- [x] `context_builder.py` - Token-budgeted context building
- [x] `enhanced_rag.py` - 3-level enhanced RAG (query enhancement, LLM re-ranking, graph expansion)
- [x] `sanitizer.py` - PII/secret redaction before LLM exposure

### ✅ Observability Module (`src/ai_dev_orchestrator/observability/`)

- [x] `phoenix_tracer.py` - Phoenix/OpenTelemetry integration
  - [x] LangChain instrumentation
  - [x] OpenAI SDK instrumentation (works with xAI)
  - [x] Custom trace spans

### ✅ Workflow Module (`src/ai_dev_orchestrator/workflow/`)

- [x] `plan_manager.py` - L1/L2/L3 plan creation and management
- [x] `discussion_manager.py` - Design discussion management
- [x] `session_manager.py` - AI session continuity tracking

### ✅ CLI (`src/ai_dev_orchestrator/cli.py`)

- [x] `ai-dev new-plan` - Create plans with granularity selection
- [x] `ai-dev new-discussion` - Create discussions
- [x] `ai-dev new-session` - Create session logs
- [x] `ai-dev health` - Check xAI API health
- [x] `ai-dev stats` - Show LLM usage statistics
- [x] `ai-dev models` - List available xAI models
- [x] `ai-dev init-db` - Initialize knowledge database

### ✅ Workflow Infrastructure

- [x] `.discussions/` - Design conversation directory with AGENTS.md
- [x] `.plans/` - Execution plan directory with README
- [x] `.sessions/` - Session continuity directory with README
- [x] `.questions/` - Open questions directory with README
- [x] `.adrs/` - ADR directory with INDEX.md

---

## What Needs to Be Completed

### 🔴 Priority 1: Testing & Validation

- [ ] **Tests**
  - [ ] `tests/test_llm_service.py` - LLM service tests (mocked)
  - [ ] `tests/test_knowledge.py` - Knowledge/RAG tests
  - [ ] `tests/test_workflow.py` - Workflow manager tests
  - [ ] `tests/test_cli.py` - CLI script tests

- [ ] **Validation**
  - [ ] Verify all imports work correctly
  - [ ] Test xAI integration with real API key
  - [ ] Test Phoenix observability startup

### 🟡 Priority 2: Documentation & Templates

- [ ] **Templates**
  - [ ] `.plans/.templates/PLAN_TEMPLATE.json` - Plan JSON template
  - [ ] `.discussions/.templates/DISC_TEMPLATE.md` - Discussion template
  - [ ] `.adrs/.templates/ADR_TEMPLATE.json` - ADR JSON template

- [ ] **Guides**
  - [ ] `docs/guides/GETTING_STARTED.md` - Step-by-step tutorial
  - [ ] `docs/guides/XAI_INTEGRATION.md` - xAI setup and usage
  - [ ] `docs/guides/RAG_SETUP.md` - Knowledge archive setup
  - [ ] `docs/guides/PHOENIX_OBSERVABILITY.md` - Tracing setup

### 🟢 Priority 3: Examples & Polish

- [ ] **Example Projects**
  - [ ] `examples/simple_rag/` - Basic RAG usage
  - [ ] `examples/structured_output/` - Pydantic schema generation
  - [ ] `examples/full_workflow/` - Discussion → Plan → Execution

- [ ] **CI/CD**
  - [ ] `.github/workflows/test.yml` - Run tests on PR
  - [ ] `.github/workflows/lint.yml` - Ruff linting

### 🔵 Priority 4: Future Features

- [ ] **Google Gemini Integration** (TODO)
  - [ ] Add `gemini_langchain.py` adapter
  - [ ] Multi-provider support in RAG chain

- [ ] **LangFuse Integration** (TODO - alternative to Phoenix)
  - [ ] Add LangFuse tracer option
  - [ ] Cloud-based observability

- [ ] **LangGraph Integration** (TODO)
  - [ ] State machine workflows
  - [ ] Multi-step agent patterns

- [ ] **Memory System** (TODO)
  - [ ] Short-term conversation memory
  - [ ] Long-term knowledge persistence
  - [ ] Self-reflection capabilities

- [ ] **Web UI**
  - [ ] Plan editor with L1/L2/L3 toggle
  - [ ] Knowledge archive browser
  - [ ] Phoenix dashboard integration

---

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| Pydantic-only dependency | Keep it minimal and portable |
| JSON for plans/ADRs | Machine-readable, AI-friendly |
| Markdown for discussions | Human-readable, flexible |
| L1/L2/L3 granularity | Evidence from EXP-001 supports tiered approach |
| Session-based continuity | AI assistants work in conversations |

---

## References

- **Source Project**: `engineering-tools` (private)
- **Key Experiment**: EXP-001 L1 vs L3 Granularity
- **Models Tested**: Opus, Sonnet, Gemini Pro, GPT-5.2 (L1) + Grok, Haiku, Flash, GPT-5.1 (L3)

---

## How to Contribute

1. Pick an item from the TODO list above
2. Create a branch: `feature/item-name`
3. Implement with tests
4. Submit PR

---

*Last Updated: December 30, 2025*
