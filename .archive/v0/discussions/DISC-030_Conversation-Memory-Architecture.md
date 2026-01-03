# DISC-030: Conversation Memory Architecture

**Status**: Active  
**Created**: 2026-01-03  
**Priority**: CRITICAL - Core Platform Feature

## Related Documents

- [DISC-0019: xAI-Gemini Agentic Capabilities](./DISC-0019_xAI-Gemini-Agentic-Capabilities.md)
- [DISC-0022: AI Knowledge Hub Architecture](./DISC-0022_AI-Knowledge-Hub-Architecture.md)
- [DISC-0024: Cross-Project ChatLogs Database](./DISC-0024_Cross-Project-ChatLogs-Database.md)
- [DISC-0026: Unified Model Registry Schema](./DISC-0026_Unified-Model-Registry-Schema.md)
- [DISC-006: Knowledge Archive RAG System](./DISC-006_Knowledge-Archive-RAG-System.md)
- [DISC-007: Unified xAI Agent Wrapper](./DISC-007_Unified-xAI-Agent-Wrapper.md)

---

## 1. Problem Statement

LLM APIs are **stateless** - they have no memory between calls. Every API request must include the full conversational context. As conversations grow, we face critical challenges:

1. **Context window limits** - Eventually history exceeds model capacity
2. **Cost optimization** - Sending irrelevant history wastes tokens/money
3. **RAG integration** - Knowledge must be injected at the right moment
4. **Agentic workflows** - Multiple agents need shared memory
5. **Debugging** - Need full visibility into what context was assembled
6. **Reproducibility** - Same inputs should produce same context

**This is the most important feature of our AI tool** - it determines the quality of every LLM interaction.

---

## 2. Design Principles

### 2.1 Deterministic Context Assembly

Every context assembly operation MUST be:
- **Hashable** - Produce identical hash for identical inputs
- **Reproducible** - Given same inputs, produce same output
- **Versioned** - Schema changes tracked for debugging
- **Auditable** - Full trace of what was included and why

### 2.2 Human-in-the-Loop

- User can inspect assembled context before sending
- User can override/pin specific memories
- User can exclude content from context
- User can see token counts and costs

### 2.3 Comprehensive Debugging

- Every context assembly logged to P2RE
- Diff view between assemblies
- Token attribution (what used how many tokens)
- Cache hit/miss visibility

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MEMORY ARCHITECTURE                               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                     MEMORY STORES                                    ││
│  │                                                                      ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ ││
│  │  │ EPISODIC    │  │ SEMANTIC    │  │ PROCEDURAL  │  │ WORKING     │ ││
│  │  │             │  │             │  │             │  │             │ ││
│  │  │ Chat history│  │ RAG content │  │ Tool usage  │  │ Current     │ ││
│  │  │ P2RE traces │  │ Research    │  │ patterns    │  │ session     │ ││
│  │  │ Sessions    │  │ Code chunks │  │ Agent roles │  │ state       │ ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                   CONTEXT ASSEMBLY ENGINE                            ││
│  │                                                                      ││
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐ ││
│  │  │ Retriever │  │ Ranker    │  │ Compressor│  │ Budget Allocator  │ ││
│  │  │           │  │           │  │           │  │                   │ ││
│  │  │ Query all │  │ Score by  │  │ Summarize │  │ Token limits      │ ││
│  │  │ stores    │  │ relevance │  │ if needed │  │ Priority queue    │ ││
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                   ASSEMBLED CONTEXT                                  ││
│  │                                                                      ││
│  │  {                                                                   ││
│  │    "context_id": "ctx_abc123",                                       ││
│  │    "context_hash": "sha256:...",                                     ││
│  │    "assembled_at": "2026-01-03T18:49:00Z",                          ││
│  │    "model_id": "grok-4-1-fast-reasoning",                           ││
│  │    "token_budget": 2000000,                                          ││
│  │    "tokens_used": 45230,                                             ││
│  │    "sections": [                                                     ││
│  │      { "type": "system", "tokens": 500, "hash": "..." },            ││
│  │      { "type": "memory", "tokens": 1200, "hash": "..." },           ││
│  │      { "type": "rag", "tokens": 3000, "hash": "..." },              ││
│  │      { "type": "history", "tokens": 40000, "hash": "..." },         ││
│  │      { "type": "user_message", "tokens": 530, "hash": "..." }       ││
│  │    ],                                                                ││
│  │    "messages": [...]                                                 ││
│  │  }                                                                   ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                    │                                     │
│                                    ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                   DEBUG & OBSERVABILITY                              ││
│  │                                                                      ││
│  │  - Full context logged to P2RE trace                                 ││
│  │  - Token attribution visible in UI                                   ││
│  │  - Cache hit/miss metrics                                            ││
│  │  - Context diff between requests                                     ││
│  │  - Replay capability for debugging                                   ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Memory Store Types

