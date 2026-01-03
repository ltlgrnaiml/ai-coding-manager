# Chat Logs Archive

> **Purpose**: Cross-project AI chat conversation logs for the AI Knowledge Hub (AIKH)

---

## Overview

This folder contains exported chat logs from AI coding assistants (Windsurf/Cascade, ChatGPT, Claude, etc.). These logs serve as:

1. **Operational Knowledge** - Past solutions, debugging sessions, architectural decisions
2. **Context for RAG** - Searchable history for AI-assisted development
3. **Training Data** - Examples of effective AI collaboration patterns

---

## Folder Structure

```text
.chat_logs/
├── README.md           # This file
├── .gitignore          # Excludes databases and temp files
├── *.md                # Chat log files (exported from AI tools)
└── chathistory.db      # Generated - DO NOT SYNC (in .gitignore)
```

---

## File Format

Chat logs follow a markdown structure with conversation turns:

```markdown
### User Input
<user message>

### Planner Response
<assistant response>
```

---

## Database Generation

The `chathistory.db` SQLite database is **generated on each device** from the markdown source files. It is excluded from git because:

1. SQLite files can corrupt during sync
2. WAL files are device-specific
3. Regeneration is fast (<60 seconds)

### Regenerate Database

```bash
# From project root
uv run python -m ai_dev_orchestrator.knowledge.chatlog_parser .chat_logs/
```

---

## Integration with AIKH

This folder is a source for the **AI Knowledge Hub (AIKH)** system:

- **Full-text search** via FTS5 index
- **Semantic search** via GPU embeddings
- **Cross-project queries** for finding related conversations
- **Context enrichment** for AI prompts

See: `docs/AIKH_ARCHITECTURE.md` for details.

---

## Git Tracking

**Tracked**:

- All `*.md` chat log files
- `README.md`
- `.gitignore`

**Ignored** (regenerated locally):

- `*.db`, `*.db-shm`, `*.db-wal`
- `*:Zone.Identifier` (Windows ADS files)

---

## Adding New Chat Logs

1. Export chat from your AI tool as markdown
2. Save to this folder with a descriptive filename
3. Commit to git
4. Database will auto-update on next sync

---

## Project

Part of the AI Coding Manager (AICM) project
