# DISC-0026: Unified Model Registry Schema (SSoT)

> **Status**: Draft  
> **Created**: 2026-01-03  
> **Author**: AI Assistant + USER  
> **Depends On**: DISC-0019, DISC-007  
> **Blocks**: P2RE enhancements, Agentic API  

---

## Summary

Design a comprehensive **Single Source of Truth (SSoT)** schema for all AI model information across providers (Anthropic, Google, xAI, future local models). This enables deterministic model selection, accurate cost tracking, capability-based routing, and automated pricing refresh.

---

## Context

### Problem

Currently model information is scattered:
- Hardcoded pricing in `backend/main.py` (MODEL_PRICING dict)
- Model lists in provider classes
- Capabilities documented in DISC-0019 but not in code
- No automated refresh mechanism
- No unified capability query API

### Vision

A database-backed model registry that:
1. Stores all model metadata (pricing, capabilities, limits)
2. Provides deterministic model selection based on task requirements
3. Tracks pricing history for cost analysis
4. Auto-refreshes from provider APIs weekly
5. Supports local/offline models alongside cloud providers

---

## Data Extracted from Provider Docs (2026-01-03)

### Google Gemini Models

| Model | Input ($/1M) | Output ($/1M) | Context | Capabilities |
|-------|--------------|---------------|---------|--------------|
| gemini-3-pro | $2.00-$4.00 | $12.00-$18.00 | 1M+ | Multimodal, best agentic |
| gemini-3-pro (batch) | $1.00-$2.00 | $6.00-$9.00 | 1M+ | 50% discount |
| gemini-2.5-pro | $0.50 (text) / $1.00 (audio) | $3.00 | 1M | Reasoning, search grounding |
| gemini-2.5-flash | $0.30 | $2.50 | 1M | Hybrid reasoning, thinking budgets |
| gemini-2.5-flash-lite | $0.10 | $0.40 | 1M | Cost-efficient, high throughput |
| gemini-2.0-flash | $0.10 (text) / $0.70 (audio) | $0.40 | 1M | Balanced multimodal, agents |

**Gemini Tools:**
- Google Search grounding ($14-$35/1K queries)
- Google Maps grounding ($25/1K queries)
- Code execution sandbox
- URL context fetching
- Computer Use (beta)
- File Search
- Deep Research
- Live API (real-time audio/video)
- Context caching (storage: $1-$4.50/1M tokens/hour)
- Batch API (50% discount)
- Image generation (Nano Banana, Imagen)
- Video generation (Veo)
- Music generation (Lyria)
- Text-to-speech (TTS Flash/Pro)

### Anthropic Claude Models

| Model | Input ($/MTok) | Output ($/MTok) | Cache Hits | Context |
|-------|----------------|-----------------|------------|---------|
| claude-opus-4.5 | $5.00 | $25.00 | $0.50 | 200K |
| claude-opus-4.1 | $15.00 | $75.00 | $1.50 | 200K |
| claude-opus-4 | $15.00 | $75.00 | $1.50 | 200K |
| claude-sonnet-4.5 | $3.00 | $15.00 | $0.30 | 200K (1M beta) |
| claude-sonnet-4 | $3.00 | $15.00 | $0.30 | 200K (1M beta) |
| claude-haiku-4.5 | $1.00 | $5.00 | $0.10 | 200K |
| claude-haiku-3.5 | $0.80 | $4.00 | $0.08 | 200K |
| claude-haiku-3 | $0.25 | $1.25 | $0.03 | 200K |

**Claude Features:**
- Prompt caching (5-min: 1.25x, 1-hour: 2x write; 0.1x read)
- Batch API (50% discount)
- Long context (>200K tokens: 2x input, 1.5x output)
- Tool use (346 tokens overhead)
- Web search ($10/1K searches)
- Web fetch (free, token cost only)
- Code execution (1,550 free hrs/mo, then $0.05/hr)
- Computer use (735 tokens overhead)
- Bash tool (245 tokens overhead)
- Text editor tool (700 tokens overhead)

### xAI Grok Models

