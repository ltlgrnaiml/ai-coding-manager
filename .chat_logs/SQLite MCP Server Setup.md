# Cascade Chat Conversation

  Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

What is the location of our uurren SQLite DB? Can you query it directly?

### Planner Response

I need to search for SQLite database files in the project to locate the current SQLite DB and determine if I can query it directly.

*Searched filesystem*

### Planner Response

Found the SQLite database at [/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0). Let me check if I can query it directly and examine its structure.

*User accepted the command `sqlite3 workspace/knowledge.db ".tables"`*

### Planner Response

The SQLite database is located at:
**[/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0)**

However, I cannot query it directly because `sqlite3` is not installed on the system. Let me check if there are any Python scripts or backend services that interact with this database to understand its structure:

*Grep searched codebase*

### Planner Response

Let me examine the database-related Python files to understand the structure and see if I can query it through the existing Python code:

*Viewed [database.py](file:///home/mycahya/coding/ai-coding-manager/backend/services/knowledge/database.py) *

*Viewed [database.py](file:///home/mycahya/coding/ai-coding-manager/src/ai_dev_orchestrator/knowledge/database.py) *

### Planner Response

## SQLite Database Location & Query Capability

**Database Location**: [/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0)

**Direct Query Status**: ❌ Cannot query directly - `sqlite3` CLI tool is not installed on the system.

## Database Structure

Based on the Python database modules, the SQLite database contains these main tables:

### Core Tables
- **`documents`** - Main document storage with metadata
- **`chunks`** - Text chunks for RAG processing  
- **`embeddings`** - Vector embeddings for semantic search
- **`relationships`** - Document relationships for graph retrieval
- **`llm_calls`** - LLM interaction tracking

### Chat System Tables
- **`chat_sessions`** - Conversation sessions
- **`chat_messages`** - Individual messages with deduplication
- **`chat_source_files`** - Source file tracking
- **`message_embeddings`** - Message vector embeddings

### Search Features
- **`content_fts`** - FTS5 full-text search virtual table
- Automatic triggers for FTS synchronization

## Query Options

Since `sqlite3` CLI isn't available, you can:

1. **Install sqlite3**: `sudo apt install sqlite3`
2. **Use Python scripts**: The existing Python modules at `@/home/mycahya/coding/ai-coding-manager/backend/services/knowledge/database.py` and `@/home/mycahya/coding/ai-coding-manager/src/ai_dev_orchestrator/knowledge/database.py` provide programmatic access
3. **Create a simple query script** using the existing database connection functions

Would you like me to install `sqlite3` or create a Python script to query the database?

*User accepted the command `sudo apt install sqlite3`*

*User accepted the command `sudo apt install sentence-transformers`*

*User accepted the command `sudo pip
 install sentence-transformers`*

*User accepted the command `apt install python3-sentence-transformers`*

*User accepted the command `sudo apt
 install python3-sentence-transformers`*

### User Input

Please help me with this error too? I have installed sqlite by the way please also retest your access

(.venv) mycahya@7950X-5090-Gamer:~/coding/ai-coding-manager$ sudo apt
 install python3-sentence-transformers
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
E: Unable to locate package python3-sentence-transformers
(.venv) mycahya@7950X-5090-Gamer:~/coding/ai-coding-manager$ 

### Planner Response

Great! Now that `sqlite3` is installed, let me first test database access and then help with the sentence-transformers installation issue.

*User accepted the command `sqlite3 workspace/knowledge.db ".tables"`*

### Planner Response

Perfect! SQLite is now working. The database exists but appears to be empty (no tables shown). Now let me help with the sentence-transformers installation issue.

*User accepted the command `sqlite3 workspace/knowledge.db "SELECT name FROM sqlite_master WHERE type='table';"`*

### Planner Response

## SQLite Database Access ✅

**Database Status**: Empty database (no tables yet) - needs initialization
- Location: [/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0)
- SQLite3 CLI now working properly

## Sentence-Transformers Installation Issue

The issue is that `sentence-transformers` isn't available as a system package. Since you're in a virtual environment (`.venv`), you should install it using pip within that environment:

*User accepted the command `pip install sentence-transformers`*

### Planner Response

The issue is that even though you're showing `(.venv)` in your prompt, the Python environment is still externally managed. Let me check if the virtual environment is properly activated and try a different approach:

*User accepted the command `which python`*

*User accepted the command `which pip`*

### Planner Response

The issue is that your virtual environment isn't properly activated. Let me help you fix this:

*Searched filesystem*

### Planner Response

The virtual environment doesn't exist yet. Let me create it and then install sentence-transformers properly:

*User accepted the command `python3 -m venv .venv`*

### Planner Response

Now let me install sentence-transformers in the newly created virtual environment:

*User accepted the command `.venv/bin/pip install sentence-transformers`*

### Planner Response

Perfect! ✅ Both issues are now resolved:

## SQLite Database Access ✅
- **Location**: [/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0)
- **Status**: Database exists but is empty (no tables initialized yet)
- **CLI Access**: Working with `sqlite3` command

## Sentence-Transformers Installation ✅
- **Issue**: Virtual environment wasn't properly created
- **Solution**: Created `.venv` and installed `sentence-transformers` successfully
- **Status**: All dependencies installed including PyTorch with CUDA support

## Next Steps

To use your virtual environment properly, activate it with:
```bash
source .venv/bin/activate
```

To initialize the database with the schema, you can run:
```bash
.venv/bin/python -c "from backend.services.knowledge.database import init_database; init_database()"
```

You can now:
1. Query the database directly with `sqlite3 workspace/knowledge.db`
2. Use sentence-transformers for embeddings in your Python code
3. Initialize the database schema when ready

### User Input

I am trying to setup the SQLite MCP Server on Windsurf for the Cascade chat to use, can you please help investigate what is not setup correctly? (I think we prefer a docker instance?? Not sure the tradeoff there)

*Updated todo list*

*Searched filesystem*

*Searched filesystem*

*Viewed [MCP%20Configs%20and%20Permissions.md](file:///home/mycahya/coding/ChatLogs/MCP%20Configs%20and%20Permissions.md) *

*User accepted the command `find ~/.config -name "*mcp*" -o -name "*windsurf*" 2>/dev/null | head -20`*

*User accepted the command `ls -la ~/.windsurf* 2>/dev/null || echo "No .windsurf files found"`*

*User accepted the command `cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json 2>/dev/null || echo "File not found at Windows path"`*

*Listed directory [.windsurf](file:///home/mycahya/.windsurf) *

### Planner Response

Found the issue. Let me update the plan and fix the configuration.

*Updated todo list*

### Planner Response

## SQLite MCP Server Issue Found

**Current Config** (at [/mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json](file:///mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json:0:0-0:0)):
```json
"sqlite": {
  "args": [
    "-y",
    "mcp-server-sqlite-npx",
    "C:\\Users\\Mycahya\\CascadeProjects\\engineering-tools\\workspace\\knowledge.db"
  ],
  "command": "npx"
}
```

**Problem**: The path points to a non-existent Windows location. Your actual database is at:
- WSL path: [/home/mycahya/coding/ai-coding-manager/workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0)
- UNC path: `\\wsl.localhost\Ubuntu\home\mycahya\coding\ai-coding-manager\workspace\knowledge.db`

---

## Docker vs Native Tradeoffs

| Aspect | **Native (npx)** | **Docker** |
|--------|------------------|------------|
| **Setup** | Simpler, uses existing Node | Requires Docker running |
| **Path Handling** | WSL paths tricky from Windows | Can mount volumes directly |
| **Isolation** | Shares host environment | Isolated, consistent |
| **Performance** | Faster (no container overhead) | Slight overhead |
| **Portability** | Depends on host tools | Consistent across machines |

**Recommendation**: For your setup (WSL + Windsurf on Windows), **native with proper UNC path** is simpler. Docker adds complexity for path mapping between Windows, WSL, and container.

---

## Fix

I'll update the config to use the correct UNC path:

*User accepted the command `cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json | sed 's|C:\\\\Users\\\\Mycahya\\\\CascadeProjects\\\\engineering-tools\\\\workspace\\\\knowledge.db|\\\\\\\\wsl.localhost\\\\Ubuntu\\\\home\\\\mycahya\\\\coding\\\\ai-coding-manager\\\\workspace\\\\knowledge.db|g' > /tmp/mcp_config_new.json && cat /tmp/mcp_config_new.json`*

*User accepted the command `cp /tmp/mcp_config_new.json /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json`*

*User accepted the command `cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json | grep -A5 '"sqlite"'`*

*Updated todo list*

### Planner Response

## ✅ SQLite MCP Server Configuration Fixed

**Changes Made:**
- Updated `mcp_config.json` to use correct WSL UNC path:
  ```
  \\wsl.localhost\Ubuntu\home\mycahya\coding\ai-coding-manager\workspace\knowledge.db
  ```

**Next Step Required:** **Restart Windsurf** for the MCP config changes to take effect.

---

**Note:** Your database is currently empty (no tables). After restarting, you may want to initialize it:

```bash
source .venv/bin/activate
python -c "from src.ai_dev_orchestrator.knowledge.database import init_database; init_database()"
```

This will create all the tables (documents, chunks, embeddings, chat_sessions, etc.) needed for the knowledge archive system.

*User accepted the command `python -c "from src.ai_dev_orchestrator.knowledge.database import init_database; init_database()"`*

### User Input

Can you check the DB now?

*User accepted the command `sqlite3 workspace/knowledge.db ".tables"`*

### Planner Response

The [workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0) is still empty. Let me check if the database was created elsewhere (the code uses `.workspace/` as the default directory):

*User accepted the command `find . -name "knowledge.db" -type f 2>/dev/null`*

### Planner Response

Two database files exist. Let me check the newly initialized one:

*User accepted the command `sqlite3 .workspace/knowledge.db ".tables"`*

*User accepted the command `sqlite3 .workspace/knowledge.db "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'trigger') ORDER BY type, name;"`*

### Planner Response

## ✅ Database Initialized Successfully

**Active Database**: `.workspace/knowledge.db` (not [workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0))

### Tables Created (14 total):
| Core Tables | Chat System | Search |
|-------------|-------------|--------|
| `documents` | `chat_sessions` | `content_fts` (FTS5) |
| `chunks` | `chat_messages` | + 4 FTS internal tables |
| `embeddings` | `chat_source_files` | |
| `relationships` | `message_embeddings` | |
| `llm_calls` | | |

### Triggers (5):
- `documents_ai`, `documents_ad`, `documents_au` - FTS sync
- `update_documents_timestamp`, `update_chat_sessions_timestamp` - auto timestamps

---

**⚠️ Path Mismatch**: The MCP config points to [workspace/knowledge.db](file:///home/mycahya/coding/ai-coding-manager/workspace/knowledge.db:0:0-0:0), but the actual initialized DB is at `.workspace/knowledge.db`. 

Want me to update the MCP config to use the correct path (`.workspace/knowledge.db`)?

### User Input

Yes please

*User accepted the command `sed -i 's|\\\\workspace\\\\knowledge.db|\\\\.workspace\\\\knowledge.db|g' /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json`*

*User accepted the command `cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json | grep -A5 '"sqlite"'`*

*Updated todo list*

### Planner Response

## ✅ MCP Config Updated

**SQLite server now points to:**
```
\\wsl.localhost\Ubuntu\home\mycahya\coding\ai-coding-manager\.workspace\knowledge.db
```

**Restart Windsurf** for the change to take effect. After restart, Cascade will have direct access to query your knowledge database.

### User Input

Ok fresh reboot of windows, fresh boot of Windsurf, still no initialization of MCP server. Can you please search the web for any hints as to why we are seeing this? I am running on WSL: ubuntu, with WSL2 Enabled Docker, should we do that for this MCP Server?

*Updated todo list*

*Searched web for MCP server initialization timed out 60 seconds SQLite Windsurf WSL*

*Read URL content from /r/windsurf/comments/1kmsj05/trying_to_enable_the_sqlite_mcp_server_an_got/ *

*Read URL content from /r/windsurf/comments/1oq6z10/solved_windsurfcascade_mcp_servers_not_loading/ *

*Read URL content from /questions/79706687/unable-to-start-mcp-servers-in-vs-code-in-wsl *

*Viewed content chunk*

*Viewed content chunk*

*Viewed content chunk*

### Planner Response

Found useful info. Let me check your system for the common issues:

*User accepted the command `sysctl fs.inotify.max_user_watches`*

*User accepted the command `cat /home/mycahya/.codeium/windsurf/mcp_config.json 2>/dev/null || cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json`*

*User accepted the command `docker --version 2>/dev/null && docker ps 2>/dev/null | head -5`*

*User accepted the command `cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json`*

*Updated todo list*

### Planner Response

## Diagnosis Complete

**Root Cause**: The `npx` command with UNC paths (`\\wsl.localhost\...`) is timing out. Windows Node.js can't efficiently access WSL filesystems, causing the 60-second timeout.

**Solution**: Use Docker (which has native WSL2 filesystem access).

Let me pull the SQLite MCP image and update the config:

*User accepted the command `docker pull mcp/sqlite`*

### Planner Response

Docker image is ready. Now let me update the MCP config to use Docker:

*User accepted the command `cat > /tmp/mcp_config_docker.json << 'EOF'
{
  "mcpServers": {
    "fetch": {
      "args": [
        "mcp-server-fetch"
      ],
      "command": "uvx",
      "disabled": false,
      "env": {}
    },
    "filesystem": {
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\Mycahya\\CascadeProjects",
        "C:\\Users\\Mycahya",
        "C:\\Users\\Mycahya\\.codeium\\windsurf",
        "\\\\wsl.localhost\\Ubuntu\\home\\mycahya\\coding",
        "\\\\wsl.localhost\\Ubuntu\\home\\mycahya\\coding\\ai-coding-manager",
        "\\\\wsl.localhost\\Ubuntu\\home\\mycahya\\coding\\engineer-tools"
      ],
      "command": "npx",
      "disabled": false,
      "env": {}
    },
    "memory": {
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ],
      "command": "npx",
      "env": {
        "MEMORY_FILE_PATH": ""
      }
    },
    "puppeteer": {
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ],
      "command": "npx",
      "disabled": false,
      "env": {}
    },
    "sqlite": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "/home/mycahya/coding/ai-coding-manager/.workspace:/mcp",
        "mcp/sqlite",
        "--db-path",
        "/mcp/knowledge.db"
      ],
      "disabled": false,
      "env": {}
    }
  }
}
EOF`*

*User accepted the command `cp /tmp/mcp_config_docker.json /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json && cat /mnt/c/Users/Mycahya/.codeium/windsurf/mcp_config.json | grep -A12 '"sqlite"'`*

### Planner Response

Let me verify the Docker config works:

*User accepted the command `echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 10 docker run --rm -i -v /home/mycahya/coding/ai-coding-manager/.workspace:/mcp mcp/sqlite --db-path /mcp/knowledge.db 2>&1 | head -20`*

*Updated todo list*

### Planner Response

## ✅ SQLite MCP Config Updated to Docker

**Changes Made:**
- Switched from `npx` (timing out on UNC paths) to `docker` command
- Mounts WSL directory directly: `/home/mycahya/coding/ai-coding-manager/.workspace:/mcp`
- Points to database: `/mcp/knowledge.db`

**New SQLite Config:**
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

**Why Docker is better for WSL2:**
- Native filesystem access (no UNC path overhead)
- Docker Desktop WSL2 backend mounts directly
- Avoids the 60-second timeout issue

**Next Step:** Restart Windsurf and check if the SQLite MCP server initializes successfully.

### User Input

OK! I think we got it. please test out using the MCP tool for SQLite to query our AI development knowledge system and ready for our chat logs? Can you find them and while you are there summarize for me all the available tables and the relationships.

*Updated todo list*

*Running MCP tool*

### Planner Response

MCP SQLite is working! Let me get the schema details:

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

### Planner Response

Excellent! The database has data. Let me explore the chat logs:

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Running MCP tool*

*Updated todo list*

### Planner Response

## ✅ SQLite MCP Server Working!

### Database Statistics

| Table | Records |
|-------|---------|
| **documents** | 65 |
| **chunks** | 3,232 |
| **embeddings** | 3,232 |
| **chat_sessions** | 31 |
| **chat_messages** | 483 |
| **chat_source_files** | 40 |
| relationships | 0 |
| llm_calls | 0 |
| message_embeddings | 0 |

---

## Database Schema & Relationships

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   documents     │       │     chunks      │       │   embeddings    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──1:N──│ doc_id (FK)     │──1:N──│ chunk_id (FK)   │
│ type            │       │ chunk_index     │       │ vector (BLOB)   │
│ title           │       │ content         │       │ model           │
│ content         │       │ start_char      │       │ dimensions      │
│ file_path       │       │ end_char        │       └─────────────────┘
│ file_hash       │       │ token_count     │
│ archived_at     │       └─────────────────┘
└────────┬────────┘
         │
    1:N  │  ┌─────────────────┐
         └──│  relationships  │ (graph edges between docs)
            │ source_id (FK)  │
            │ target_id (FK)  │
            │ relationship_type│
            └─────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│  chat_sessions  │       │  chat_messages  │       │ message_embeddings  │
├─────────────────┤       ├─────────────────┤       ├─────────────────────┤
│ id (PK)         │──1:N──│ session_id (FK) │──1:N──│ message_id (FK)     │
│ title           │       │ content_hash    │       │ vector (BLOB)       │
│ message_count   │       │ role            │       │ model               │
│ topics (JSON)   │       │ content         │       └─────────────────────┘
│ summary         │       │ sequence_num    │
└────────┬────────┘       │ source_file     │
         │                └─────────────────┘
    1:N  │  ┌─────────────────────┐
         └──│  chat_source_files  │ (tracks import provenance)
            │ session_id (FK)     │
            │ file_path           │
            │ file_hash           │
            │ message_count       │
            └─────────────────────┘

┌─────────────────┐        ┌─────────────────┐
│   llm_calls     │        │   content_fts   │ (FTS5 full-text search)
├─────────────────┤        ├─────────────────┤
│ session_id      │        │ title           │
│ model           │        │ content         │
│ prompt/response │        │ doc_id          │
│ tokens_in/out   │        └─────────────────┘
│ cost            │
└─────────────────┘
```

---

## Document Types in System

| Type | Count |
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

## Chat Logs Found

**31 chat sessions** imported from [/home/mycahya/coding/ChatLogs/](file:///home/mycahya/coding/ChatLogs:0:0-0:0), including:
- AI-Native Documentation Strategy (43 messages)
- Chat Memory Implementation (27 messages)
- API Versioning and Naming ADR (23 messages)
- Workflow Feature Development
- DAT Refactor discussions (multiple AI models)
- And more...

The system is ready for chat log analysis and RAG queries!

### User Input

Ok Please update our open session log on the status of current codebase here for the ai-coding-manager.

*Updated todo list*

*Searched filesystem*

*Viewed [SESSION_007_Chat-Quality-Grading-System.md](file:///home/mycahya/coding/ai-coding-manager/.sessions/SESSION_007_Chat-Quality-Grading-System.md) *

### Planner Response

SESSION_007 is complete. I'll create SESSION_008 for our current work:

*Edited relevant file*

### Planner Response

Let me fix the markdown lint warnings:

*Edited relevant file*

### Planner Response

Let me rewrite the file with proper markdown formatting:

*Viewed [SESSION_008_SQLite-MCP-Server-Setup.md](file:///home/mycahya/coding/ai-coding-manager/.sessions/SESSION_008_SQLite-MCP-Server-Setup.md) *

*Edited relevant file*

*Updated todo list*

### Planner Response

## ✅ Session Log Created

Created `@/home/mycahya/coding/ai-coding-manager/.sessions/SESSION_008_SQLite-MCP-Server-Setup.md` documenting:

- **SQLite CLI installation** and database initialization
- **Virtual environment setup** with sentence-transformers
- **MCP Docker configuration** fix (root cause: UNC path timeout)
- **Database status**: 65 docs, 3,232 chunks/embeddings, 31 chat sessions, 483 messages
- **Schema summary** with relationships diagram
- **Handoff notes** with next steps

The remaining lint warnings are minor table spacing style issues (MD060) that don't affect functionality.

### User Input

Please generate a commit message and commit your session log

*User accepted the command `git status --short`*

*User accepted the command `git add .sessions/SESSION_008_SQLite-MCP-Server-Setup.md`*

*User accepted the command `git commit -m "docs(sessions): add SESSION_008 SQLite MCP server setup

- Document SQLite CLI installation and database initialization
- Record MCP Docker config fix for WSL2 timeout issue
- Capture database status: 65 docs, 3,232 chunks, 31 chat sessions
- Include schema summary and technical notes on Docker vs npx
- Add handoff notes for next steps (relationships, embeddings, grading)

Root cause: npx with UNC paths times out; Docker has native WSL access"`*

*Updated todo list*

### Planner Response

## ✅ Committed

```
c1cd724 docs(sessions): add SESSION_008 SQLite MCP server setup
```

**1 file changed, 150 insertions(+)**
- [.sessions/SESSION_008_SQLite-MCP-Server-Setup.md](file:///home/mycahya/coding/ai-coding-manager/.sessions/SESSION_008_SQLite-MCP-Server-Setup.md:0:0-0:0)