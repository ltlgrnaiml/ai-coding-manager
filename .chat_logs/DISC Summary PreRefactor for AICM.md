# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

Please read in and summarize all DISC files, synthesize a "Vision" statement that the sum total of the recorded work details, and call out any contridictatory information.

*Searched filesystem*

*Listed directory [.discussions](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions) *

*Updated todo list*

*Viewed [INDEX.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/INDEX.md) *

*Viewed [DISC-001_DevTools-AI-Workflow-Integration.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-001_DevTools-AI-Workflow-Integration.md) *

*Viewed [DISC-001_Knowledge-Capture-System-Vision.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-001_Knowledge-Capture-System-Vision.md) *

*Viewed [DISC-002_AI-Lite-Prompt-Chain-Workflow.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-002_AI-Lite-Prompt-Chain-Workflow.md) *

*Viewed [DISC-003_Langchain-Langgraph-Integration.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-003_Langchain-Langgraph-Integration.md) *

*Viewed [DISC-004_PII-Sanitization-Pipeline.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-004_PII-Sanitization-Pipeline.md) *

*Viewed [DISC-005_Embedding-Model-Selection.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-005_Embedding-Model-Selection.md) *

*Viewed [DISC-006_Knowledge-Archive-RAG-System.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-006_Knowledge-Archive-RAG-System.md) *

*Viewed [DISC-006_xAI_Prompts.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-006_xAI_Prompts.md) *

*Viewed [DISC-007_Unified-xAI-Agent-Wrapper.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-007_Unified-xAI-Agent-Wrapper.md) *

*Viewed [DISC-008_Open-Questions-Workflow-UX.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-008_Open-Questions-Workflow-UX.md) *

*Viewed [DISC-009_Orphan-ADRs-Policy-Document-Strategy.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-009_Orphan-ADRs-Policy-Document-Strategy.md) *

*Viewed [DISC-010_Centralized-UI-UX-Design-System.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-010_Centralized-UI-UX-Design-System.md) *

*Viewed [DISC-011_Unified-Artifact-Model.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-011_Unified-Artifact-Model.md) *

*Viewed [DISC-012_Plan-Artifact-Structure-Lifecycle.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-012_Plan-Artifact-Structure-Lifecycle.md) *

*Viewed [DISC-013_Quality-Scoring-System.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-013_Quality-Scoring-System.md) *

*Viewed [DISC-014_Primary-Chain-Validation.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-014_Primary-Chain-Validation.md) *

*Viewed [DISC-015_AI-Native-Documentation-Architecture.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-015_AI-Native-Documentation-Architecture.md) *

*Viewed [DISC-016_AI-Context-Prompt-Generator.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-016_AI-Context-Prompt-Generator.md) *

*Viewed [DISC-017_AI-Coding-Management-Hub.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-017_AI-Coding-Management-Hub.md) *

*Viewed [DISC-017_Standalone-DevTool-Architecture.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-017_Standalone-DevTool-Architecture.md) *

*Viewed [DISC-018_Meta-Agent-Self-Improvement-System.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-018_Meta-Agent-Self-Improvement-System.md) *

*Updated todo list*

### Planner Response

---

# DISC Files Synthesis Report

## Executive Summary

I analyzed **18 DISC files** (plus duplicates) covering the full scope of the ai-coding-manager project. Below is the summary, synthesized vision, and identified contradictions.

---

## Individual DISC Summaries

### Foundation Layer (L0 DISCs)

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-011** | Unified Artifact Model (UAM) | `active` | **UMBRELLA** - Defines the Six-Pillar documentation model (EXPLORE→DECIDE→DEFINE→SHAPE→EXECUTE→GUIDE), Primary Chain Model (every artifact has ONE parent), lifecycle states, and quality scoring. Supersedes fragmented ADR-0016. |
| **DISC-009** | Orphan ADRs & Policy Strategy | `deferred` | Addressed by DISC-011's tier-skip mechanism and Primary Chain validation |

### Knowledge & RAG Layer

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-001** (KCS) | Knowledge Capture System Vision | `active` | Transform project into an **Agentic AI Coding Knowledge System** - monitors git commits, extracts code snippets with quality signals, stores in SQLite with embeddings, provides context-aware prompts for budget models |
| **DISC-001** (DT) | DevTools AI Workflow Integration | `resolved` | Extend DevTools panel for 6-tier workflow with 2D/3D artifact graph visualization using react-force-graph |
| **DISC-006** | Knowledge Archive & RAG System | `resolved` | Unified `knowledge.db` serving as persistent storage AND RAG corpus - bidirectional file sync, FTS5, semantic search, PII sanitization |
| **DISC-006** (xAI) | xAI Generation Prompts | - | Test prompts for artifact generation with RAG context |