### 4.1 Episodic Memory (Chat History)
- **Source**: P2RE traces, chat sessions
- **Content**: Full message history with metadata
- **Retrieval**: Session-based, recency-weighted
- **Compression**: Summarization for old messages

### 4.2 Semantic Memory (Knowledge)
- **Source**: Research papers, code chunks, documentation
- **Content**: Embedded text chunks with vectors
- **Retrieval**: Semantic similarity search
- **Compression**: Already chunked

### 4.3 Procedural Memory (Skills)
- **Source**: Tool definitions, agent roles, workflows
- **Content**: System prompts, tool schemas
- **Retrieval**: Role/task based
- **Compression**: Versioned templates

### 4.4 Working Memory (Session State)
- **Source**: Current conversation
- **Content**: Variables, tool outputs, intermediate results
- **Retrieval**: Direct access
- **Compression**: None (always include)

---

## 5. Context Assembly Algorithm

```python
def assemble_context(
    session_id: str,
    user_message: str,
    model_id: str,
    budget_tokens: int,
    options: AssemblyOptions,
) -> AssembledContext:
    """
    Deterministic context assembly algorithm.
    
    Priority order (highest to lowest):
    1. System prompt (required)
    2. Working memory (current state)
    3. User message (current input)
    4. Pinned memories (user-specified)
    5. RAG results (semantic search)
    6. Recent history (sliding window)
    7. Summarized history (compressed)
    8. Related traces (cross-session)
    """
    
    # Phase 1: Gather candidates
    candidates = []
    candidates.extend(get_system_prompts(options.role))
    candidates.extend(get_working_memory(session_id))
    candidates.extend(get_pinned_memories(session_id))
    candidates.extend(search_semantic(user_message, options.rag_sources))
    candidates.extend(get_recent_history(session_id, options.history_limit))
    candidates.extend(get_summarized_history(session_id))
    candidates.extend(search_related_traces(user_message, session_id))
    
    # Phase 2: Score and rank
    scored = score_candidates(candidates, user_message, options)
    ranked = sorted(scored, key=lambda x: x.priority, reverse=True)
    
    # Phase 3: Budget allocation
    allocated = allocate_budget(ranked, budget_tokens, options)
    
    # Phase 4: Compress if needed
    compressed = compress_if_needed(allocated, budget_tokens)
    
    # Phase 5: Assemble final context
    context = build_messages(compressed)
    
    # Phase 6: Hash and log
    context_hash = compute_deterministic_hash(context)
    log_to_p2re(session_id, context, context_hash)
    
    return AssembledContext(
        context_id=generate_id(),
        context_hash=context_hash,
        messages=context,
        token_usage=compute_tokens(context),
        debug_info=build_debug_info(candidates, scored, allocated),
    )
```

---

## 6. Token Budget Allocation

| Priority | Category | Default % | Description |
|----------|----------|-----------|-------------|
| P0 | System Prompt | 5% | Role, instructions, constraints |
| P1 | Working Memory | 10% | Current session state |
| P2 | User Message | 5% | Current input (always full) |
| P3 | Pinned Memories | 10% | User-specified important context |
| P4 | RAG Results | 20% | Semantic search results |
| P5 | Recent History | 40% | Last N messages (full) |
| P6 | Summarized History | 5% | Compressed older history |
| P7 | Related Traces | 5% | Cross-session context |

---

## 7. Deterministic Hashing

Every context assembly produces a deterministic hash:

```python
def compute_deterministic_hash(context: AssembledContext) -> str:
    """
    SHA-256 hash of normalized context.
    
    Guarantees:
    - Same inputs → same hash
    - Order-independent for unordered sections
    - Ignores timestamps/IDs (content-only)
    """
    normalized = {
        "schema_version": "1.0.0",
        "sections": [
            {
                "type": section.type,
                "content_hash": sha256(section.content),
                "priority": section.priority,
            }
            for section in sorted(context.sections, key=lambda x: x.type)
        ]
    }
    return f"sha256:{sha256(json.dumps(normalized, sort_keys=True))}"
```

