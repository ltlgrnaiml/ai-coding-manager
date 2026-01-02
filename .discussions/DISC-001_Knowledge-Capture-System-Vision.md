# DISC-001: Knowledge Capture System Vision

> **ID**: DISC-001
> **Status**: active
> **Created**: 2025-12-31
> **Session**: SESSION_007

---

## Summary

Transform ai-dev-orchestrator from a simple workflow tool into a comprehensive **Agentic AI Coding Knowledge System** that captures best practices and working code snippets from engineering-tools, indexes everything in a rich SQLite database with embeddings, and intelligently selects the right prompt/context for the right model in the right situation to supplement L2/L3 plans with rich, relevant context for smaller models.

---

## Context

The ai-dev-orchestrator project needs to stay synchronized with innovations happening in the engineering-tools repository. Currently there's no automated way to track changes, capture working patterns, or provide context-aware assistance to AI models of varying capabilities. The goal is to build a knowledge capture system that makes smaller/budget models perform like premium models by providing them with relevant, verified code examples.

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Monitor engineering-tools git commits for relevant changes | High |
| FR-02 | Extract and index code snippets with quality signals | High |
| FR-03 | Detect and catalog reusable patterns from code | High |
| FR-04 | Store knowledge in SQLite database with FTS and embeddings | High |
| FR-05 | Provide context selection based on task type and target model | Medium |
| FR-06 | Track absorption status (what has ai-dev already adopted) | Medium |
| FR-07 | Support ML profiles for model-specific prompt strategies | Medium |
| FR-08 | Generate AI-readable TODO lists from sync reports | High |

---

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | Default mode must be deterministic (no LLM required) | High |
| NFR-02 | Real-time sync without requiring always-on server | High |
| NFR-03 | One-directional sync only (engineering-tools → ai-dev) | High |
| NFR-04 | Support configurable rules for what to capture | Medium |

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-01 | Embedding model: same as engineering-tools or different? | open | |
| Q-02 | Storage: single DB file or split by category? | open | |
| Q-03 | How to handle context window limits? | open | |
| Q-04 | How to version and track pattern evolution? | open | |

---

## Options Considered

### Option A: Git Hooks (Recommended)

**Description**: Use git post-commit hooks to notify ai-dev of changes.

**Pros**:
- Zero overhead when not committing
- No always-on server needed

**Cons**:
- Only captures committed changes
- Requires hook installation

### Option B: File Watcher (watchdog)

**Description**: Use Python watchdog to monitor for file changes.

**Pros**:
- Real-time on every save

**Cons**:
- Must be running to capture changes

---

## Decision

**Selected Option**: Option A (Git Hooks) with Option B as optional enhancement

**Rationale**: Git hooks provide zero-overhead real-time notification at commit granularity.

---

## Resulting Artifacts

| Type | ID | Title | Status |
|------|-----|-------|--------|
| Script | `scripts/sync_from_upstream.py` | Sync monitoring tool | created |
| Script | `sync.ps1` | PowerShell wrapper | created |
| Config | `.sync_rules.yaml` | Sync rules configuration | planned |

---

## Conversation Log

### SESSION_007 (2025-12-31)

- Discussed need for automated sync between repos
- USER clarified vision: Agentic AI Coding tool capturing best methods and snippets
- USER confirmed: ai-dev needs larger DB with ML profiles for context-aware prompt selection
- USER confirmed: LLM mode optional, default deterministic
- USER confirmed: one-directional sync only
- USER confirmed: real-time via git hooks preferred
- Created initial sync_from_upstream.py script
- Designed expanded database schema

---

## Resolution

**Resolution Date**: 
**Resolution Type**: 
**Outcome**: 

---

## Original Vision Document

### The Agentic AI Coding Assistant

### Core Concept

