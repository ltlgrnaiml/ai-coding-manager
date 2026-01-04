# DISC-0009: AI Chat Integration Architecture (Cross-Cutting)

> **Status**: `active`
> **Created**: 2026-01-03
> **Source Chat**: `Conversation Memory Architecture.md`
> **Session**: SESSION_0017
> **Parent Discussion**: DISC-0003 (UAM Umbrella)
> **Delegation Scope**: Chat UI, streaming responses, tool calling, context injection, session state
> **Inherits Context**: `true`

---

## Summary

**AI Chat Integration** is the user-facing interface where all AICM pillars converge. The chat is where conversations start (creating chat logs), where context is injected (via Tap-In), where knowledge is queried (from AIKH), and where traces are captured (for P2RE). This is where the "methodology-as-software" becomes tangible.

---

## Inherited Context (from DISC-0002)

- **Current Score**: 3/10
- **What's Good**: MCP integration mentioned
- **What's Great**: Core user touchpoint
- **Needs Enhancement**: Architecture design
- **Missing**: Full specification

---

## Chat Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI CHAT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER MESSAGE                                                   │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   CHAT SERVICE                           │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │                                                         │   │
│  │  1. TAP-IN                                              │   │
│  │     └── Load context from AIKH, sessions, AGENTS.md     │   │
│  │                                                         │   │
│  │  2. CONTEXT ENRICHMENT                                  │   │
│  │     └── Semantic search for relevant knowledge          │   │
│  │                                                         │   │
│  │  3. PROMPT CONSTRUCTION                                 │   │
│  │     └── System prompt + context + user message          │   │
│  │                                                         │   │
│  │  4. LLM ROUTING                                         │   │
│  │     └── Select provider/model based on task             │   │
│  │                                                         │   │
│  │  5. STREAMING RESPONSE                                  │   │
│  │     └── Real-time token delivery to UI                  │   │
│  │                                                         │   │
│  │  6. TOOL EXECUTION                                      │   │
│  │     └── Handle tool calls (file ops, search, etc.)      │   │
│  │                                                         │   │
│  │  7. TRACE CAPTURE (P2RE)                                │   │
│  │     └── Record full interaction for observability       │   │
│  │                                                         │   │
│  │  8. CHAT LOG PERSISTENCE                                │   │
│  │     └── Save conversation to .chat_logs/                │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│      │                                                          │
│      ▼                                                          │
│  AI RESPONSE (streamed)                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Prompt Design

### Core System Prompt Template
```markdown
# AICM AI Assistant

You are an AI assistant integrated with the AICM (AI Coding Manager) system.

## Your Capabilities
- Access to project artifacts (DISCs, ADRs, SPECs, Plans)
- Search across knowledge base (AIKH)
- Create and modify artifacts following UAM chain
- Track session continuity

## Project Rules (from AGENTS.md)
{agents_md_content}

## Current Context
**Session**: {session_id}
**Active Work**: {active_disc_or_plan}
**Recent Decisions**: {recent_adrs}

## Relevant Knowledge
{enriched_context}

## Your Behavior
1. Follow project rules strictly
2. Maintain session continuity
3. Reference artifacts by ID (e.g., DISC-0001)
4. Ask for clarification when scope is unclear
5. Produce traceable outputs (link to sources)
```

---

## Multi-Provider LLM Support

### Supported Providers
| Provider | Models | Use Cases |
|----------|--------|-----------|
| **Anthropic** | Claude 3.5 Sonnet, Haiku | Primary, quality work |
| **OpenAI** | GPT-4o, GPT-4o-mini | Alternative, specific tasks |
| **xAI** | Grok | Experimental |
| **Google** | Gemini Pro, Flash | Cost optimization |
| **Local** | Ollama (Llama, Mistral) | Privacy, offline |

### Model Router
```python
class ModelRouter:
    """Route requests to appropriate model based on task."""
    
    def select_model(self, task: TaskType, budget: Budget) -> Model:
        if task == TaskType.GENERATION and budget.allows_premium:
            return Model.CLAUDE_SONNET
        elif task == TaskType.SCORING:
            return Model.CLAUDE_HAIKU
        elif task == TaskType.EMBEDDING:
            return Model.LOCAL_EMBEDDING
        else:
            return self.default_model
```

---

## Streaming Response Architecture

### WebSocket Flow
```
Client                    Server                    LLM Provider
   │                         │                           │
   │──── WS Connect ────────▶│                           │
   │                         │                           │
   │──── Send Message ──────▶│                           │
   │                         │──── Stream Request ──────▶│
   │                         │                           │
   │◀──── Token ────────────│◀──── Token ──────────────│
   │◀──── Token ────────────│◀──── Token ──────────────│
   │◀──── Token ────────────│◀──── Token ──────────────│
   │                         │                           │
   │◀──── [DONE] ───────────│◀──── [DONE] ─────────────│
   │                         │                           │
   │◀──── Trace ID ─────────│                           │
```

