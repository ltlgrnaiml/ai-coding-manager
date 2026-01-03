# PLAN-0007: Multi-Provider LLM Adapter

**Status**: `in_progress`
**Created**: 2026-01-03
**Priority**: L1

## Objective

Create a clean adapter interface for multiple LLM providers (xAI, Anthropic, Google) with unified chat and tool calling support.

## Current State

- xAI (Grok): Implemented in `main.py` via OpenAI SDK
- Google (Gemini): Implemented in `main.py` via `google.generativeai`
- Anthropic (Claude): Not implemented

## Requirements

1. **Adapter Interface**: Clean abstraction for LLM providers
2. **Unified API**: Same interface for chat + tool calls across providers
3. **Streaming**: SSE streaming support for all providers
4. **Tool Calling**: Native tool/function calling support
5. **Model Switching**: Runtime model selection by provider

## Milestones

### M01: Provider Adapter Base (L1)

- [ ] Create `backend/services/llm/base.py` with abstract `LLMProvider` class
- [ ] Define common types: `ChatMessage`, `ToolCall`, `ToolResult`
- [ ] Define abstract methods: `chat()`, `chat_stream()`, `supports_tools()`

### M02: xAI Adapter (L1)

- [ ] Create `backend/services/llm/xai_provider.py`
- [ ] Migrate existing xAI logic from `main.py`
- [ ] Add tool calling support via OpenAI function calling

### M03: Anthropic Adapter (L1)

- [ ] Create `backend/services/llm/anthropic_provider.py`
- [ ] Implement chat with `anthropic` SDK
- [ ] Implement tool calling with Claude's tool_use

### M04: Provider Registry & Routing (L1)

- [ ] Create `backend/services/llm/registry.py`
- [ ] Auto-detect available providers by API keys
- [ ] Route requests to appropriate provider based on model

### M05: Update Chat Endpoints (L1)

- [ ] Refactor `main.py` to use provider registry
- [ ] Add Claude models to `/api/chat/models`
- [ ] Test streaming with all providers

## Verification

```bash
# Test Claude chat
curl -X POST http://localhost:8100/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"model":"claude-sonnet-4-20250514"}'

# List models (should include Claude)
curl http://localhost:8100/api/chat/models
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/services/llm/__init__.py` | Create - Package init |
| `backend/services/llm/base.py` | Create - Abstract base class |
| `backend/services/llm/types.py` | Create - Shared types |
| `backend/services/llm/xai_provider.py` | Create - xAI adapter |
| `backend/services/llm/anthropic_provider.py` | Create - Claude adapter |
| `backend/services/llm/registry.py` | Create - Provider registry |
| `backend/main.py` | Modify - Use new providers |
| `pyproject.toml` | Modify - Add anthropic dependency |
