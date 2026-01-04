# DISC-0005: P2RE — Prompt-to-Response Evaluator (Pillar 3)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: LLM observability, trace capture, prompt management, evaluation, lessons learned
> **Inherits Context**: `true`

---

## Summary

**P2RE (Prompt-to-Response Evaluator)** is AICM's Pillar 3 — the full observability layer for AI interactions. P2RE captures what was asked, what context was used, what was generated, what tools were called, and whether it worked. This enables debugging, improvement, cost tracking, and learning.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 4/10
- **What's Good**: Schema drafted, Lessons concept
- **What's Great**: Clear value proposition
- **Needs Enhancement**: Trace capture integration
- **Missing**: Full implementation

---

## Chain of Thought: What Does P2RE Capture?

```
User Message
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    P2RE TRACE CAPTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PROMPT CONSTRUCTION                                         │
│     ├── System prompt (AGENTS.md context)                       │
│     ├── Enriched context (from AIKH)                           │
│     ├── User message                                           │
│     └── Token count: input_tokens                              │
│                                                                 │
│  2. RAG RETRIEVAL (if any)                                      │
│     ├── Query embedding                                         │
│     ├── Retrieved documents                                     │
│     ├── Relevance scores                                        │
│     └── Time: retrieval_ms                                      │
│                                                                 │
│  3. LLM GENERATION                                              │
│     ├── Model ID                                                │
│     ├── Provider (anthropic, openai, xai)                      │
│     ├── Parameters (temperature, max_tokens)                    │
│     ├── Output content                                          │
│     ├── Token count: output_tokens                              │
│     ├── Time: generation_ms                                     │
│     └── Cost: calculated from tokens                            │
│                                                                 │
│  4. TOOL EXECUTION (if any)                                     │
│     ├── Tool name                                               │
│     ├── Arguments                                               │
│     ├── Result                                                  │
│     ├── Success/failure                                         │
│     └── Time: tool_ms                                           │
│                                                                 │
│  5. VALIDATION                                                  │
│     ├── Schema validation (if applicable)                       │
│     ├── User feedback (thumbs up/down)                         │
│     └── Auto-eval score (LLM-as-judge)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Response to User
```

---

## The Lessons Learned System

**Unique to P2RE**: When a problem is solved, capture the pattern for future reference.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LESSONS LEARNED                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PROBLEM                                                        │
│  ├── What went wrong?                                          │
│  ├── What was unclear?                                         │
│  └── Error message or symptom                                  │
│                                                                 │
│  DIAGNOSIS                                                      │
│  ├── How was root cause found?                                 │
│  ├── What tools/techniques used?                               │
│  └── Decision process                                          │
│                                                                 │
│  RESOLUTION                                                     │
│  ├── Steps taken to fix                                        │
│  ├── Code changes made                                         │
│  └── Verification method                                       │
│                                                                 │
│  PATTERN (Distilled)                                            │
│  ├── Reusable insight                                          │
│  ├── Keywords for search                                       │
│  └── Applicability conditions                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Auto-Suggest**: When similar problems are detected, surface relevant lessons.

---

## Assessment: What's Designed

### ✅ Schema Design (DRAFTED)

From archived PLAN-0008:

```sql
traces (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    model_id TEXT,
    provider TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    success BOOLEAN
);

trace_prompts (
    trace_id TEXT PRIMARY KEY REFERENCES traces(id),
    system_prompt TEXT,
    enriched_context TEXT,
    user_message TEXT
);

trace_responses (
    trace_id TEXT PRIMARY KEY REFERENCES traces(id),
    content TEXT,
    tool_calls TEXT,  -- JSON array
    finish_reason TEXT
);

lessons (
    id TEXT PRIMARY KEY,
    trace_id TEXT REFERENCES traces(id),
    problem TEXT,
    diagnosis TEXT,
    resolution TEXT,
    pattern TEXT,
    keywords TEXT,  -- JSON array for search
    created_at TEXT
);
```

### ✅ Value Proposition (CLEAR)

- **Debugging**: See exactly what AI received and produced
- **Cost Tracking**: Know spend per model, per session
- **Quality**: Correlate prompts with good/bad outputs
- **Learning**: Build knowledge base of solved problems

---

## Assessment: What's Missing

### 🔴 Trace Capture Hook (MISSING)

**Problem**: LLM calls don't automatically create traces.

**Needed**:
```python
class TracingLLMProvider(BaseLLMProvider):
    """Wrapper that captures traces for all LLM calls."""
    
    async def chat(self, messages, model_id, **kwargs):
        trace = Trace.start()
        
        try:
            response = await self._inner.chat(messages, model_id, **kwargs)
            trace.record_success(response)
        except Exception as e:
            trace.record_failure(e)
            raise
        finally:
            await self._save_trace(trace)
        
        return response
```

### 🔴 P2RE Database (MISSING)

**Problem**: No database exists for traces.

**Needed**:
- Create `~/.aikh/p2re.db`
- Initialize schema
- Retention policy (traces can be voluminous)

### 🔴 Trace Viewer UI (MISSING)

**Problem**: No way to view traces in frontend.

**Needed**:
- Trace list with filters
- Trace detail view
- Cost dashboard
- Lesson browser

### 🔴 Evaluation System (MISSING)

**Problem**: No automated quality scoring.

**Needed**:
- LLM-as-judge integration
- User feedback capture
- Quality trend tracking

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | Where to store P2RE data? | `open` | `~/.aikh/p2re.db` (separate from main) |
| Q-2 | What's the retention policy? | `open` | 30 days default, configurable |
| Q-3 | How to capture without latency impact? | `open` | Async write, buffer in memory |
| Q-4 | Which LLM evaluates quality? | `open` | Cheap model (Haiku, Flash) |
| Q-5 | How to link lessons to traces? | `open` | trace_id foreign key |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0007 | P2RE Database and Retention | Storage strategy |
| ADR-0008 | Trace Capture Architecture | How traces are recorded |
| ADR-0009 | Lessons Learned System | Pattern capture and retrieval |

---

## Implementation Priorities

### P1: Database & Models (Week 1)

- [ ] Create P2RE schema
- [ ] Initialize database
- [ ] Pydantic models for traces

### P2: Trace Capture (Week 2)

- [ ] TracingLLMProvider wrapper
- [ ] Integrate with existing providers
- [ ] Async trace saving

### P3: API Endpoints (Week 3)

- [ ] `/api/p2re/traces` — List, filter, get
- [ ] `/api/p2re/stats` — Usage statistics
- [ ] `/api/p2re/lessons` — CRUD for lessons

### P4: Frontend (Week 4)

- [ ] TraceViewer component
- [ ] Cost dashboard
- [ ] Lesson browser

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0004 (AIKH) | `soft` | `pending` | Lessons can enrich AIKH |
| DISC-0009 (AI Chat) | `hard` | `pending` | Chat triggers trace capture |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:
- P2RE as observability layer
- Lessons Learned as unique differentiator
- Trace capture without latency impact
- Integration with LLM provider layer

**Key Insights**:
- Async trace saving is critical for performance
- Lessons Learned could become most valuable feature
- Cost tracking enables optimization decisions

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for P2RE database, trace capture, lessons system)

---

*DISC-0005 | Child of DISC-0003 | SESSION_0017*