When engaging a smaller/budget model (L3 granularity), the system should be able to:

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Developer Request                         │
│  "Implement streaming SSE endpoint for chat"                     │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Context Selector (ML Profile)                  │
│                                                                  │
│  Input: Task description, target model, complexity score         │
│                                                                  │
│  Query Knowledge DB:                                             │
│  - "streaming SSE" → 3 working examples from engineering-tools   │
│  - "FastAPI endpoint" → 5 patterns with Google docstrings        │
│  - "chat implementation" → 2 complete implementations            │
│                                                                  │
│  Score & Rank by:                                                │
│  - Recency (newer = better)                                      │
│  - Verified working (has tests = higher score)                   │
│  - Similarity to current task                                    │
│  - Model capability match                                        │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Enriched L3 Plan Output                        │
│                                                                  │
│  Task: Implement streaming SSE endpoint                          │
│                                                                  │
│  Context Injected:                                               │
│  - REFERENCE: gateway/routes/chat.py:45-89 (working SSE)         │
│  - PATTERN: Always use `yield f"data: {json}\\n\\n"` format      │
│  - EXAMPLE: [complete code snippet from knowledge DB]            │
│  - CONSTRAINT: Must follow ADR-0037 observability patterns       │
│                                                                  │
│  This context is AUTOMATICALLY selected based on task + model    │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Matters

| Model Tier | Without Knowledge DB | With Knowledge DB |
|------------|---------------------|-------------------|
| **L1 (Premium)** | Can figure it out | Faster, consistent patterns |
| **L2 (Mid-tier)** | Needs hints | Gets working examples |
| **L3 (Budget)** | Often fails | Gets copy-paste snippets |

**Key Insight**: Smaller models aren't dumb - they just need more context. By capturing and indexing working code, we can make L3 models perform like L2.

---

## Database Schema (Expanded)

### Core Tables (from engineering-tools)

```sql
-- Existing: documents, chunks, embeddings, relationships, llm_calls
```

### New Tables for Agentic AI Coding

```sql
-- Working code snippets with metadata
CREATE TABLE code_snippets (
    id TEXT PRIMARY KEY,
    source_repo TEXT NOT NULL,           -- 'engineering-tools', 'ai-dev-orchestrator'
    file_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    content TEXT NOT NULL,
    language TEXT NOT NULL,              -- 'python', 'typescript', etc.
    
    -- Classification
    category TEXT NOT NULL,              -- 'api_endpoint', 'service', 'contract', 'test'
    tags TEXT,                           -- JSON array: ["streaming", "sse", "fastapi"]
    
    -- Quality signals
    has_tests BOOLEAN DEFAULT FALSE,
    has_docstring BOOLEAN DEFAULT FALSE,
    complexity_score INTEGER,            -- 1-10, computed
    
    -- Tracking
    captured_at TEXT DEFAULT (datetime('now')),
    last_verified TEXT,                  -- Last time tests passed
    source_commit TEXT,                  -- Git commit hash
    
    -- Embeddings
    embedding_id INTEGER REFERENCES embeddings(id)
);

-- Patterns: Generalized best practices
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                  -- 'SSE Streaming Pattern'
    description TEXT NOT NULL,
    
    -- Pattern definition
    template TEXT NOT NULL,              -- Code template with placeholders
    variables TEXT,                      -- JSON: {"endpoint": "string", "model": "string"}
    
    -- Usage context
    when_to_use TEXT,                    -- Natural language description
    when_not_to_use TEXT,
    
    -- Examples
    example_snippets TEXT,               -- JSON array of snippet IDs
    
    -- ADR/SPEC references
    related_adrs TEXT,                   -- JSON array: ["ADR-0037", "ADR-0043"]
    
    -- Tracking
    created_at TEXT DEFAULT (datetime('now')),
    usage_count INTEGER DEFAULT 0
);

-- ML Profiles: Model-specific prompt strategies
CREATE TABLE ml_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                  -- 'grok-3-mini-streaming'
    
    -- Model targeting
    model_family TEXT NOT NULL,          -- 'grok', 'claude', 'gpt', 'gemini'
    model_tier TEXT NOT NULL,            -- 'premium', 'mid', 'budget'
    
    -- Prompt strategy
    system_prompt_template TEXT,
    context_injection_strategy TEXT,     -- 'full', 'chunked', 'summary'
    max_context_tokens INTEGER,
    
    -- Behavior tuning
    temperature REAL DEFAULT 0.7,
    prefer_examples BOOLEAN DEFAULT TRUE,
    prefer_patterns BOOLEAN DEFAULT TRUE,
    
    -- Performance tracking
    success_rate REAL,
    avg_tokens_used INTEGER,
    last_updated TEXT
);

-- Task-Context mappings: What context works for what tasks
CREATE TABLE task_context_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Task classification
    task_type TEXT NOT NULL,             -- 'implement_endpoint', 'fix_bug', 'add_test'
    task_keywords TEXT,                  -- JSON array for matching
    
    -- Context selection
    snippet_query TEXT,                  -- FTS query to find relevant snippets
    pattern_ids TEXT,                    -- JSON array of pattern IDs
    required_adrs TEXT,                  -- JSON array of ADR IDs
    
    -- Model-specific overrides
    ml_profile_id TEXT REFERENCES ml_profiles(id),
    
    -- Effectiveness tracking
    times_used INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0
);

-- Absorption tracking: What has ai-dev already adopted
CREATE TABLE absorption_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    source_repo TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_commit TEXT,
    
    target_path TEXT,                    -- Where it was adopted in ai-dev
    adoption_type TEXT,                  -- 'direct_copy', 'adapted', 'inspired'
    
    absorbed_at TEXT DEFAULT (datetime('now')),
    notes TEXT
);

-- Sync state: Track what's been processed
CREATE TABLE sync_state (
    id INTEGER PRIMARY KEY,
    repo TEXT NOT NULL UNIQUE,
    last_commit TEXT,
    last_sync TEXT,
    files_processed INTEGER DEFAULT 0
);
```

