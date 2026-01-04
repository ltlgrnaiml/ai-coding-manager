# DISC-0004: AIKH — AI Knowledge Hub (Pillar 2)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: Knowledge database architecture, search unification, context enrichment, research integration
> **Inherits Context**: `true`

---

## Summary

The **AI Knowledge Hub (AIKH)** is AICM's Pillar 2 — the persistent, cross-project knowledge base that provides context to AI assistants. AIKH consolidates Chat Logs, Artifacts, and Research into a unified searchable corpus, enabling the "never repeat yourself" promise.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 6/10
- **What's Good**: Concept clear, Research DB exists
- **What's Great**: Foundation already built (sqlite, FTS5, embeddings)
- **Needs Enhancement**: Search unification, Context Enricher
- **Missing**: Full integration with chat flow

---

## Tree of Thought: AIKH Components

```
                    ┌─────────────────────────────────────┐
                    │         AI KNOWLEDGE HUB            │
                    │      "Everything searchable"        │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  CHAT LOGS    │         │   ARTIFACTS   │         │   RESEARCH    │
│     DB        │         │      DB       │         │      DB       │
├───────────────┤         ├───────────────┤         ├───────────────┤
│ Conversations │         │ DISCs, ADRs   │         │ Papers        │
│ User messages │         │ SPECs, Plans  │         │ Concepts      │
│ AI responses  │         │ Contracts     │         │ Citations     │
│ Timestamps    │         │ Guides        │         │ Embeddings    │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                    ┌─────────────────────────────────────┐
                    │        UNIFIED SEARCH ENGINE        │
                    ├─────────────────────────────────────┤
                    │  • Full-text (FTS5)                 │
                    │  • Semantic (embeddings)            │
                    │  • Hybrid (RRF fusion)              │
                    │  • Concept-based                    │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│   CONTEXT     │         │     AUTO      │         │    QUICK      │
│   ENRICHER    │         │   COMPLETE    │         │  REFERENCE    │
├───────────────┤         ├───────────────┤         ├───────────────┤
│ Injects into  │         │ @paper:       │         │ Side panel    │
│ AI prompts    │         │ @concept:     │         │ Drag-and-drop │
│ Relevant docs │         │ @disc:        │         │ Copy citation │
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## Assessment: What's Working

### ✅ Research Database (BUILT)

**Current Implementation**:
- SQLite with FTS5 full-text search
- Paper chunks with embeddings (sqlite-vec)
- Concept extraction and co-occurrence
- Citation graph
- ~90 papers indexed

**Location**: `backend/services/knowledge/`

### ✅ Embedding Infrastructure (READY)

**Current Implementation**:
- sentence-transformers for local embeddings
- GPU acceleration support (CUDA, MPS)
- Batch processing pipeline

### ✅ Search Foundations (PARTIAL)

**Current Implementation**:
- Full-text search via FTS5
- Semantic search via vector similarity
- Hybrid search with RRF fusion (Reciprocal Rank Fusion)

---

## Assessment: What Needs Enhancement

### 🟡 Chat Logs Integration (STUB)

**Current State**: Chat logs exist as files, not queryable.

**Enhancement Needed**:
- [ ] Parse `.chat_logs/*.md` into database
- [ ] Extract conversation turns
- [ ] Embed for semantic search
- [ ] Link to resulting artifacts

**Proposed Schema**:
```sql
chat_logs (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    created_at TEXT,
    file_modified_at TEXT
);

chat_turns (
    id INTEGER PRIMARY KEY,
    chat_log_id INTEGER REFERENCES chat_logs(id),
    turn_number INTEGER,
    role TEXT,  -- 'user' | 'assistant'
    content TEXT,
    timestamp TEXT
);

chat_embeddings (
    turn_id INTEGER PRIMARY KEY REFERENCES chat_turns(id),
    embedding BLOB  -- sqlite-vec format
);
```

### 🟡 Artifact Indexing (PARTIAL)

**Current State**: Artifacts exist as files, manually searchable.

**Enhancement Needed**:
- [ ] Auto-index on file change
- [ ] Extract metadata from frontmatter
- [ ] Cross-reference validation
- [ ] Embed content for semantic search

### 🟡 Unified Search API (MISSING)

**Current State**: Separate endpoints for papers vs artifacts.

**Enhancement Needed**:
- [ ] Single `/api/search` endpoint
- [ ] Type filter (chat, artifact, research)
- [ ] Relevance scoring across types
- [ ] Result highlighting

---

## Assessment: What's Missing

### 🔴 Context Enricher (MISSING)

**Problem**: AI prompts don't automatically include relevant knowledge.

**Needed**:
```python
def enrich_context(user_message: str) -> EnrichedContext:
    """Inject relevant knowledge into AI context."""
    
    # 1. Semantic search across all AIKH
    relevant = unified_search(user_message, top_k=5)
    
    # 2. Extract mentioned artifacts
    artifacts = extract_artifact_refs(user_message)
    
    # 3. Find related decisions
    decisions = find_related_adrs(relevant)
    
    # 4. Build enriched context
    return EnrichedContext(
        knowledge=relevant,
        artifacts=artifacts,
        decisions=decisions,
        token_budget=4000  # Configurable
    )
```

**Integration Point**: Called before every LLM request.

### 🔴 Cross-Project Knowledge (MISSING)

**Problem**: Knowledge is siloed per project.

**Needed**:
- Shared AIKH instance across projects
- Project tagging for filtering
- Permission model for shared knowledge

### 🔴 Autocomplete Integration (MISSING)

**Problem**: Chat panel doesn't suggest from knowledge base.

**Needed**:
- Real-time search as user types
- Trigger prefixes (`@paper:`, `@disc:`, etc.)
- Insert reference into message

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | Single DB or multiple DBs? | `open` | Multiple: chat.db, artifacts.db, research.db |
| Q-2 | Where to store AIKH data? | `open` | `~/.aikh/` for cross-project, `.aikh/` for local |
| Q-3 | How to handle embedding model changes? | `open` | Version field, re-embed on change |
| Q-4 | What's the token budget for context? | `open` | 4K default, configurable per model |
| Q-5 | How to prioritize search results? | `open` | Recency + relevance + type weighting |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0004 | AIKH Database Architecture | Storage strategy |
| ADR-0005 | Unified Search Strategy | Search unification |
| ADR-0006 | Context Enrichment Protocol | How context injection works |

---

## Implementation Priorities

### P1: Chat Log Parsing (Week 1)

- [ ] Create `chat_log_parser.py`
- [ ] Schema migration for chat tables
- [ ] Initial import of existing chat logs

### P2: Unified Search API (Week 2)

- [ ] Create `/api/search` endpoint
- [ ] Federated search across all DBs
- [ ] Result ranking with RRF

### P3: Context Enricher (Week 3)

- [ ] Implement `enrich_context()` function
- [ ] Integrate with LLM provider layer
- [ ] Test token budget management

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0005 (P2RE) | `soft` | `pending` | P2RE traces can enrich AIKH |
| DISC-0006 (Tap-In) | `hard` | `pending` | Tap-In consumes AIKH context |
| DISC-0009 (AI Chat) | `hard` | `pending` | Chat UI calls Context Enricher |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:
- AIKH architecture decomposition
- Chat log parsing as first priority
- Context Enricher as core differentiator
- Cross-project knowledge as future enhancement

**Key Insights**:
- Research DB is the strongest component (already built)
- Chat log integration unlocks the full loop
- Context Enricher is what makes "never repeat yourself" real

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for database architecture, search, context enrichment)

---

*DISC-0004 | Child of DISC-0003 | SESSION_0017*
