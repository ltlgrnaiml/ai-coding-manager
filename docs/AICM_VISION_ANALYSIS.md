# AICM Vision Scope Analysis

> **SESSION_009** | 2026-01-02 | Revision 1 (Pre-Research)

This document analyzes the current AICM vision for strengths and weaknesses, identifying areas requiring additional research before the vision can be considered complete.

---

## Executive Summary

The AICM vision is **strong on conceptual architecture** but **weak on implementation specifics** in several critical areas. The UAM foundation is well-defined, but the "Tap-In Protocol" and AI orchestration layers need research-backed design decisions.

---

## Strengths Analysis

### 🟢 S1: Unified Artifact Model (UAM) - EXCELLENT

**What's Working**:

- Six-pillar model (EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE) is comprehensive
- Primary Chain Model provides deterministic traceability
- Lifecycle states (draft → active → resolved/superseded) are well-defined
- Quality scoring rubrics with provenance tracking
- Inter-document linking rules established

**Research Backing**: This is grounded in Documentation-Driven Development, ADR patterns, and Design Docs best practices. DISC-011 through DISC-015 provide solid foundation.

**Score**: 9/10 - Minor refinements only

---

### 🟢 S2: Workflow Spectrum (5 Modes) - STRONG

**What's Working**:

- Manual → Prompt Gen → Smart Link → Section Improve → E2E Generation
- Clear spectrum from human control to AI autonomy
- Flexible mode switching during development
- Acknowledges need to evolve with industry

**Research Backing**: Aligns with human-in-the-loop AI patterns and graduated autonomy concepts.

**Score**: 8/10 - Needs implementation research

---

### 🟢 S3: Research Infrastructure - SOLID

**What's Working**:

- PDF extraction pipeline (`extract_pdf_papers.py`) functional
- Research database with academic metadata schema
- FTS5 + vector search hybrid approach
- CLI and API interfaces available
- ~24 papers already extracted and indexed

**Research Backing**: Self-built, functional, ready for scaling.

**Score**: 8/10 - Ready for use

---

### 🟢 S4: Self-Propagating Methodology - INNOVATIVE

**What's Working**:

- Projects built with AICM include all context artifacts
- Future sessions can "tap-in" without re-explaining
- Git-tracked documentation creates automatic history
- Quality scores persist for comparison

**Research Backing**: Novel concept combining documentation practices with AI context management.

**Score**: 7/10 - Needs validation research

---

### 🟢 S5: Technology Stack - PRAGMATIC

**What's Working**:

- FastAPI + React + SQLite (proven, portable)
- Pydantic for contract validation
- sqlite-vec for embeddings
- MCP for AI tool integration

**Research Backing**: Industry-standard choices, well-documented.

**Score**: 9/10 - Solid foundation

---

## Weaknesses Analysis

### 🔴 W1: Tap-In Protocol - UNDER-SPECIFIED

**Current State**: Conceptually described but lacks technical specification.

**Missing Details**:

- How exactly does context serialization work?
- What's the "warm-up" cost for different project sizes?
- How do we handle stale context vs fresh re-indexing?
- Token budget allocation across context layers
- Context compression strategies for large projects
- Cross-project context sharing mechanisms

**Research Needed**: 
- Context window optimization papers
- RAG chunking strategies for code + docs
- Long-context LLM techniques
- Memory hierarchies in AI systems

**Impact**: HIGH - This is the core differentiator

**Score**: 4/10 - Needs significant research

---

### 🔴 W2: AI Chat Integration Architecture - VAGUE

**Current State**: "AI Chat Window with MCP integration" stated but not designed.

**Missing Details**:

- Streaming architecture for real-time responses
- Context injection strategy (what goes into system prompt?)
- Tool calling patterns and error handling
- Multi-turn conversation management
- Session state persistence
- Model switching and fallback strategies
- Cost optimization (when to use cheap vs expensive models)

**Research Needed**:
- Agentic AI system architectures
- Tool-use patterns in production systems
- Streaming LLM response handling
- Context management in chat systems

**Impact**: HIGH - Core user-facing feature

**Score**: 3/10 - Needs fundamental design

---

### 🔴 W3: Quality Scoring Implementation - THEORETICAL

**Current State**: DISC-013 describes rubrics but no implementation exists.

**Missing Details**:

- Which LLM evaluates quality? (Judge models)
- How to calibrate scoring across different content types?
- Cost of quality evaluation at scale
- Human-AI scoring correlation validation
- Improvement suggestion generation
- A/B testing of prompts based on scores

**Research Needed**:
- LLM-as-judge papers
- Evaluation frameworks (MT-Bench, AlpacaEval patterns)
- Automated code review systems
- Documentation quality metrics

**Impact**: MEDIUM - Affects user experience, not blocking

**Score**: 4/10 - Needs implementation research

---