| Model | Input ($/1M) | Output ($/1M) | Context | Capabilities |
|-------|--------------|---------------|---------|--------------|
| grok-4-0709 | $3.00 | $15.00 | 256K | Premium quality |
| grok-4-fast-reasoning | $5.00 | $25.00 | 2M | Deep reasoning, CoT |
| grok-4-1-fast-reasoning | $5.00 | $25.00 | 2M | Reasoning with speed |
| grok-4-1-fast-non-reasoning | $0.20 | $0.50 | 2M | Fast inference |
| grok-code-fast-1 | ~$1.00 | ~$3.00 | 256K | Code-optimized |
| grok-3 | $3.00 | $15.00 | 131K | Premium quality |
| grok-3-mini | ~$0.50 | ~$1.50 | 131K | Budget-friendly |
| grok-2-vision-1212 | ~$2.00 | ~$8.00 | 32K | Image understanding |

**xAI Features:**
- Server-side agentic tools (web_search, x_search, code_execution)
- MCP integration
- Collections/Document search
- Citations with position tracking
- Verbose streaming (real-time tool visibility)
- Massive 2M context window (reasoning models)
- Vision capabilities

---

## Proposed Schema Design

### Core Tables

```sql
-- Provider registry
CREATE TABLE providers (
    id TEXT PRIMARY KEY,           -- 'anthropic', 'google', 'xai', 'local'
    name TEXT NOT NULL,
    api_base_url TEXT,
    auth_type TEXT,                -- 'api_key', 'oauth', 'none'
    status TEXT DEFAULT 'active',  -- 'active', 'deprecated', 'maintenance'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model registry (SSoT for all models)
CREATE TABLE models (
    id TEXT PRIMARY KEY,           -- 'claude-sonnet-4', 'gemini-2.5-flash'
    provider_id TEXT NOT NULL REFERENCES providers(id),
    name TEXT NOT NULL,            -- Human-readable name
    family TEXT,                   -- 'claude-4', 'gemini-2.5', 'grok-4'
    category TEXT,                 -- 'flagship', 'fast', 'lite', 'vision', 'code'
    
    -- Context & Limits
    context_window INTEGER,        -- Max tokens
    max_output_tokens INTEGER,
    
    -- Pricing (per 1M tokens, in USD)
    input_price_per_mtok REAL,
    output_price_per_mtok REAL,
    cache_read_price_per_mtok REAL,
    cache_write_price_per_mtok REAL,
    batch_input_price_per_mtok REAL,
    batch_output_price_per_mtok REAL,
    
    -- Capabilities (boolean flags)
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_tools BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_audio BOOLEAN DEFAULT FALSE,
    supports_video BOOLEAN DEFAULT FALSE,
    supports_code_execution BOOLEAN DEFAULT FALSE,
    supports_web_search BOOLEAN DEFAULT FALSE,
    supports_caching BOOLEAN DEFAULT FALSE,
    supports_batch BOOLEAN DEFAULT FALSE,
    supports_reasoning BOOLEAN DEFAULT FALSE,  -- Explicit CoT
    supports_json_mode BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    release_date DATE,
    deprecation_date DATE,
    status TEXT DEFAULT 'active',  -- 'active', 'preview', 'deprecated'
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool definitions (capabilities that cost extra)
CREATE TABLE tools (
    id TEXT PRIMARY KEY,
    provider_id TEXT REFERENCES providers(id),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Pricing
    price_per_use REAL,            -- e.g., $0.01 per search
    price_per_1k_uses REAL,        -- e.g., $10 per 1K searches
    token_overhead INTEGER,        -- Extra input tokens added
    
    -- Availability
    models_supported TEXT,         -- JSON array of model IDs
    free_tier_limit INTEGER,       -- e.g., 5000 free searches/month
    
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pricing history for trend analysis
CREATE TABLE pricing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id TEXT REFERENCES models(id),
    input_price REAL,
    output_price REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT                    -- 'api', 'manual', 'scrape'
);

-- Model selection rules (for deterministic routing)
CREATE TABLE routing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER DEFAULT 0,    -- Higher = checked first
    
    -- Conditions (JSON)
    conditions TEXT,               -- {"task_type": "code", "context_size": ">100000"}
    
    -- Action
    model_id TEXT REFERENCES models(id),
    fallback_model_id TEXT REFERENCES models(id),
    
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pydantic Models

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ProviderStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"

class ModelCategory(str, Enum):
    FLAGSHIP = "flagship"
    FAST = "fast"
    LITE = "lite"
    VISION = "vision"
    CODE = "code"
    REASONING = "reasoning"
    AUDIO = "audio"

class ModelCapabilities(BaseModel):
    streaming: bool = True
    tools: bool = False
    vision: bool = False
    audio: bool = False
    video: bool = False
    code_execution: bool = False
    web_search: bool = False
    caching: bool = False
    batch: bool = False
    reasoning: bool = False
    json_mode: bool = False

class ModelPricing(BaseModel):
    input_per_mtok: float
    output_per_mtok: float
    cache_read_per_mtok: float | None = None
    cache_write_per_mtok: float | None = None
    batch_input_per_mtok: float | None = None
    batch_output_per_mtok: float | None = None

class ModelInfo(BaseModel):
    id: str
    provider_id: str
    name: str
    family: str | None = None
    category: ModelCategory
    
    context_window: int
    max_output_tokens: int | None = None
    
    pricing: ModelPricing
    capabilities: ModelCapabilities
    
    release_date: datetime | None = None
    deprecation_date: datetime | None = None
    status: str = "active"
    notes: str | None = None

class ToolInfo(BaseModel):
    id: str
    provider_id: str
    name: str
    description: str | None = None
    
    price_per_use: float | None = None
    price_per_1k: float | None = None
    token_overhead: int = 0
    
    models_supported: list[str] = []
    free_tier_limit: int | None = None

class RoutingRule(BaseModel):
    name: str
    priority: int = 0
    conditions: dict  # e.g., {"task": "code", "context_gt": 100000}
    model_id: str
    fallback_model_id: str | None = None
    enabled: bool = True
```

