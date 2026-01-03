# DISC-0024: Cross-Project Chat Logs Database Architecture

> **Status**: `active`
> **Created**: 2026-01-02
> **Updated**: 2026-01-02
> **Author**: USER
> **AI Session**: -
> **Depends On**: DISC-0023 (Artifact DB Auto-Sync), DISC-0022 (AI Knowledge Hub)
> **Blocks**: Chat Log Viewer implementation
> **Dependency Level**: L1

---

## Summary

Define the architecture for managing cross-project AI chat logs stored at `/home/mycahya/coding/ChatLogs/`. This decision addresses whether chat logs should be stored in a separate database (isolated from per-project artifact DBs), the schema design, ingestion pipeline, and integration with the Workflow Manager.

---

## Context

### Background

AI-assisted development generates valuable chat logs from tools like Windsurf/Cascade, ChatGPT, Claude, etc. These logs:

1. **Are cross-project in scope** - A single chat may reference multiple repositories
2. **Contain structured conversations** - User inputs, AI responses, tool calls, file references
3. **Are a knowledge asset** - Past solutions, architectural decisions, debugging sessions
4. **Currently exist as markdown files** - ~50 files totaling ~3.5MB at `/home/mycahya/coding/ChatLogs/`

### Current State

| Metric | Value |
|--------|-------|
| Total Files | ~50 markdown files |
| Size Range | 2KB - 334KB per file |
| Total Size | ~3.5MB |
| Format | Markdown with `### User Input` / `### Planner Response` sections |
| Location | `/home/mycahya/coding/ChatLogs/` (outside any single project) |

### Trigger

USER request to integrate chat logs into the Workflow Manager with searchability, recognizing this requires an architectural decision about database isolation.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Ingest all existing chat log files from the ChatLogs folder
- [ ] **FR-2**: Parse markdown structure to extract user/assistant turns
- [ ] **FR-3**: Extract metadata: topics, file references, commands executed
- [ ] **FR-4**: Enable full-text search across all chat logs
- [ ] **FR-5**: Enable GPU-accelerated semantic search across chat content
- [ ] **FR-6**: Display chat logs in Workflow Manager with dedicated viewer
- [ ] **FR-7**: Support cross-project queries (find chats mentioning any project)
- [ ] **FR-8**: Monitor ChatLogs folder for new files (watchdog)

### Non-Functional Requirements

- [ ] **NFR-1**: Database should be independent of any single project
- [ ] **NFR-2**: Startup sync should complete within 60 seconds for full corpus
- [ ] **NFR-3**: Search latency < 500ms for typical queries
- [ ] **NFR-4**: Support future growth to 500+ chat logs

---

## Architectural Decision: Separate Database

### The Question

Should chat logs be stored in:
- **Option A**: AICM's existing `research_papers.db`
- **Option B**: A new project-local `chatlogs.db` within AICM
- **Option C**: A separate cross-project `ChatLogs.db` at a central location

### Analysis

| Factor | Option A (research_papers.db) | Option B (local chatlogs.db) | Option C (central ChatLogs.db) |
|--------|-------------------------------|------------------------------|--------------------------------|
| **Scope Alignment** | ❌ Mixes research + chats | ⚠️ Ties to AICM only | ✅ Cross-project by design |
| **Isolation** | ❌ Shared failure domain | ✅ Isolated | ✅ Isolated |
| **Portability** | ❌ Coupled to AICM | ⚠️ Requires AICM | ✅ Can be used by any tool |
| **Complexity** | ✅ No new DB | ⚠️ One more DB in project | ⚠️ External dependency |
| **Backup** | ⚠️ Mixed concerns | ✅ Clear | ✅ Clear |
| **GPU Embeddings** | ✅ Existing infra | ⚠️ Need new table | ⚠️ Need new table |

### Recommendation: **Option C - Central ChatLogs.db**

**Rationale**:

1. **Cross-project nature**: Chat logs span multiple repositories; they don't belong to any single project
2. **Single Source of Truth**: One database for all chat history, queryable from any project
3. **Separation of Concerns**: Research papers are academic knowledge; chat logs are operational knowledge
4. **Future-proof**: Other tools (engineering-tools, new projects) can query the same DB
5. **Independent lifecycle**: Chat logs DB can be backed up, migrated, or upgraded independently

**Location**: `/home/mycahya/coding/ChatLogs/chathistory.db`

This keeps the database alongside the source markdown files, making the folder self-contained.

---

## Cross-Device Portability Architecture

### The Challenge

The user needs access to chat logs and research papers across multiple devices (workstation, laptop, etc.). This requires a clear separation between:

1. **Portable Source Data** - The actual content that must travel with the user
2. **Generated Databases** - Derived artifacts that can be regenerated locally