### AI Integration Layer

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-002** | AI-Lite Prompt Chain | `resolved` | Design prompt chain workflow: DISC→ADR→SPEC→Contract→PLAN with copy-paste-ready prompts for any LLM |
| **DISC-003** | LangChain/Langgraph | `resolved` | Integrate LangChain + Langgraph for unified LLM orchestration with Phoenix observability |
| **DISC-004** | PII Sanitization | `resolved` | Regex-based MVP with <5% false positive rate for safe RAG context injection |
| **DISC-005** | Embedding Model Selection | `resolved` | Primary: `all-mpnet-base-v2` (768 dims); Hybrid search (BM25 + vectors via RRF merge) |
| **DISC-007** | Unified xAI Agent Wrapper | `active` | Single `XAIAgent` class combining LangChain RAG + xAI native SDK agentic tools (web/X search, code execution, MCP, collections) |

### Workflow & Quality Layer (DISC-011 Children)

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-012** | Plan Structure & Lifecycle | `resolved` | L3-first granularity by default, auto-sync INDEX.json, never delete archived PLANs, amendment pattern with guardrails |
| **DISC-013** | Quality Scoring System | `resolved` | Hybrid scoring with Score Provenance Chain (SHA256 hashes), rubric versioning, embedded score history, tracks WHO scored (ai/human) |
| **DISC-014** | Primary Chain Validation | `resolved` | Graduated CI enforcement - required fields block, orphans warn; auto-generated artifact graph; JSON validation reports |

### Documentation & Context Layer

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-008** | Open Questions Workflow UX | `active` | Warning dialogs + wizard for question resolution before artifact creation; Question Closure Checklist (7 steps) |
| **DISC-010** | Centralized UI/UX Design System | `draft` | Single TypeScript design tokens module for all colors, fonts, spacing, graph physics |
| **DISC-015** | AI-Native Documentation Architecture | `draft` | Research-driven (20 papers) approach for RAG-optimized chunking, semantic linking, hierarchical memory (L0-L3), Zettelkasten-inspired linking |
| **DISC-016** | AI Context Prompt Generator | `active` | CLI/API tool to generate AI-optimized prompts with auto-nested context for AI tools without file system access |

### Tooling & Platform Layer

| DISC | Title | Status | Core Purpose |
|------|-------|--------|--------------|
| **DISC-017** | AI Coding Management Hub (AICM) | `active` | Web-based platform for managing UAM artifacts with AI chat, MCP integration, observability dashboard, and "tap-in" capability (point at any project folder → instant context) |
| **DISC-018** | Meta-Agent Self-Improvement | `deferred` | Future vision: agents evaluating, swapping, and improving other agents based on quality metrics |

---

# 🌟 Synthesized Vision Statement

## **AI Coding Management (AICM) Platform Vision**

> **Build an AI-first development management platform that enables solo developers (and small teams) to leverage AI assistants at maximum effectiveness by providing structured artifact workflows, rich contextual knowledge, and continuous quality feedback—making budget models perform like premium models through intelligent context injection.**

### Core Pillars

1. **Unified Artifact Model (UAM)** - Six-pillar documentation (EXPLORE→DECIDE→DEFINE→SHAPE→EXECUTE→GUIDE) with Primary Chain traceability, lifecycle management, and schema validation

2. **Knowledge-Augmented AI** - SQLite + embeddings knowledge archive that captures code patterns, ADRs, and session history; hybrid search (BM25 + vectors); RAG context injection that enables smaller models to match premium quality

3. **Self-Propagating Context ("Tap-In")** - Point the tool at any UAM-compliant project folder and instantly have full context: artifacts, vectors, session history, and relationships—no warmup cost

4. **Quality-Driven Development** - Score Provenance Chain with content-addressed scoring, rubric versioning, and AI experimentation correlation; "Everything Graded" philosophy

5. **Workflow Automation Spectrum** - From manual editing to AI prompt generation to smart document linking to full E2E agentic generation; workflow modes evolve with industry

