# DISC-016: AI Context Prompt Generator

> **Status**: `active`
> **Created**: 2026-01-01
> **Updated**: 2026-01-01
> **Author**: USER
> **AI Session**: SESSION_024
> **Depends On**: DISC-006 (Knowledge Archive RAG)
> **Blocks**: None
> **Dependency Level**: L1

---

## Summary

Design a system that generates AI-optimized prompts with automatically nested context for AI tools that lack file system access but have large context windows. The system leverages RAG, memory, and reflection patterns to construct comprehensive prompts that give external AI tools the context they need to deliver high-quality responses.

---

## Context

### Background

The engineering-tools platform uses AI-assisted development extensively. While tools like Windsurf/Cascade have direct file system access and can explore codebases, many powerful AI tools (Claude API, ChatGPT, Gemini, etc.) operate in a "context-only" mode where:

1. They cannot access files directly
2. They have large context windows (100K-2M tokens)
3. They rely entirely on what's provided in the prompt

Currently, developers must manually:
- Copy/paste relevant code snippets
- Include architecture decisions
- Reference related files
- Structure the prompt for optimal AI comprehension

This is time-consuming and error-prone. A well-designed prompt generator could automate this.

### Trigger

USER request to explore a system that automatically constructs context-rich prompts for AI tools without file system access.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: System can analyze a developer's query/intent and identify relevant context
- [ ] **FR-2**: System retrieves relevant files, ADRs, specs, contracts from the codebase
- [ ] **FR-3**: System uses RAG to find semantically related content
- [ ] **FR-4**: System structures output as an AI-optimized prompt with nested context
- [ ] **FR-5**: System respects token limits and prioritizes most relevant context
- [ ] **FR-6**: System includes reflection/memory from previous sessions when relevant
- [ ] **FR-7**: Output prompt is copy-paste ready for external AI tools

### Non-Functional Requirements

- [ ] **NFR-1**: Generated prompts should be optimized for AI comprehension (per ADR-0034 patterns)
- [ ] **NFR-2**: Context retrieval should complete in <5 seconds for typical queries
- [ ] **NFR-3**: System should support multiple output formats (markdown, structured XML, etc.)

---

## Constraints

- **C-1**: Must work with existing codebase structure (ADRs, SPECs, contracts, etc.)
- **C-2**: Must integrate with existing Knowledge Archive/RAG infrastructure (DISC-006)
- **C-3**: No external API calls for context generation (all local processing)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | What prompt structure works best for different AI models? | `open` | |
| Q-2 | Should we support multiple "prompt profiles" for different tasks (code review, feature implementation, debugging)? | `open` | |
| Q-3 | How do we handle context that exceeds token limits? Summarization? Priority ranking? | `open` | |
| Q-4 | Should the system track which prompts led to successful outcomes (feedback loop)? | `open` | |
| Q-5 | What metadata should be included (file paths, line numbers, timestamps)? | `open` | |
| Q-6 | Should we support "prompt templates" that developers can customize? | `open` | |

---

## Options Considered

### Option A: CLI-Based Prompt Generator

**Description**: A command-line tool that takes a query and outputs a structured prompt to stdout/clipboard.

```bash
prompt-gen "Implement the new validation layer for profiles" --max-tokens 50000
```

**Pros**:
- Simple to implement
- Easy to integrate into any workflow
- No UI overhead

**Cons**:
- Less discoverable
- No visual preview of included context

### Option B: DevTools UI Integration

**Description**: Integrate into the existing DevTools Workflow Manager UI with a dedicated "Prompt Builder" panel.

**Pros**:
- Visual context selection
- Preview before copy
- Integrated with existing artifact browser

**Cons**:
- More complex implementation
- Requires frontend work

### Option C: Hybrid (CLI + API + UI)

**Description**: Build as a service with API endpoints, CLI wrapper, and optional UI.

**Pros**:
- Maximum flexibility
- Can be used programmatically
- Supports all use cases

**Cons**:
- Most complex to implement
- May be over-engineering for initial use case

### Recommendation

Start with **Option A** (CLI) with API layer, leaving room to add UI later.

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Primary interface (CLI vs UI vs API) | `pending` | |
| D-2 | Prompt output format (Markdown, XML, custom) | `pending` | |
| D-3 | Context retrieval strategy (RAG-only, hybrid, rule-based) | `pending` | |
| D-4 | Token budget allocation strategy | `pending` | |

---

## Scope Definition

### In Scope

- Query analysis and intent detection
- Codebase context retrieval (files, ADRs, contracts)
- RAG-based semantic search integration
- Prompt structure optimization
- Token budget management
- Copy-paste ready output

### Out of Scope

- Direct integration with external AI APIs (user handles that)
- Real-time streaming to AI tools
- Response parsing/handling from AI tools
- Training custom models

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-006 | `soft` | `active` | RAG retrieval | Knowledge Archive provides embedding/search infrastructure |
| DISC-015 | `soft` | `active` | Documentation context | AI-native docs format helps with context generation |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | - | - | TBD |
| Contract | - | - | TBD |
| Plan | - | - | TBD |

---

## Conversation Log

### 2026-01-01 - SESSION_024

**Topics Discussed**:
- Initial concept for AI prompt generator
- Use case: AI tools without file system access but with large context windows
- RAG/Memory/Reflection integration

**Key Insights**:
- Many powerful AI tools can't access files directly
- Manual context copying is tedious and error-prone
- System should automate context selection and prompt structuring

**Action Items**:
- [ ] Define prompt structure patterns for different AI models
- [ ] Explore integration with existing RAG infrastructure
- [ ] Prototype context retrieval logic

---

## Resolution

**Resolution Date**: -

**Outcome**: -

**Next Steps**:
1. TBD

---

## Quality Score

**Status**: `[PENDING]` - Score calculated after required fields populated

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