### 🔴 W4: Artifact Generation Pipelines - UNDEFINED

**Current State**: "DISC → ADR → SPEC → Contract → PLAN" described but not implemented.

**Missing Details**:

- Prompt engineering for each artifact type
- Validation gates between generation steps
- Human approval workflows
- Rollback and versioning strategies
- Template management
- Confidence thresholds for auto-generation

**Research Needed**:
- Agentic workflow orchestration
- Multi-step LLM pipelines
- Code generation validation techniques
- Self-correcting AI systems

**Impact**: HIGH - Core value proposition

**Score**: 3/10 - Needs design + implementation

---

### 🔴 W5: Observability Dashboard - PLACEHOLDER

**Current State**: "LangChain/LangFuse/LangGraph trace viewer" mentioned, no design.

**Missing Details**:

- Which observability platform to integrate?
- Self-hosted vs cloud trade-offs
- Trace storage and retention policies
- Cost attribution per artifact
- Performance metrics and alerting
- User-facing dashboards vs developer tools

**Research Needed**:
- LLM observability best practices
- Phoenix, LangFuse, Weights & Biases comparisons
- Cost optimization strategies for LLM apps
- Tracing standards (OpenTelemetry for LLMs)

**Impact**: MEDIUM - Important for optimization, not MVP blocking

**Score**: 3/10 - Needs research + design

---

### 🔴 W6: Multi-Project / Team Support - NOT ADDRESSED

**Current State**: Focus is solo-dev, no mention of scaling.

**Missing Details**:

- Conflict resolution for concurrent edits
- Sharing artifacts across projects
- User authentication and authorization
- Cloud deployment vs local-first
- Sync strategies for distributed teams

**Research Needed**:
- Collaborative AI tools
- CRDT for document sync
- Auth patterns for developer tools

**Impact**: LOW (for MVP) - Can defer

**Score**: 2/10 - Not designed at all

---

### 🔴 W7: Error Handling & Recovery - MISSING

**Current State**: No discussion of failure modes.

**Missing Details**:

- LLM API failures and retries
- Partial generation recovery
- Context corruption handling
- Database integrity checks
- User-facing error messages
- Graceful degradation strategies

**Research Needed**:
- Fault-tolerant AI systems
- Graceful degradation patterns
- Error handling in agentic systems

**Impact**: MEDIUM - Critical for production use

**Score**: 2/10 - Completely missing

---

### 🟡 W8: UI/UX Design - CONCEPTUAL ONLY

**Current State**: "Like DevToolsPage" but no mockups or specifications.

**Missing Details**:

- Component hierarchy and state management
- Responsive design requirements
- Accessibility considerations
- Keyboard shortcuts and power-user features
- Theme and customization options

**Research Needed**:
- Modern developer tool UX patterns
- IDE extension UX studies
- Accessibility in code editors

**Impact**: MEDIUM - Affects adoption

**Score**: 5/10 - Has direction, needs detail

---

## Strength-to-Weakness Mapping

| Strength | Related Weakness | Gap |
|----------|------------------|-----|
| S1: UAM Model | W4: Artifact Generation | How to auto-generate valid artifacts? |
| S2: Workflow Spectrum | W2: AI Chat Architecture | How does chat interact with workflows? |
| S3: Research Infra | - | No gap, ready to use |
| S4: Self-Propagating | W1: Tap-In Protocol | Technical implementation details |
| S5: Tech Stack | W5: Observability | Which tools integrate best? |

---

## Priority Research Areas

Based on impact and current score:

| Priority | Area | Current Score | Impact | Research Focus |
|----------|------|---------------|--------|----------------|
| **P1** | W1: Tap-In Protocol | 4/10 | HIGH | Context optimization, RAG strategies |
| **P2** | W2: AI Chat Architecture | 3/10 | HIGH | Agentic systems, tool-use patterns |
| **P3** | W4: Artifact Generation | 3/10 | HIGH | LLM pipelines, validation |
| **P4** | W3: Quality Scoring | 4/10 | MED | LLM-as-judge, evaluation |
| **P5** | W5: Observability | 3/10 | MED | LLM tracing, cost optimization |
| **P6** | W7: Error Handling | 2/10 | MED | Fault tolerance, recovery |
| **P7** | W8: UI/UX Design | 5/10 | MED | Developer tool patterns |
| **P8** | W6: Multi-Project | 2/10 | LOW | Defer to post-MVP |

---

## Recommendation

**Before Revision 2**, acquire research papers in these categories:

1. **Context & Memory Management** (for W1, W2)
2. **Agentic AI Architectures** (for W2, W4)
3. **LLM Evaluation & Quality** (for W3)
4. **AI Observability & Tracing** (for W5)
5. **Code Generation Validation** (for W4)
6. **Developer Tool UX** (for W8)

See `.research_prompts/` for targeted search queries.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial analysis (pre-research) |