---

## Real-Time Sync: Options

### Q5 Answer: How to do real-time without a server?

| Method | Requires Server | Pros | Cons |
|--------|-----------------|------|------|
| **File Watcher** | No | Simple, instant | Must be running |
| **Git Hooks** | No | Triggered on commit | Only on commits, not saves |
| **VS Code Extension** | No | Deep integration | IDE-specific |
| **Polling** | No | Simple | Delayed, wasteful |
| **Background Service** | Yes (light) | Always on | Resource usage |

### Recommended: Git Hooks + On-Demand

```
┌─────────────────────────────────────────────────────────────────┐
│                    engineering-tools repo                        │
│                                                                  │
│  .git/hooks/post-commit:                                         │
│  #!/bin/bash                                                     │
│  # Notify ai-dev-orchestrator of new commit                      │
│  echo $(git rev-parse HEAD) >> ~/.aidev/pending_syncs.txt        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ai-dev-orchestrator                            │
│                                                                  │
│  On startup / on-demand:                                         │
│  1. Check ~/.aidev/pending_syncs.txt                             │
│  2. Process new commits                                          │
│  3. Update knowledge DB                                          │
│  4. Clear pending file                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Alternative: Watchdog File Watcher

```python
# Can run as background process or on-demand
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.py', '.json', '.md')):
            # Queue for processing
            sync_queue.put(event.src_path)

# Start with: python -m aidev.sync --watch
```

**Recommendation**: Start with git hooks (zero overhead), add file watcher as optional feature.

---

## Sync Rules Configuration

```yaml
# .sync_rules.yaml

version: "1.0"
description: "Rules for syncing engineering-tools → ai-dev-orchestrator"

# Source configuration
source:
  repo: "../engineering-tools"
  type: "one-directional"  # engineering-tools → ai-dev only