6. **AI Observability & Evaluation** - LangChain/Phoenix traces, prompt quality evaluation, schema adherence checking; human monitors AI output, doesn't code directly

### Target Outcome

A developer using this platform can:
- Start with a chat conversation → auto-generate DISC
- Pass DISC through agentic workflows → auto-generate ADRs, SPECs, Contracts, PLANs
- See quality scores in real-time with improvement hints
- Use budget models (Haiku, Flash) with rich context and achieve premium-quality output
- "Tap in" to any project built with this tool and continue seamlessly
- Eventually: have meta-agents improve, swap, and classify other agents (DISC-018 future)

---

# ⚠️ Identified Contradictions & Conflicts

## 1. **Duplicate DISC-001 Files**
| File | Topic |
|------|-------|
| [DISC-001_DevTools-AI-Workflow-Integration.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-001_DevTools-AI-Workflow-Integration.md:0:0-0:0) | DevTools panel UI with 2D/3D visualization |
| [DISC-001_Knowledge-Capture-System-Vision.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-001_Knowledge-Capture-System-Vision.md:0:0-0:0) | Knowledge capture and sync from engineering-tools |

**Issue**: Two completely different discussions share the same DISC ID.
**Recommendation**: Renumber Knowledge Capture to DISC-019 or another available number.

---

## 2. **Duplicate DISC-006 Files**
| File | Topic |
|------|-------|
| [DISC-006_Knowledge-Archive-RAG-System.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-006_Knowledge-Archive-RAG-System.md:0:0-0:0) | Main Knowledge Archive design |
| [DISC-006_xAI_Prompts.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-006_xAI_Prompts.md:0:0-0:0) | Test prompts for artifact generation |

**Issue**: The prompts file should not be a DISC—it's supplementary material.
**Recommendation**: Rename to `DISC-006_xAI_Prompts-SUPPLEMENT.md` or move to a `prompts/` directory.

---

## 3. **Duplicate DISC-017 Files**
| File | Topic |
|------|-------|
| [DISC-017_AI-Coding-Management-Hub.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-017_AI-Coding-Management-Hub.md:0:0-0:0) | Concise AICM overview |
| [DISC-017_Standalone-DevTool-Architecture.md](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions/DISC-017_Standalone-DevTool-Architecture.md:0:0-0:0) | Detailed AICM architecture |

**Issue**: Same DISC ID, similar content with different detail levels.
**Recommendation**: Merge into single file or keep one as the canonical version.

---

## 4. **Tier Numbering Confusion (Acknowledged)**
DISC-011 explicitly acknowledges and resolves this:
- **ADR-0016** defined a 3-tier model (T0=Contracts, T1=ADRs, T2=SPECs, T3=Guides)
- **ADR-0043** defined a 6-tier workflow (T0=Discussion, T1=ADR, T2=SPEC, T3=Contract, T4=Plan, T5=Fragment)
- **ADR-0010** called Contracts "Tier 0"

**Resolution**: UAM (DISC-011) replaces tier numbering with **named pillars** (EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE) to eliminate confusion.

---

## 5. **Session Numbering Discrepancy**
- DISC-015 references `SESSION_022` with date `2026-01-01`
- DISC-011 references `SESSION_021` with date `2025-12-31`
- Multiple DISCs reference SESSION_024 on different dates

**Issue**: Session ID assignment may have gaps or reuse.
**Recommendation**: Audit `.sessions/` folder for gaps and ensure consistent incrementing.

---

## 6. **INDEX.md Statistics Mismatch**
The INDEX.md states:
- **Total Discussions**: 16
- But there are **18+ DISC files** (including duplicates)

**Recommendation**: Update INDEX.md to reflect accurate count after resolving duplicates.

---

## 7. **Minor: Embedding Dimension Inconsistency**
- DISC-005 recommends `all-mpnet-base-v2` with **768 dimensions**
- DISC-006 schema shows `embeddings` table with comment: `384-dim float array`

**Issue**: Mismatch between recommended model dimension and schema comment.
**Recommendation**: Update DISC-006 schema comment to match actual model (768 or make configurable).

---

*Updated todo list*

### Planner Response

## Summary

I analyzed **18 DISC files** from [.discussions/](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/.discussions:0:0-0:0) and delivered:

