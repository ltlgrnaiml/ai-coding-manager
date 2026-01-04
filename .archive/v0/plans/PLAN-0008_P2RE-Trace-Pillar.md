# PLAN-0008: P2RE - Prompt-to-Response Evaluator

> **Status**: draft
> **Created**: 2025-01-03
> **Objective**: Establish P2RE as a first-class artifact pillar with dedicated database for LLM observability

---

## Overview

P2RE (Prompt-to-Response Evaluator) captures the full lifecycle of LLM interactions:
- **Prompts**: Templates, versions, system messages
- **Traces**: Individual LLM calls with full context
- **Responses**: Output content, tokens, latency
- **Evaluations**: Quality metrics, ratings, feedback
- **Lessons**: Solved problems, distilled solutions, reusable patterns

---

## Architecture

### New UAM Pillar

```
Six Pillars (existing):
  EXPLORE (DISC) → DECIDE (ADR) → DEFINE (SPEC) → 
  SHAPE (Contract) → EXECUTE (PLAN) → GUIDE

New Pillar:
  OBSERVE (P2RE) - LLM interaction observability
```

### Database: `~/.aikh/p2re.db`

Separate from artifacts.db to:
1. Allow independent scaling (traces can be voluminous)
2. Enable specialized indexing for trace queries
3. Support time-series patterns (retention, rollup)

### Schema

```
traces              - Individual LLM calls
├── prompts         - System/user prompt content
├── responses       - Model output
├── metrics         - Tokens, latency, cost
└── evaluations     - Quality scores

lessons             - Solved problems knowledge base
├── problem         - What went wrong / what was unclear
├── diagnosis       - Decision process for finding solution
├── resolution      - Steps taken to solve
└── pattern         - Distilled, reusable insight

prompt_templates    - Reusable prompt patterns
├── versions        - Version history
└── experiments     - A/B test assignments

sessions            - Conversation groupings
└── trace_sessions  - Links traces to sessions
```

---

## Milestones

### M1: Database & Models
- [ ] Create P2RE database schema
- [ ] Implement database initialization
- [ ] Create Pydantic models for P2RE artifacts

### M2: Service Layer
- [ ] P2RE service for CRUD operations
- [ ] Trace capture integration with LLM providers
- [ ] Automatic trace recording on chat requests

### M3: API Endpoints
- [ ] `/api/p2re/traces` - List, search, get traces
- [ ] `/api/p2re/prompts` - Prompt template management
- [ ] `/api/p2re/stats` - Usage statistics
- [ ] `/api/p2re/evaluations` - Quality feedback

### M4: Frontend Integration
- [ ] Add P2RE to artifact types in workflow.py
- [ ] Create TraceViewer component
- [ ] Integrate with ArtifactReader
- [ ] Add P2RE section to sidebar

### M5: Lessons Learned (Solved Problems)
- [ ] Create `lessons` table schema (problem, diagnosis, resolution, pattern)
- [ ] Link lessons to originating traces/sessions
- [ ] `/api/p2re/lessons` - CRUD for solved problems
- [ ] Pattern extraction - distill reusable insights from resolution
- [ ] Lesson search - semantic retrieval for similar problems
- [ ] Auto-suggest when context matches past solved problems
- [ ] LessonsViewer component in frontend

### M6: Phoenix Bridge (Optional)
- [ ] Import traces from Phoenix
- [ ] Sync mechanism for dual storage

---

## Success Criteria

1. All LLM calls automatically captured in P2RE database
2. Traces viewable as first-class artifacts in UI
3. Prompt templates manageable and versionable
4. Quality metrics trackable per model/prompt
5. Full lifecycle: Prompt → Trace → Response → Evaluation → Lesson
6. Lessons searchable and auto-suggested when similar problems encountered

---

## Files to Create/Modify

### New Files
- `backend/services/p2re/__init__.py`
- `backend/services/p2re/database.py` - Schema and init
- `backend/services/p2re/models.py` - Pydantic models
- `backend/services/p2re/service.py` - Business logic
- `backend/services/p2re/router.py` - API endpoints
- `contracts/devtools/p2re.py` - API contracts

### Modified Files
- `contracts/devtools/workflow.py` - Add TRACE artifact type
- `backend/main.py` - Register P2RE router
- `backend/services/llm/base.py` - Add trace capture hook
- Frontend components for trace viewing
