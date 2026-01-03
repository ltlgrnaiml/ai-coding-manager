# DISC-0023: Artifact DB Auto-Sync System

> **Status**: `active`
> **Created**: 2026-01-02
> **Updated**: 2026-01-02
> **Author**: USER
> **AI Session**: -
> **Depends On**: DISC-011 (Unified Artifact Model), DISC-006 (Knowledge Archive RAG)
> **Blocks**: None
> **Dependency Level**: L1

---

## Summary

Design and implement an automatic artifact database synchronization system that initializes on Docker startup, performs initial DB refresh with current data, and monitors file system changes via watchdog to keep the artifact database in sync with the filesystem.

---

## Context

### Background

The Workflow Manager currently discovers artifacts by scanning the filesystem on-demand. However:

1. **Chat Logs** are stored in a separate folder (e.g., `.chat_logs/` or similar) and are NOT currently visible or searchable in the UI
2. **No automatic ingestion** - artifacts must be manually triggered for inclusion
3. **No change monitoring** - new or modified artifacts are not automatically detected
4. **No background sync** - the system relies on manual refresh

This creates a poor user experience where:
- Chat logs cannot be browsed alongside other artifacts
- New sessions/discussions/ADRs may not appear until manual refresh
- The artifact database can become stale

### Trigger

USER request to ensure Chat Logs are auto-absorbed into the Artifact DB with background task initialization and watchdog monitoring.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: On Docker container startup, initialize/verify artifact database schema
- [ ] **FR-2**: On startup, perform full scan and sync of all artifact directories
- [ ] **FR-3**: Include Chat Logs in artifact discovery (add CHAT_LOG artifact type)
- [ ] **FR-4**: Implement file system watchdog to monitor artifact directories for changes
- [ ] **FR-5**: Auto-ingest new artifacts when files are created
- [ ] **FR-6**: Auto-update artifact metadata when files are modified
- [ ] **FR-7**: Handle artifact deletion gracefully
- [ ] **FR-8**: Extract and index front matter/metadata for fast search

### Non-Functional Requirements

- [ ] **NFR-1**: Background sync should not block API responses
- [ ] **NFR-2**: Watchdog should detect changes within 5 seconds
- [ ] **NFR-3**: Startup sync should complete within 30 seconds for typical repo
- [ ] **NFR-4**: Memory footprint for watchdog < 50MB

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Where are chat logs currently stored? What folder structure? | `open` | |
| Q-2 | Should chat logs be parsed for structured metadata (turns, participants, timestamps)? | `open` | |
| Q-3 | Should we use SQLite for artifact metadata or keep it in-memory? | `open` | |
| Q-4 | How to handle large chat logs (>1MB)? Chunking strategy? | `open` | |
| Q-5 | Should watchdog run in same process or separate worker? | `open` | |

---

## Options Considered

### Option A: Startup Script + Watchdog Library

**Description**: Use Python `watchdog` library with startup initialization script.

```python
# On container start
async def on_startup():
    await init_artifact_db()
    await full_sync_all_artifacts()
    start_watchdog_observer()
```

**Pros**:
- Simple implementation
- Well-tested watchdog library
- Runs in-process

**Cons**:
- Single point of failure
- May miss events during heavy load

### Option B: Separate Sync Worker Process

**Description**: Run artifact sync as a separate microservice/worker.

**Pros**:
- Isolated from main API
- Can be restarted independently
- Better fault tolerance

**Cons**:
- More complex deployment
- IPC overhead

### Option C: Periodic Polling + Event Queue

**Description**: Poll filesystem every N seconds, queue changes for processing.

**Pros**:
- Works on all filesystems
- Predictable behavior
- No watchdog dependency

**Cons**:
- Higher latency for change detection
- More CPU usage from polling

### Recommendation

Start with **Option A** (in-process watchdog) for simplicity, with architecture that allows migration to Option B if needed.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   FastAPI   │    │  Artifact   │    │  Watchdog   │  │
│  │   Backend   │◄───┤   Service   │◄───┤  Observer   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                   │         │
│         ▼                  ▼                   ▼         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Artifact Database (SQLite)          │    │
│  │  - artifact_id, type, path, title, metadata     │    │
│  │  - FTS5 for full-text search                    │    │
│  │  - embeddings for semantic search               │    │
│  └─────────────────────────────────────────────────┘    │
│                           │                              │
│         ┌─────────────────┼─────────────────┐           │
│         ▼                 ▼                 ▼           │
│   .discussions/     .sessions/      .chat_logs/         │
│   .adrs/            .plans/         docs/guides/        │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Phase 1: Chat Log Integration
1. Add `CHAT_LOG` to ArtifactType enum
2. Add `.chat_logs/` to ARTIFACT_DIRECTORIES
3. Create ChatLogViewer component
4. Parse chat log metadata (date, participants, summary)

### Phase 2: Startup Sync
1. Create `artifact_sync_service.py`
2. Implement `init_artifact_db()` for schema creation
3. Implement `full_sync()` for startup population
4. Register as FastAPI lifespan event

### Phase 3: Watchdog Integration
1. Add `watchdog` to requirements
2. Implement `ArtifactWatchdogHandler` class
3. Start observer in background task
4. Handle create/modify/delete events

### Phase 4: Metadata Extraction
1. Improve front matter parsing for sessions
2. Add summary generation for chat logs
3. Index metadata in FTS5 for search

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-011 | `hard` | `active` | Artifact types | UAM defines artifact taxonomy |
| DISC-006 | `soft` | `active` | Search/RAG | Knowledge Archive provides search infra |
| DISC-0022 | `soft` | `active` | AIKH integration | Knowledge Hub for unified search |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | - | Artifact DB Sync Architecture | TBD |
| Contract | - | ArtifactSyncService API | TBD |
| Plan | - | Implement Auto-Sync System | TBD |

---

## Conversation Log

### 2026-01-02

**Topics Discussed**:
- Chat logs not visible in Workflow Manager UI
- Need for automatic DB initialization on startup
- Watchdog monitoring for file changes
- Better metadata extraction for sessions and chat logs

**Key Insights**:
- Chat logs are stored separately and not currently integrated
- Background sync is essential for good UX
- Tree-style navigation requested for document overview

**Action Items**:
- [ ] Add CHAT_LOG artifact type
- [ ] Implement startup sync
- [ ] Add watchdog monitoring
- [ ] Improve metadata extraction

---

## Resolution

**Resolution Date**: -

**Outcome**: -

**Next Steps**:
1. Implement CHAT_LOG artifact type
2. Create artifact sync service
3. Add watchdog observer

---

## Quality Score

**Status**: `[PENDING]` - Score calculated after required fields populated

---

*Template version: 2.0.0 | Per ADR-0048 (Unified Artifact Model)*