### 1. Individual Summaries
All 18 DISCs categorized into layers:
- **Foundation** (DISC-011 UAM umbrella, DISC-009)
- **Knowledge/RAG** (DISC-001, DISC-006)
- **AI Integration** (DISC-002 through DISC-007)
- **Workflow/Quality** (DISC-012 through DISC-014)
- **Documentation/Context** (DISC-008, DISC-010, DISC-015, DISC-016)
- **Tooling/Platform** (DISC-017, DISC-018)

### 2. Synthesized Vision
**AI Coding Management (AICM) Platform** - An AI-first development management platform with five core pillars:
1. **Unified Artifact Model** - Six-pillar documentation with Primary Chain traceability
2. **Knowledge-Augmented AI** - SQLite + embeddings for budget models to match premium quality
3. **Self-Propagating Context ("Tap-In")** - Point at any project folder for instant context
4. **Quality-Driven Development** - Score Provenance Chain with AI experimentation correlation
5. **Workflow Automation Spectrum** - From manual to full agentic generation

### 3. Contradictions Identified
| Issue | Severity | Recommendation |
|-------|----------|----------------|
| **Duplicate DISC-001** (2 different topics) | HIGH | Renumber Knowledge Capture |
| **Duplicate DISC-006** (main + prompts) | MEDIUM | Move prompts to supplement |
| **Duplicate DISC-017** (2 versions) | MEDIUM | Merge into single canonical file |
| **Tier numbering confusion** | LOW | Already resolved by UAM pillars |
| **Session ID gaps** | LOW | Audit session folder |
| **INDEX.md count wrong** (16 vs 18+) | LOW | Update after deduplication |
| **Embedding dims (768 vs 384)** | LOW | Update schema comment |

### User Input

What about the UI/UX components are there any information there?

*Updated todo list*

*Searched filesystem*

*Listed directory [ai-coding-manager](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager) *

*Listed directory [frontend](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend) *

*Listed directory [src](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src) *

*Listed directory [views](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/views) *

*Viewed [App.tsx](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/App.tsx) *

*Viewed [package.json](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/package.json) *

*Viewed [ChatView.tsx](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/views/ChatView.tsx) *