---

## 8. Agentic Communication

For multi-agent workflows, the memory system exposes:

```python
class AgentMemoryInterface:
    """Interface for agent-to-agent communication via shared memory."""
    
    def publish(self, key: str, value: Any, scope: Scope) -> None:
        """Publish to shared memory."""
    
    def subscribe(self, key: str, callback: Callable) -> None:
        """Subscribe to memory changes."""
    
    def get_agent_context(self, agent_id: str, task: str) -> AssembledContext:
        """Get context optimized for specific agent's role."""
    
    def handoff(self, from_agent: str, to_agent: str, state: dict) -> None:
        """Transfer working memory between agents."""
```

---

## 9. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/memory/sessions` | GET | List memory sessions |
| `/api/memory/sessions/{id}` | GET | Get session with history |
| `/api/memory/sessions/{id}/context` | POST | Assemble context |
| `/api/memory/sessions/{id}/memories` | GET/POST | Manage pinned memories |
| `/api/memory/search` | POST | Semantic search across stores |
| `/api/memory/debug/{context_id}` | GET | Get assembly debug info |
| `/api/memory/replay/{context_id}` | POST | Replay context assembly |
| `/api/memory/stats` | GET | Memory system statistics |

---

## 10. Database Schema

```sql
-- Memory sessions (conversations)
CREATE TABLE memory_sessions (
    id TEXT PRIMARY KEY,
    name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT,  -- JSON
    summary TEXT,   -- Compressed history
    summary_hash TEXT,
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0
);

-- Individual memories (messages, facts, etc.)
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES memory_sessions(id),
    type TEXT NOT NULL,  -- message, fact, tool_output, summary
    role TEXT,  -- user, assistant, system, tool
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding BLOB,  -- Vector for semantic search
    tokens INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,
    pinned BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL,
    metadata TEXT  -- JSON
);

-- Assembled contexts (for debugging/replay)
CREATE TABLE assembled_contexts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES memory_sessions(id),
    context_hash TEXT NOT NULL,
    model_id TEXT NOT NULL,
    token_budget INTEGER NOT NULL,
    tokens_used INTEGER NOT NULL,
    sections TEXT NOT NULL,  -- JSON array
    messages TEXT NOT NULL,  -- JSON array
    debug_info TEXT,  -- JSON
    created_at TEXT NOT NULL,
    trace_id TEXT  -- Link to P2RE trace
);

-- Indexes
CREATE INDEX idx_memories_session ON memories(session_id);
CREATE INDEX idx_memories_type ON memories(type);
CREATE INDEX idx_memories_pinned ON memories(pinned) WHERE pinned = TRUE;
CREATE INDEX idx_contexts_session ON assembled_contexts(session_id);
CREATE INDEX idx_contexts_hash ON assembled_contexts(context_hash);
```

---

## 11. Implementation Plan

### L1.1: Core Memory Models & Storage Layer
- [ ] Memory Pydantic models
- [ ] SQLite database schema
- [ ] CRUD operations
- [ ] Embedding storage

### L1.2: Context Assembly Engine
- [ ] Retrieval from all stores
- [ ] Scoring and ranking
- [ ] Budget allocation
- [ ] Compression strategies

### L1.3: RAG Integration Layer
- [ ] Research paper search
- [ ] Code chunk search
- [ ] Trace search
- [ ] Result formatting

### L1.4: Agentic Communication Interface
- [ ] Shared memory store
- [ ] Publish/subscribe
- [ ] Agent handoff
- [ ] Context specialization

### L1.5: Debug & Observability Layer
- [ ] Context logging to P2RE
- [ ] Token attribution
- [ ] Replay capability
- [ ] Debug endpoints

### L1.6: Frontend Integration
- [ ] Context preview panel
- [ ] Token budget visualization
- [ ] Memory pinning UI
- [ ] Debug view

---

## 12. Success Criteria

1. **Determinism**: Same inputs produce identical context hash
2. **Efficiency**: Context assembly < 100ms
3. **Visibility**: Full debug info available for every request
4. **Flexibility**: User can override any memory decision
5. **Scalability**: Handles 1M+ messages across sessions
6. **Integration**: Works with all existing RAG sources
7. **Agentic**: Supports multi-agent memory sharing
