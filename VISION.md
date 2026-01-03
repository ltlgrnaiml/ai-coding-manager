# AICM Vision Statement

> **Version**: 0.1.0 (Genesis)  
> **Created**: 2026-01-03  
> **Status**: FOUNDATIONAL

---

## What IS the AICM?

**AICM (AI Coding Manager)** is not a tool. It is a **methodology-as-software** — a system that embodies the philosophy of AI-human collaborative development while simultaneously being built BY that philosophy.

### The Core Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                        THE AICM LOOP                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    CHAT LOGS (Raw Ore)                                              │
│         │                                                           │
│         ▼                                                           │
│    DISCUSSIONS (Refined Problems)                                   │
│         │                                                           │
│         ▼                                                           │
│    DECISIONS (Architectural Choices)                                │
│         │                                                           │
│         ▼                                                           │
│    SPECIFICATIONS (Behavioral Contracts)                            │
│         │                                                           │
│         ▼                                                           │
│    CODE (Implementation)                                            │
│         │                                                           │
│         ▼                                                           │
│    TRACES (Observability)                                           │
│         │                                                           │
│         └──────────────────► KNOWLEDGE ◄─────────────────┘          │
│                                   │                                 │
│                                   ▼                                 │
│                           NEXT CHAT LOG                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**AICM captures the full lifecycle of AI-assisted development:**
1. **Conversations become documents** → Chat logs refine into DISCs
2. **Documents become decisions** → DISCs crystallize into ADRs
3. **Decisions become contracts** → ADRs specify into SPECs and Contracts
4. **Contracts become code** → Contracts guide implementation
5. **Code becomes traces** → Execution generates observability data
6. **Traces become knowledge** → P2RE captures what happened and why
7. **Knowledge informs conversations** → AIKH enriches the next chat

---

## The Four Pillars of AICM

### 1. UAM — Unified Artifact Model

**What it is**: A deterministic documentation structure that traces every line of code back to a human decision.

**The Chain**: `DISC → ADR → SPEC → Contract → PLAN → Code`

**Why it matters**: No orphaned code. No mysterious decisions. Every implementation has provenance.

---

### 2. AIKH — AI Knowledge Hub

**What it is**: A persistent, cross-project knowledge base that provides context to AI assistants.

**Components**:
- **Chat Logs DB** — Raw conversation history (the source of truth)
- **Artifacts DB** — Structured documents (DISCs, ADRs, SPECs)
- **Research DB** — Academic papers, concepts, citations

**Why it matters**: AI never starts from zero. Every session has access to project history, decisions, and domain knowledge.

---

### 3. P2RE — Prompt-to-Result Execution Traces

**What it is**: Full observability of AI interactions — what was asked, what was retrieved, what was generated, what was executed.

**Captures**:
- Prompt construction (system + context + user)
- RAG retrieval (what knowledge was used)
- LLM generation (what was produced)
- Tool execution (what actions were taken)
- Result validation (did it work?)

**Why it matters**: Debugging AI behavior. Improving prompts. Understanding costs. Reproducing results.

---

### 4. Tap-In Protocol

**What it is**: The ability for any AI session to instantly understand a project by consuming its artifacts.

**How it works**:
1. AI reads `AGENTS.md` → Learns project rules
2. AI reads recent `.sessions/` → Understands current state
3. AI queries AIKH → Gets relevant context
4. AI follows UAM → Knows what artifacts to produce

**Why it matters**: Zero ramp-up time. Continuity across AI sessions. No context re-explaining.

---

## Why Is AICM Special?

### 1. Self-Documenting

AICM is being built WITH AICM. Every decision about AICM is captured as a DISC, crystallized as an ADR, specified as a SPEC. **The product documents itself as it evolves.**

### 2. Self-Informing

Projects built with AICM contribute knowledge back to AIKH. **The more you build, the smarter the system becomes.** Research papers, solved problems, architectural patterns — all indexed and retrievable.

### 3. Self-Propagating

Any project initialized with AICM structure automatically gains:
- Session continuity (AI remembers)
- Decision traceability (know why)
- Knowledge enrichment (context on demand)
- Quality enforcement (validated artifacts)

### 4. First-Principles Native

No legacy assumptions. No "we've always done it this way." Every design decision is questioned, documented, and justified. **The system evolves based on what works, not what existed.**

---

## The AICM Product Suite

### For Solo Developers (Current Focus)

```
┌─────────────────────────────────────────────────────┐
│                    AICM Solo                        │
├─────────────────────────────────────────────────────┤
│  • Local-first (SQLite, files on disk)             │
│  • IDE-agnostic (works with any AI assistant)      │
│  • Git-native (artifacts are version controlled)   │
│  • Zero external dependencies for basic use        │
└─────────────────────────────────────────────────────┘
```

### Future: AICM Cloud

```
┌─────────────────────────────────────────────────────┐
│                    AICM Cloud                       │
├─────────────────────────────────────────────────────┤
│  • Cross-project knowledge sharing                 │
│  • Team collaboration on artifacts                 │
│  • Centralized P2RE traces                         │
│  • Model routing and cost optimization             │
└─────────────────────────────────────────────────────┘
```

---

## What Makes a Project AICM-Compatible?

A project is **AICM-compatible** when an AI assistant can:

1. **Understand the rules** → `AGENTS.md` exists and defines behavior
2. **Track session state** → `.sessions/` captures AI continuity
3. **Follow the chain** → Artifacts link backward to chat logs
4. **Query knowledge** → AIKH can index and search the project
5. **Produce traces** → P2RE can observe AI interactions

### Minimum Requirements

| Requirement | Purpose | File/Folder |
|-------------|---------|-------------|
| **Project Rules** | AI behavior guidance | `AGENTS.md` |
| **Session Tracking** | AI continuity | `.sessions/` |
| **Chat Archive** | Raw conversation source | `.chat_logs/` or link to AIKH |
| **Artifact Chain** | Decision traceability | `.discussions/`, `.adrs/` |
| **Git Tracking** | Version control | `.git/` |

**5 requirements = AICM-compatible**

### Optional Enhancements

| Enhancement | Purpose | When Needed |
|-------------|---------|-------------|
| **Contracts** | Runtime validation | When data shapes matter |
| **Plans** | Execution tracking | When multi-step work exists |
| **Research** | Knowledge enrichment | When domain expertise needed |
| **P2RE** | Observability | When debugging AI behavior |

---

## The Vision in One Sentence

> **AICM is a self-documenting, self-informing system that captures the full lifecycle of AI-human collaborative development, ensuring every piece of code can be traced back to a human decision through a deterministic chain of artifacts.**

---

## What We Build Next

1. **Prove the loop** — Build AICM using AICM, from chat logs to working code
2. **Validate the chain** — Every artifact traces to a source
3. **Demonstrate tap-in** — New AI session understands project instantly
4. **Ship the scaffold** — `aicm init` creates compatible projects

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-01-03 | SESSION_017 | Genesis — foundational vision from first principles |