### Architecture Decision: Source-First Portability

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PORTABLE (Sync Across Devices)                   │
├─────────────────────────────────────────────────────────────────────┤
│  /home/mycahya/coding/ChatLogs/                                     │
│  ├── *.md (50 chat log files, ~3.5MB)      ← SOURCE OF TRUTH       │
│  └── .gitignore (excludes *.db files)                               │
│                                                                     │
│  /home/mycahya/coding/AI Papers/                                    │
│  ├── *.pdf (research papers)               ← SOURCE OF TRUTH       │
│  └── extracted_papers/ (optional, can regenerate)                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                 GENERATED (Device-Local, Regenerable)               │
├─────────────────────────────────────────────────────────────────────┤
│  /home/mycahya/coding/ChatLogs/                                     │
│  └── chathistory.db        ← GENERATED, in .gitignore               │
│                                                                     │
│  /home/mycahya/coding/AI Papers/                                    │
│  └── research_papers.db    ← GENERATED, in .gitignore               │
└─────────────────────────────────────────────────────────────────────┘
```

### Sync Strategy

| Resource | Sync Method | Notes |
|----------|-------------|-------|
| `ChatLogs/*.md` | Cloud sync (OneDrive, Dropbox, Syncthing) | ~3.5MB, syncs quickly |
| `AI Papers/*.pdf` | Cloud sync | Larger (~500MB+), sync selectively |
| `chathistory.db` | **DO NOT SYNC** | Regenerate on each device |
| `research_papers.db` | **DO NOT SYNC** | Regenerate on each device |

### Why Not Sync Databases?

1. **SQLite lock conflicts** - Concurrent access from sync clients causes corruption
2. **Platform differences** - WAL files, page sizes may differ
3. **Regeneration is cheap** - Initial ingest takes <60 seconds
4. **Embeddings are expensive** - GPU embeddings should be generated per-device anyway

### Device Bootstrap Workflow

When setting up a new device:

```bash
# 1. Clone AICM repo
git clone https://github.com/ltlgrnaiml/ai-coding-manager.git

# 2. Sync ChatLogs and AI Papers folders from cloud storage
# (OneDrive, Dropbox, or Syncthing)

# 3. Create symlinks in AICM workspace
cd ai-coding-manager
ln -s /path/to/ChatLogs ./ChatLogs
ln -s /path/to/AI\ Papers ./AI_Papers

# 4. Regenerate databases (runs automatically on first API call, or manually):
uv run python -m ai_dev_orchestrator.knowledge.chatlog_parser /path/to/ChatLogs

# 5. (Optional) Generate GPU embeddings if device has GPU
uv run python scripts/gpu_batch_embedder.py
```

### Folder Structure for Portability

Both `ChatLogs/` and `AI Papers/` should have a `.gitignore` to exclude generated files:

```gitignore
# ChatLogs/.gitignore
*.db
*.db-shm
*.db-wal
```

```gitignore
# AI Papers/.gitignore
*.db
*.db-shm
*.db-wal
extracted_papers/  # Optional: include if you want to avoid re-extraction
```

### Environment Variable Overrides

For flexibility across devices with different paths:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHATLOG_DB_PATH` | `<ChatLogs>/chathistory.db` | Override database location |
| `CHATLOG_SOURCE_PATH` | `/home/mycahya/coding/ChatLogs` | Source markdown files |
| `PAPERS_DB_PATH` | `<AI Papers>/research_papers.db` | Research papers DB |
| `PAPERS_SOURCE_PATH` | `/home/mycahya/coding/AI Papers` | Source PDF files |

---

## Database Schema Design

### Tables

```sql
-- Core chat log table
CREATE TABLE chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    title TEXT,
    file_size INTEGER,
    created_date TEXT,
    modified_date TEXT,
    turn_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    projects_referenced TEXT,  -- JSON array of project names
    ingested_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Individual conversation turns
CREATE TABLE chat_turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_index INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    has_code_blocks INTEGER DEFAULT 0,
    has_file_refs INTEGER DEFAULT 0,
    has_commands INTEGER DEFAULT 0,
    UNIQUE(chat_log_id, turn_index)
);

-- Extracted file references
CREATE TABLE chat_file_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    project_name TEXT
);

-- Extracted commands
CREATE TABLE chat_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    was_accepted INTEGER DEFAULT 0
);

-- GPU embeddings for semantic search
CREATE TABLE chat_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_log_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
    turn_id INTEGER REFERENCES chat_turns(id),
    embedding BLOB NOT NULL,
    embedding_model TEXT DEFAULT 'all-mpnet-base-v2',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 full-text search
CREATE VIRTUAL TABLE chat_fts USING fts5(
    title,
    content,
    content_rowid='id',
    tokenize='porter'
);
```

### Indexes

```sql
CREATE INDEX idx_chat_logs_filename ON chat_logs(filename);
CREATE INDEX idx_chat_logs_modified ON chat_logs(modified_date);
CREATE INDEX idx_chat_turns_role ON chat_turns(role);
CREATE INDEX idx_chat_turns_chat_log ON chat_turns(chat_log_id);
CREATE INDEX idx_chat_file_refs_path ON chat_file_refs(file_path);
CREATE INDEX idx_chat_file_refs_project ON chat_file_refs(project_name);
```

---

## Ingestion Pipeline

### Phase 1: Initial Ingest

```
ChatLogs/*.md → Parser → chat_logs + chat_turns → FTS index
                                ↓
                        chat_file_refs, chat_commands
```

### Phase 2: GPU Embeddings

```
chat_turns.content → GPU Embedder → chat_embeddings
chat_logs (title + summary) → GPU Embedder → chat_embeddings (log-level)
```

### Phase 3: Watchdog Monitoring

```
Watchdog Observer → File Created/Modified → Re-ingest → Update FTS + Embeddings
```

---

## Integration with AICM

### Backend

1. **New service**: `backend/services/chatlog_service.py`
   - Connect to external `ChatLogs.db`
   - Provide search, list, get endpoints
   - GPU embedding integration

2. **New API routes**: `/api/devtools/chatlogs/*`
   - `GET /chatlogs` - List all chat logs
   - `GET /chatlogs/{id}` - Get single chat log with turns
   - `POST /chatlogs/search` - Full-text + semantic search
   - `POST /chatlogs/sync` - Trigger manual sync

### Frontend

1. **New artifact type**: `CHAT_LOG` in `ArtifactType` enum
2. **New tab**: Chat Logs tab in Workflow Sidebar
3. **New viewer**: `ChatLogViewer` component with:
   - Conversation thread view
   - Search within chat
   - File reference links
   - Copy code blocks

### Docker

1. Mount ChatLogs folder as volume: `/home/mycahya/coding/ChatLogs:/chatlog`
2. Configure DB path via environment variable: `CHATLOG_DB_PATH=/chatlogs/chathistory.db`

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should we support chat logs from multiple AI tools with different formats? | `open` | |
| Q-2 | Should embeddings be stored in the same DB or a separate embeddings-only file? | `resolved` | Same DB for simplicity |
| Q-3 | How to handle very large chat logs (>500KB)? Chunking strategy? | `open` | |
| Q-4 | Should we extract and index code blocks separately? | `open` | |
| Q-5 | Privacy: Should we support redaction of sensitive content? | `open` | |

---

## Implementation Plan

### Phase 1: Database Setup (This Session)

1. Create `chatlog_database.py` with schema initialization
2. Create `chatlog_parser.py` for markdown parsing
3. Initial bulk ingest of all existing files
4. FTS5 indexing

### Phase 2: API Integration

1. Add `chatlog_service.py` with FastAPI routes
2. Add `CHAT_LOG` artifact type
3. Mount volume in docker-compose.yml

### Phase 3: Frontend

1. Add Chat Logs tab to sidebar
2. Create `ChatLogViewer` component
3. Integrate with search

### Phase 4: GPU Embeddings

1. Batch embed all chat logs
2. Add semantic search endpoint
3. "Related Chats" feature

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-0023 | `soft` | `active` | Watchdog pattern | Artifact sync architecture |
| DISC-0022 | `soft` | `active` | Search integration | AIKH unified search |
| DISC-011 | `soft` | `active` | Artifact types | UAM artifact taxonomy |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-0050 | Cross-Project ChatLogs Database | TBD |
| Contract | - | ChatLogService API | TBD |
| Plan | PLAN-0006 | Implement ChatLogs Integration | TBD |

---

## Conversation Log

### 2026-01-02

**Topics Discussed**:

- Cross-project nature of chat logs
- Architectural decision: separate DB vs integrated
- Schema design with FTS5 and GPU embeddings
- Integration approach with AICM Workflow Manager

**Key Insights**:

- Chat logs are operational knowledge, distinct from research papers
- Cross-project scope requires independent database
- ~50 files, ~3.5MB total - manageable for single SQLite DB
- Markdown format with `### User Input` / `### Planner Response` structure

**Decision**:

- **Approved Option C**: Separate `ChatLogs.db` at `/home/mycahya/coding/ChatLogs/chathistory.db`

---

## Resolution

**Resolution Date**: 2026-01-02

**Outcome**: Proceed with Option C - Central ChatLogs.db

**Next Steps**:

1. Create database schema and initialization script
2. Implement markdown parser for Cascade format
3. Bulk ingest existing files
4. Integrate with AICM backend/frontend

---

## Quality Score

**Status**: `[APPROVED]` - Architectural decision made, ready for implementation

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