*Viewed [WorkflowView.tsx](file://wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/views/WorkflowView.tsx) *

*Updated todo list*

### Planner Response

# UI/UX Component Information

## Current Implementation (in codebase)

The frontend is a **React + TypeScript + TailwindCSS** application with two main views:

### `@//wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/App.tsx`
- **Sidebar navigation** with icon-based nav (Chat, Workflow)
- **Dark theme** (gray-950 background)
- **Lucide icons** throughout
- API health check with warning banner

### `@//wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/views/ChatView.tsx`
- **Streaming chat** with xAI Grok models
- **Model selector** dropdown
- **Markdown rendering** with syntax highlighting (react-markdown, react-syntax-highlighter)
- **Message bubbles** with copy functionality
- **Auto-scroll** and **auto-resize textarea**

### `@//wsl.localhost/Ubuntu/home/mycahya/coding/ai-coding-manager/frontend/src/views/WorkflowView.tsx`
- **Three-panel layout**: Stats sidebar → Artifact list → Content viewer
- **Artifact type filtering** (discussion, adr, plan, session, question)
- **Search functionality**
- **Color-coded artifact types** (purple=discussion, cyan=adr, green=plan, etc.)

---

## Planned UI/UX from DISC Files

### From DISC-001 (DevTools AI Workflow Integration) - **RESOLVED**

**Layout Pattern** (Agreed):
```
┌─────────────────────────────────────────────────────────────────────┐
│  DevTools Workflow Manager                              [🔍] [⚙️]  │
├──────────────┬──────────────────────────────────────────────────────┤
│  📁 ADRs     │         INTERACTIVE MAP (2D/3D Toggle)              │
│  ├─ ADR-0001 │      [DISC]──▶[ADR-0043]──▶[SPEC]──▶[Plan]          │
│  ...         ├──────────────────────────────────────────────────────│
│  📋 SPECs    │              READER VIEW                             │
│  💬 Discuss  │  # ADR-0043: AI Development Workflow                │
│  📑 Plans    │                                    [✏️ Edit]        │
│  🔷 Contracts│                                                      │
└──────────────┴──────────────────────────────────────────────────────┘
```

**Key Decisions**:
| Feature | Decision |
|---------|----------|
| **Graph Visualization** | `react-force-graph` with 2D/3D toggle |
| **Editor Mode** | Slide-in panel from right, replaces viewer |
| **Map Interactivity** | Click node → focus file → update reader |
| **Node Colors by Tier** | Blue=DISC, Green=ADR, Yellow=SPEC, Purple=Contract, Red=Plan |

**Approved Enhancements**:
- Resizable split panes (Map ↔ Reader)
- Quick preview on hover (tooltip cards)
- Breadcrumb navigation trail
- Status indicators (✅ active, ⚠️ review, 📝 draft)
- Keyboard navigation (Tab, arrows, E for edit)

---

### From DISC-010 (Centralized UI/UX Design System) - **DRAFT**

**Problem**: Design decisions scattered across files (hardcoded colors, magic numbers).

**Proposed Solution**: Single TypeScript design tokens module:

```typescript
// shared/design-tokens.ts (proposed)
export const colors = {
  tiers: {
    discussion: '#3B82F6',  // Blue
    adr: '#22C55E',         // Green
    spec: '#EAB308',        // Yellow
    contract: '#A855F7',    // Purple
    plan: '#EF4444',        // Red
    fragment: '#6B7280',    // Gray
  },
  // ... more tokens
}
```

**Open Questions**:
- CSS variables vs JS constants?
- Graph physics in design tokens or separate?
- Runtime-configurable or build-time only?

---

### From DISC-017 (AI Coding Management Hub) - **ACTIVE**

**Core UI (Two Main Tools)**:
1. **Workflow Manager** - artifact browser with sidebar, reader/editor split
2. **AI Chat Window** - integrated chat with MCP tool access, streaming

**Additional Planned Components**:
| Component | Purpose |
|-----------|---------|
| **Observability Dashboard** | LangChain/LangFuse/LangGraph trace viewer |
| **Quality Evaluator** | Prompt quality, schema adherence display |
| **Context API Panel** | "Tap-in" project browser |

**Workflow Modes** (UI must support):
1. Manual Mode - human edits directly
2. Prompt Gen Mode - AI generates copy-paste prompts
3. Smart Link Mode - chat linked to open document
4. Section Improve Mode - review score → tweak prompt
5. E2E Generation Mode - full agentic generation

---

### From DISC-008 (Open Questions Workflow UX) - **ACTIVE**

**Proposed UX Flows**:

**Warning Dialog** (when AI Prompt Copy with open questions):
```
┌─────────────────────────────────────────────────────┐
│  ⚠️ Open Questions Detected                         │
│                                                     │
│  This discussion has 4 unanswered questions.        │
│                                                     │
│  [ View Questions ]  [ Resolve Now ]  [ Copy Anyway ]│
└─────────────────────────────────────────────────────┘
```

**Question Resolution Wizard**:
```
┌─────────────────────────────────────────────────────┐
│  Open Questions Wizard (1 of 4)                     │
│                                                     │
│  Q-1: Should wrapper auto-select between...?        │
│                                                     │
│  Context: [relevant info displayed]                 │
│                                                     │
│  Your Answer: [text input]                          │
│                                                     │
│  [ 🤖 Suggest Answer ]  [ Defer ]  [ Save & Next ] │
└─────────────────────────────────────────────────────┘
```

**Artifact Card Badge**:
```
┌─────────────────────────────────────────────────────┐
│  📋 DISC-007                           🟡 4 Open    │
│  Unified xAI Agent Wrapper                          │
└─────────────────────────────────────────────────────┘
```

---

### From DISC-017 (Migration Assets)

**High-Value Components to Migrate from engineering-tools**:
| Component Count | Source Location | Value |
|-----------------|-----------------|-------|
| **33 Workflow Components** | `apps/homepage/frontend/src/components/workflow/` | ⭐⭐⭐⭐⭐ |

These 33 components are flagged for migration but marked as **100% fungible** (need refactoring).

---

## Summary: Current vs Planned State

| Aspect | Current | Planned |
|--------|---------|---------|
| **Views** | 2 (Chat, Workflow) | 4+ (Chat, Workflow, Observability, Quality) |
| **Graph Visualization** | ❌ None | react-force-graph 2D/3D |
| **Design System** | Hardcoded in components | Centralized tokens module |
| **Quality Scoring UI** | ❌ None | Real-time score bars with tooltips |
| **Question Wizard** | ❌ None | Step-by-step resolution flow |
| **Observability** | ❌ None | LangFuse/Phoenix trace viewer |
| **Migrated Components** | 2 views | 33+ from engineering-tools |