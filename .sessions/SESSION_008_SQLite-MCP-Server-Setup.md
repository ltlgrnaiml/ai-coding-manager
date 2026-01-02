# SESSION_008: SQLite MCP Server Setup

**Date**: 2026-01-02  
**Objective**: Configure SQLite MCP server for Windsurf/Cascade to enable direct database queries

---

## Work Completed

### 1. SQLite CLI Installation

- Installed `sqlite3` CLI tool via `sudo apt install sqlite3`
- Verified database access at `/home/mycahya/coding/ai-coding-manager/.workspace/knowledge.db`

### 2. Database Initialization

- Ran `init_database()` from `src.ai_dev_orchestrator.knowledge.database`
- Created all tables, triggers, and FTS5 indexes
- Confirmed 15 tables with proper schema

### 3. Virtual Environment Setup

- Created `.venv` at project root
- Installed `sentence-transformers` and dependencies (PyTorch, CUDA support)

### 4. MCP Server Configuration (Docker)

- **Problem**: Original `npx` config with UNC paths (`\\wsl.localhost\...`) caused 60-second timeout
- **Root Cause**: Windows Node.js cannot efficiently access WSL filesystem via UNC paths
- **Solution**: Switched to Docker-based MCP server with native WSL volume mounts

**Updated Config** (`/mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json`):

```json
"sqlite": {
  "command": "docker",
  "args": [
    "run", "--rm", "-i",
    "-v", "/home/mycahya/coding/ai-coding-manager/.workspace:/mcp",
    "mcp/sqlite",
    "--db-path", "/mcp/knowledge.db"
  ]
}
```

### 5. Verified MCP Server Functionality

- Successfully queried database via MCP tools
- Confirmed all tables accessible
- Retrieved chat session and document statistics

---

## Current Database Status

### Record Counts

| Table           | Records |
|-------|---------|
| documents | 65 |
| chunks | 3,232 |
| embeddings | 3,232 |
| chat_sessions | 31 |
| chat_messages | 483 |
| chat_source_files | 40 |
| relationships | 0 |
| llm_calls | 0 |
| message_embeddings | 0 |

### Document Types

| Type        | Count |
|------|-------|
| chat_record | 39 |
| document | 14 |
| discussion | 3 |
| plan | 3 |
| refactor | 2 |
| migration | 2 |
| adr | 1 |
| spec | 1 |

---

## Database Schema Summary

### Core Knowledge Tables

- **documents** → **chunks** → **embeddings** (1:N:N chain)
- **relationships** - Graph edges between documents (source_id, target_id, relationship_type)
- **content_fts** - FTS5 full-text search virtual table

### Chat System Tables

- **chat_sessions** → **chat_messages** → **message_embeddings** (1:N:N chain)
- **chat_source_files** - Tracks import provenance per session

### Utility Tables

- **llm_calls** - Tracks RAG query costs and token usage

---

## Configuration Files Modified

| File | Change |
|------|--------|
| `/mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json` | Updated sqlite server to use Docker |

---

## Handoff Notes

### Completed

- [x] SQLite CLI installed and working
- [x] Database initialized with full schema
- [x] Virtual environment created with sentence-transformers
- [x] MCP SQLite server configured via Docker
- [x] Verified MCP tools work (list_tables, describe_table, read_query)

### Next Steps

- [ ] Populate `relationships` table with document graph edges
- [ ] Generate `message_embeddings` for semantic chat search
- [ ] Implement `llm_calls` tracking for cost analysis
- [ ] Build chat quality grading system (per SESSION_007 handoff)

---

## Technical Notes

### Docker vs npx for WSL2 MCP Servers

| Aspect | npx (UNC paths) | Docker |
|--------|-----------------|--------|
| WSL filesystem access | Slow, unreliable | Native, fast |
| Timeout risk | High (60s+ common) | Low |
| Setup complexity | Simple config | Requires Docker running |
| Recommendation | ❌ Avoid for WSL | ✅ Preferred |

### Key Learnings

1. Windows processes (npx via Windsurf) cannot efficiently access WSL filesystems
2. Docker Desktop with WSL2 backend has native filesystem integration
3. MCP server timeout (60s) is a symptom of cross-filesystem latency

---

*Session active. MCP SQLite server operational.*