### API Endpoint
```python
@router.websocket("/api/chat/stream")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        message = await websocket.receive_json()
        
        # 1. Tap-In: Load context
        context = await tap_in_service.build_context(
            project_path=message["project"],
            user_message=message["content"]
        )
        
        # 2. Start trace
        trace = trace_service.start_trace()
        
        # 3. Stream response
        async for token in llm_service.stream_chat(
            messages=context.messages,
            model=message.get("model", "claude-3-5-sonnet")
        ):
            await websocket.send_json({"type": "token", "content": token})
        
        # 4. Save trace
        await trace_service.save_trace(trace)
        
        # 5. Save to chat log
        await chatlog_service.append_turn(message, response)
        
        await websocket.send_json({"type": "done", "trace_id": trace.id})
```

---

## Tool Calling (MCP Integration)

### Available Tools
| Tool | Purpose | Trigger |
|------|---------|---------|
| `read_file` | Read project files | @file: mention |
| `search_knowledge` | Query AIKH | @search: or implicit |
| `create_artifact` | Generate DISC/ADR | "create discussion" |
| `run_command` | Execute shell | Explicit request |
| `view_trace` | Show P2RE trace | @trace: mention |

### MCP Server Configuration
```json
{
  "servers": {
    "filesystem": {
      "command": "mcp-filesystem",
      "args": ["--allowed-dir", "/project"]
    },
    "aikh": {
      "command": "mcp-aikh",
      "args": ["--db", "~/.aikh/"]
    }
  }
}
```

---

## Session State Management

### Session Object
```python
@dataclass
class ChatSession:
    id: str
    project_path: str
    started_at: datetime
    
    # Conversation state
    messages: list[Message]
    turn_count: int
    
    # Context state
    tap_in_context: TapInContext
    active_artifacts: list[str]
    
    # Tracking
    tokens_used: int
    cost_usd: float
    trace_ids: list[str]
```

### Persistence Strategy
- **In-Memory**: Current conversation
- **Redis (optional)**: Multi-server state
- **File**: Chat log for permanence

---

## Implementation Priorities

### Phase 1: Core Chat (Week 1-2)
- [ ] WebSocket streaming endpoint
- [ ] Basic system prompt
- [ ] Multi-provider support
- [ ] Chat log persistence

### Phase 2: Context Integration (Week 3)
- [ ] Tap-In integration
- [ ] AIKH context enrichment
- [ ] AGENTS.md injection

### Phase 3: Tool Calling (Week 4)
- [ ] MCP server setup
- [ ] File operations
- [ ] Knowledge search
- [ ] Artifact creation

### Phase 4: Frontend (Week 5-6)
- [ ] Chat UI component
- [ ] Streaming display
- [ ] Tool result rendering
- [ ] Session management

---

## Key Questions for ADR Production

| ID | Question | Status | Proposed Answer |
|----|----------|--------|-----------------|
| Q-1 | WebSocket vs SSE for streaming? | `open` | WebSocket (bidirectional needed) |
| Q-2 | How to handle tool errors? | `open` | Display error, allow retry |
| Q-3 | Chat log format? | `open` | Markdown with YAML frontmatter |
| Q-4 | Max conversation length? | `open` | 100 turns, then archive |
| Q-5 | Default model? | `open` | Claude 3.5 Sonnet (configurable) |

---

## Proposed ADRs from This DISC

| ADR ID | Title | Scope |
|--------|-------|-------|
| ADR-0019 | Chat Streaming Architecture | WebSocket design |
| ADR-0020 | System Prompt Structure | Prompt engineering |
| ADR-0021 | MCP Tool Integration | Tool calling patterns |

---

## Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| DISC-0003 (UAM) | `parent` | `active` | Part of UAM methodology |
| DISC-0004 (AIKH) | `hard` | `pending` | Chat queries AIKH |
| DISC-0005 (P2RE) | `hard` | `pending` | Chat creates traces |
| DISC-0006 (Tap-In) | `hard` | `pending` | Chat triggers tap-in |
| DISC-0008 (Artifact Gen) | `soft` | `pending` | Chat can generate artifacts |

---

## Conversation Log

### 2026-01-03 - SESSION_0017

**Topics Discussed**:
- Chat as convergence point for all pillars
- System prompt design for AICM context
- Multi-provider LLM support
- Streaming and tool calling architecture

**Key Insights**:
- Chat is where methodology becomes tangible
- WebSocket needed for bidirectional communication
- Every message triggers the full AICM stack

---

## Resolution

**Resolution Date**: TBD

**Outcome**: TBD (Produces ADRs for streaming, prompts, tools)

---

*DISC-0009 | Child of DISC-0003 | SESSION_0017*