---

## API Design

### Model Registry API

```python
# Query models
GET /api/models
GET /api/models/{model_id}
GET /api/models?provider=anthropic&capability=vision

# Model selection (deterministic routing)
POST /api/models/select
{
    "task_type": "code_review",
    "context_tokens": 150000,
    "required_capabilities": ["tools", "reasoning"],
    "max_cost_per_mtok": 5.0,
    "prefer_provider": "anthropic"
}
# Returns: best matching model with reasoning

# Cost estimation
POST /api/models/estimate-cost
{
    "model_id": "claude-sonnet-4",
    "input_tokens": 50000,
    "output_tokens": 2000,
    "tools_used": ["web_search"],
    "tool_calls": 3
}
# Returns: {"estimated_cost_usd": 0.185, "breakdown": {...}}

# Pricing refresh (admin)
POST /api/models/refresh-pricing
```

### Agentic API (Unified Interface)

```python
# Unified chat/completion endpoint
POST /api/ai/complete
{
    "messages": [...],
    "model": "auto",  # or specific model ID
    "task_hint": "code_review",  # helps routing
    "capabilities_required": ["tools"],
    "tools": [...],  # tool definitions
    "max_tokens": 4096,
    "stream": true
}

# Tool execution
POST /api/ai/tools/execute
{
    "tool": "web_search",
    "provider": "google",  # or "xai"
    "params": {"query": "..."}
}
```

---

## Implementation Roadmap

### Phase 1: Database & Core (Week 1)
- [ ] Create SQLite schema in P2RE database
- [ ] Seed initial model data from extracted docs
- [ ] Create Pydantic models
- [ ] Basic CRUD API endpoints

### Phase 2: Model Selection (Week 2)
- [ ] Implement routing rules engine
- [ ] Add capability-based model selection
- [ ] Cost estimation endpoint
- [ ] Integrate with existing chat endpoint

### Phase 3: Refresh Automation (Week 3)
- [ ] Price scraper for each provider
- [ ] Weekly cron job for refresh
- [ ] Pricing history tracking
- [ ] Alert on significant price changes

### Phase 4: Unified Agentic API (Week 4+)
- [ ] Abstract provider differences
- [ ] Unified tool calling interface
- [ ] Automatic fallback on errors
- [ ] Full P2RE trace integration

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-1 | Should we cache model info in memory or always query DB? | Open |
| Q-2 | How to handle provider-specific tool parameters? | Open |
| Q-3 | Should routing rules be user-configurable via UI? | Open |
| Q-4 | How to integrate local/HuggingFace models? | Open |
| Q-5 | Should we track per-user/per-project cost budgets? | Open |

---

## Related Documents

- DISC-0019: xAI + Gemini Agentic Capabilities Mapping
- DISC-007: Unified xAI Agent Wrapper
- ADR-TBD: Model Selection Strategy