# What to capture
capture:
  # Code snippets with quality signals
  snippets:
    paths:
      - "gateway/**/*.py"
      - "shared/contracts/**/*.py"
      - "scripts/workflow/**/*.py"
    
    # Only capture if these conditions are met
    filters:
      min_lines: 5
      max_lines: 200
      require_docstring: true
      require_type_hints: true
    
    # Quality boosters
    boost_if:
      - has_tests: +2
      - in_main_branch: +1
      - recently_modified: +1
  
  # Architecture artifacts
  artifacts:
    paths:
      - ".adrs/**/*.json"
      - "docs/specs/**/*.json"
      - ".plans/**/*.json"
      - ".discussions/**/*.md"
    
    # Always capture these
    always_include:
      - "AGENTS.md"
      - "docs/guides/AI_DEVELOPMENT_WORKFLOW.md"
  
  # Patterns to extract
  patterns:
    extract_from:
      - "gateway/services/*.py"      # Service patterns
      - "gateway/routes/*.py"        # API patterns
      - "shared/contracts/*.py"      # Contract patterns
    
    # Pattern detection rules
    detect:
      - name: "SSE Streaming"
        keywords: ["StreamingResponse", "yield", "text/event-stream"]
      - name: "Pydantic Contract"
        keywords: ["BaseModel", "Field", "validator"]
      - name: "FastAPI Endpoint"
        keywords: ["@router", "async def", "Response"]

# What to exclude
exclude:
  paths:
    - "apps/data_aggregator/**"      # DAT-specific (but capture patterns)
    - "apps/pptx_generator/**"       # PPTX-specific
    - "apps/sov_analyzer/**"         # SOV-specific
    - "tests/**"                     # Tests (unless paired with source)
    - "workspace/**"                 # Runtime data
    - ".venv/**"
    - "__pycache__/**"
  
  # But DO capture generalizable patterns from excluded paths
  capture_patterns_from_excluded: true

# Keyword-based priority
keywords:
  high_priority:
    - "xai"
    - "streaming"
    - "agent"
    - "orchestrat"
    - "workflow"
    - "plan"
    - "contract"
    - "embedding"
    - "knowledge"
  
  medium_priority:
    - "service"
    - "endpoint"
    - "api"
    - "pydantic"
  
  low_priority:
    - "util"
    - "helper"
    - "config"

# Generalization rules
generalize:
  # Replace specific names with placeholders
  replacements:
    "data_aggregator": "{tool_name}"
    "DAT": "{tool_acronym}"
    "engineering-tools": "{project_name}"
  
  # Extract patterns from tool-specific code
  extract_patterns: true

# Sync behavior
sync:
  mode: "git-hooks"        # 'git-hooks', 'file-watcher', 'polling', 'manual'
  
  # For git-hooks mode
  hooks:
    post_commit: true
    post_merge: true
  
  # For file-watcher mode (if enabled)
  watcher:
    debounce_ms: 1000
    batch_size: 10
  
  # Processing
  on_sync:
    - extract_snippets
    - update_embeddings
    - detect_patterns
    - generate_todo

# LLM integration (optional, default off)
llm:
  enabled: false           # Set to true to enable LLM-guided processing
  model: "grok-3-mini"
  tasks:
    - summarize_changes
    - suggest_absorptions
    - generate_pattern_docs
```

---

## Implementation Phases

### Phase 1: Enhanced Deterministic Sync (Now)
- [ ] Implement sync rules parser
- [ ] Add snippet extraction with quality signals
- [ ] Create expanded SQLite schema
- [ ] Add git hooks for real-time notification

### Phase 2: Knowledge Indexing
- [ ] Implement pattern detection
- [ ] Add embedding generation for snippets
- [ ] Build FTS indexes for code search
- [ ] Create absorption tracking

### Phase 3: ML Profile System
- [ ] Design profile schema
- [ ] Implement context selector
- [ ] Add task-context mappings
- [ ] Build effectiveness tracking

### Phase 4: Plan Enrichment
- [ ] Integrate with L2/L3 plan generation
- [ ] Auto-inject relevant snippets
- [ ] Add pattern references
- [ ] Track which context helped

### Phase 5: LLM-Guided Mode (Optional)
- [ ] Add LLM summarization
- [ ] Implement suggestion generation
- [ ] Build feedback loop for learning

---

## Open Questions

1. **Embedding Model**: Use same as engineering-tools (sentence-transformers) or different?
2. **Storage**: Single DB file or split by category?
3. **Context Window Management**: How to handle when selected context exceeds model limits?
4. **Pattern Versioning**: How to track pattern evolution over time?

---

## Next Steps

1. Create expanded database schema
2. Implement sync rules parser
3. Add git hooks to engineering-tools
4. Build snippet extraction with quality signals
5. Test end-to-end flow

