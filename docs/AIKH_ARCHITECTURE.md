# AI Knowledge Hub (AIKH) Architecture

> **Version**: 1.0.0  
> **Last Updated**: 2026-01-02

---

## Overview

The AI Knowledge Hub (AIKH) is a centralized, cross-platform knowledge management system designed to support AI-assisted development workflows. It provides persistent storage for documents, chat histories, and research materials with full-text search and semantic embeddings.

---

## Core Components

### 1. Artifacts Database (`artifacts.db`)

**Purpose**: Primary RAG (Retrieval-Augmented Generation) store for project artifacts.

| Table | Description |
|-------|-------------|
| `documents` | ADRs, specs, plans, discussions, contracts |
| `chunks` | Document chunks for retrieval |
| `embeddings` | Vector embeddings for semantic search |
| `relationships` | Document-to-document links (graph) |
| `llm_calls` | LLM query/response history |
| `content_fts` | FTS5 full-text search index |

### 2. Chat Logs Database (`chatlogs.db`)

**Purpose**: Cross-project conversation history for context retrieval.

| Table | Description |
|-------|-------------|
| `chat_logs` | Source files and metadata |
| `chat_turns` | Individual conversation turns |
| `chat_file_refs` | Extracted file references |
| `chat_commands` | Extracted shell commands |
| `chat_embeddings` | Turn embeddings for search |
| `chat_fts` | FTS5 full-text search index |

### 3. Research Database (`research.db`)

**Purpose**: Academic paper storage with rich metadata and PDF archival.

| Table | Description |
|-------|-------------|
| `research_papers` | Paper metadata (arXiv, DOI, authors) |
| `paper_sections` | Structured sections (intro, methods, etc.) |
| `paper_chunks` | Chunks for RAG integration |
| `paper_embeddings` | Semantic embeddings |
| `paper_images` | Extracted figures (BLOB storage) |
| `paper_tables` | Extracted tables |
| `paper_citations` | Citation relationships |
| `paper_categories` | Topic classification |
| `paper_files` | PDF files (BLOB storage) |
| `research_fts` | FTS5 full-text search index |

---

## Directory Structure

```
~/.aikh/                      # AIKH Home (per-machine)
├── config.json               # AIKH configuration
├── artifacts.db              # Artifacts database
├── chatlogs.db               # Chat logs database
└── research.db               # Research papers database
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIKH_HOME` | `~/.aikh` | AIKH home directory |
| `CHATLOG_DB_PATH` | `$AIKH_HOME/chatlogs.db` | Chat logs database path |

---

## Cross-Platform Support

### Path Resolution

```python
from pathlib import Path
import os

def get_aikh_home() -> Path:
    # 1. Environment variable
    if env := os.environ.get("AIKH_HOME"):
        return Path(env)
    # 2. Docker mount
    if Path("/aikh").exists():
        return Path("/aikh")
    # 3. User home
    return Path.home() / ".aikh"
```

### Platform Paths

| Platform | AIKH Home |
|----------|-----------|
| macOS | `/Users/<user>/.aikh/` |
| Linux/WSL2 | `/home/<user>/.aikh/` |
| Windows | `C:\Users\<user>\.aikh\` |
| Docker | `/aikh/` |

---

## GPU Acceleration

### Strategy

All embedding and inference operations use **GPU-first** execution:

1. **CUDA** (NVIDIA) - Windows/Linux with RTX 5090
2. **MPS** (Metal) - macOS with Apple Silicon M4 Max
3. **CPU** - Fallback when no GPU available

### Configuration Module

```python
# src/ai_dev_orchestrator/knowledge/aikh_config.py

def get_torch_device() -> str:
    """Returns 'cuda', 'mps', or 'cpu'"""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"
```

### Hardware Specifications

| Platform | Hardware | VRAM/Memory | Framework |
|----------|----------|-------------|-----------|
| Windows/WSL2 | RTX 5090 | 32GB GDDR7 | CUDA 12.x |
| macOS | M4 Max | Unified (up to 128GB) | MPS |

---

## Database Schema Features

### Full-Text Search (FTS5)

All databases use SQLite FTS5 with Porter stemming:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
    title, content, doc_id UNINDEXED,
    content='documents',
    content_rowid='rowid',
    tokenize='porter'
);
```

### Vector Embeddings

Embeddings stored as BLOBs with model metadata:

```sql
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY,
    chunk_id INTEGER NOT NULL,
    vector BLOB NOT NULL,        -- numpy array as bytes
    model TEXT NOT NULL,         -- e.g., 'all-mpnet-base-v2'
    dimensions INTEGER NOT NULL, -- e.g., 768
    created_at TEXT DEFAULT (datetime('now'))
);
```

### Write-Ahead Logging (WAL)

All databases use WAL mode for concurrent access:

```python
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA foreign_keys = ON")
```

---

## Initialization

### Manual Initialization

```bash
# From project root
python scripts/init_aikh_databases.py
```

### Programmatic Initialization

```python
from ai_dev_orchestrator.knowledge.database import init_database
from ai_dev_orchestrator.knowledge.chatlog_database import init_database as init_chatlogs
from ai_dev_orchestrator.knowledge.research_database import init_research_database

# Initialize all databases
init_database()           # artifacts.db
init_chatlogs()           # chatlogs.db
init_research_database()  # research.db
```

---

## Docker Integration

### Volume Mounting

```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ~/.aikh:/aikh  # Mount AIKH home
    environment:
      - AIKH_HOME=/aikh
```

### Container Paths

Inside Docker containers, AIKH uses `/aikh/` as the home directory when the volume is mounted.

---

## Migration Notes

### From Legacy Paths

| Old Path | New Path |
|----------|----------|
| `.workspace/knowledge.db` | `~/.aikh/artifacts.db` |
| `/home/mycahya/coding/ChatLogs/chathistory.db` | `~/.aikh/chatlogs.db` |
| `.workspace/research_papers.db` | `~/.aikh/research.db` |

### Migration Script

```bash
# Backup old databases
cp .workspace/knowledge.db ~/.aikh/artifacts.db
cp .workspace/research_papers.db ~/.aikh/research.db

# Re-initialize to add any new tables
python scripts/init_aikh_databases.py
```

---

## Related Documentation

- [CONCURRENT_DEVELOPMENT_POLICY.md](./CONCURRENT_DEVELOPMENT_POLICY.md) - Cross-platform workflow
- [README.md](../README.md) - Project overview
- [AGENTS.md](../AGENTS.md) - AI coding assistant rules
