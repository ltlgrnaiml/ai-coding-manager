"""Model Registry Service.

SSoT for all AI model information - pricing, capabilities, tools, and routing.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .database import get_connection


# =============================================================================
# Enums
# =============================================================================

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
    IMAGE_GEN = "image_gen"


class ModelStatus(str, Enum):
    ACTIVE = "active"
    PREVIEW = "preview"
    DEPRECATED = "deprecated"


# =============================================================================
# Pydantic Models
# =============================================================================

class ModelCapabilities(BaseModel):
    """Capability flags for a model."""
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
    mcp: bool = False


class ModelPricing(BaseModel):
    """Pricing information per 1M tokens."""
    input_per_mtok: float
    output_per_mtok: float
    cache_read_per_mtok: float | None = None
    cache_write_per_mtok: float | None = None
    batch_input_per_mtok: float | None = None
    batch_output_per_mtok: float | None = None


class ProviderInfo(BaseModel):
    """Provider information."""
    id: str
    name: str
    api_base_url: str | None = None
    auth_type: str = "api_key"
    status: str = "active"


class ModelInfo(BaseModel):
    """Complete model information."""
    id: str
    provider_id: str
    name: str
    family: str | None = None
    category: str | None = None
    
    context_window: int
    max_output_tokens: int | None = None
    
    pricing: ModelPricing
    capabilities: ModelCapabilities
    
    release_date: str | None = None
    deprecation_date: str | None = None
    status: str = "active"
    notes: str | None = None


class ToolInfo(BaseModel):
    """Tool information with pricing."""
    id: str
    provider_id: str | None = None
    name: str
    display_name: str | None = None
    description: str | None = None
    
    price_per_use: float | None = None
    price_per_1k: float | None = None
    token_overhead: int = 0
    
    models_supported: list[str] = []
    free_tier_limit: int | None = None
    parameters_schema: dict | None = None


class MCPServerInfo(BaseModel):
    """MCP server information."""
    id: str
    name: str
    description: str | None = None
    server_type: str  # stdio, sse, http
    command: str | None = None
    url: str | None = None
    status: str = "active"
    tools: list[dict] = []
    resources: list[dict] = []


class ModelSelectionRequest(BaseModel):
    """Request for deterministic model selection."""
    task_type: str | None = None
    context_tokens: int | None = None
    required_capabilities: list[str] = []
    max_cost_per_mtok: float | None = None
    prefer_provider: str | None = None
    prefer_category: str | None = None


class CostEstimateRequest(BaseModel):
    """Request for cost estimation."""
    model_id: str
    input_tokens: int
    output_tokens: int
    tools_used: list[str] = []
    tool_calls: int = 0
    use_cache: bool = False
    use_batch: bool = False


class CostEstimateResponse(BaseModel):
    """Cost estimation response."""
    estimated_cost_usd: float
    breakdown: dict


# =============================================================================
# Database Operations
# =============================================================================

def upsert_provider(provider: ProviderInfo) -> bool:
    """Insert or update a provider."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO providers (id, name, api_base_url, auth_type, status, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                api_base_url = excluded.api_base_url,
                auth_type = excluded.auth_type,
                status = excluded.status,
                updated_at = datetime('now')
            """,
            (provider.id, provider.name, provider.api_base_url, provider.auth_type, provider.status)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def upsert_model(model: ModelInfo) -> bool:
    """Insert or update a model."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO models (
                id, provider_id, name, family, category,
                context_window, max_output_tokens,
                input_price_per_mtok, output_price_per_mtok,
                cache_read_price_per_mtok, cache_write_price_per_mtok,
                batch_input_price_per_mtok, batch_output_price_per_mtok,
                supports_streaming, supports_tools, supports_vision,
                supports_audio, supports_video, supports_code_execution,
                supports_web_search, supports_caching, supports_batch,
                supports_reasoning, supports_json_mode, supports_mcp,
                release_date, deprecation_date, status, notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                family = excluded.family,
                category = excluded.category,
                context_window = excluded.context_window,
                max_output_tokens = excluded.max_output_tokens,
                input_price_per_mtok = excluded.input_price_per_mtok,
                output_price_per_mtok = excluded.output_price_per_mtok,
                cache_read_price_per_mtok = excluded.cache_read_price_per_mtok,
                cache_write_price_per_mtok = excluded.cache_write_price_per_mtok,
                batch_input_price_per_mtok = excluded.batch_input_price_per_mtok,
                batch_output_price_per_mtok = excluded.batch_output_price_per_mtok,
                supports_streaming = excluded.supports_streaming,
                supports_tools = excluded.supports_tools,
                supports_vision = excluded.supports_vision,
                supports_audio = excluded.supports_audio,
                supports_video = excluded.supports_video,
                supports_code_execution = excluded.supports_code_execution,
                supports_web_search = excluded.supports_web_search,
                supports_caching = excluded.supports_caching,
                supports_batch = excluded.supports_batch,
                supports_reasoning = excluded.supports_reasoning,
                supports_json_mode = excluded.supports_json_mode,
                supports_mcp = excluded.supports_mcp,
                status = excluded.status,
                notes = excluded.notes,
                updated_at = datetime('now')
            """,
            (
                model.id, model.provider_id, model.name, model.family, model.category,
                model.context_window, model.max_output_tokens,
                model.pricing.input_per_mtok, model.pricing.output_per_mtok,
                model.pricing.cache_read_per_mtok, model.pricing.cache_write_per_mtok,
                model.pricing.batch_input_per_mtok, model.pricing.batch_output_per_mtok,
                int(model.capabilities.streaming), int(model.capabilities.tools),
                int(model.capabilities.vision), int(model.capabilities.audio),
                int(model.capabilities.video), int(model.capabilities.code_execution),
                int(model.capabilities.web_search), int(model.capabilities.caching),
                int(model.capabilities.batch), int(model.capabilities.reasoning),
                int(model.capabilities.json_mode), int(model.capabilities.mcp),
                model.release_date, model.deprecation_date, model.status, model.notes
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()


def upsert_tool(tool: ToolInfo) -> bool:
    """Insert or update a tool."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO model_tools (
                id, provider_id, name, display_name, description,
                price_per_use, price_per_1k_uses, token_overhead,
                models_supported, free_tier_limit, parameters_schema
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                display_name = excluded.display_name,
                description = excluded.description,
                price_per_use = excluded.price_per_use,
                price_per_1k_uses = excluded.price_per_1k_uses,
                token_overhead = excluded.token_overhead,
                models_supported = excluded.models_supported,
                free_tier_limit = excluded.free_tier_limit,
                parameters_schema = excluded.parameters_schema
            """,
            (
                tool.id, tool.provider_id, tool.name, tool.display_name, tool.description,
                tool.price_per_use, tool.price_per_1k, tool.token_overhead,
                json.dumps(tool.models_supported), tool.free_tier_limit,
                json.dumps(tool.parameters_schema) if tool.parameters_schema else None
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_all_providers() -> list[ProviderInfo]:
    """Get all providers."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM providers WHERE status = 'active'").fetchall()
        return [ProviderInfo(
            id=row["id"],
            name=row["name"],
            api_base_url=row["api_base_url"],
            auth_type=row["auth_type"],
            status=row["status"]
        ) for row in rows]
    finally:
        conn.close()


def get_all_models(provider_id: str | None = None, capability: str | None = None) -> list[ModelInfo]:
    """Get all models, optionally filtered."""
    conn = get_connection()
    try:
        query = "SELECT * FROM models WHERE status = 'active'"
        params = []
        
        if provider_id:
            query += " AND provider_id = ?"
            params.append(provider_id)
        
        if capability:
            cap_col = f"supports_{capability}"
            query += f" AND {cap_col} = 1"
        
        rows = conn.execute(query, params).fetchall()
        return [_row_to_model_info(row) for row in rows]
    finally:
        conn.close()


def get_model(model_id: str) -> ModelInfo | None:
    """Get a single model by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
        if row:
            return _row_to_model_info(row)
        return None
    finally:
        conn.close()


def get_tools_for_model(model_id: str) -> list[ToolInfo]:
    """Get tools available for a specific model."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM model_tools 
            WHERE status = 'active' 
            AND (models_supported IS NULL OR models_supported LIKE ?)
            """,
            (f'%"{model_id}"%',)
        ).fetchall()
        return [_row_to_tool_info(row) for row in rows]
    finally:
        conn.close()


def get_all_tools(provider_id: str | None = None) -> list[ToolInfo]:
    """Get all tools, optionally filtered by provider."""
    conn = get_connection()
    try:
        if provider_id:
            rows = conn.execute(
                "SELECT * FROM model_tools WHERE status = 'active' AND provider_id = ?",
                (provider_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM model_tools WHERE status = 'active'").fetchall()
        return [_row_to_tool_info(row) for row in rows]
    finally:
        conn.close()


def select_model(request: ModelSelectionRequest) -> ModelInfo | None:
    """Select best model based on requirements."""
    models = get_all_models()
    
    # Filter by required capabilities
    if request.required_capabilities:
        filtered = []
        for model in models:
            caps = model.capabilities.model_dump()
            if all(caps.get(cap, False) for cap in request.required_capabilities):
                filtered.append(model)
        models = filtered
    
    # Filter by context window
    if request.context_tokens:
        models = [m for m in models if m.context_window >= request.context_tokens]
    
    # Filter by max cost
    if request.max_cost_per_mtok:
        models = [m for m in models if m.pricing.input_per_mtok <= request.max_cost_per_mtok]
    
    # Prefer specific provider
    if request.prefer_provider:
        preferred = [m for m in models if m.provider_id == request.prefer_provider]
        if preferred:
            models = preferred
    
    # Prefer specific category
    if request.prefer_category:
        preferred = [m for m in models if m.category == request.prefer_category]
        if preferred:
            models = preferred
    
    # Sort by cost (cheapest first)
    models.sort(key=lambda m: m.pricing.input_per_mtok + m.pricing.output_per_mtok)
    
    return models[0] if models else None


def estimate_cost(request: CostEstimateRequest) -> CostEstimateResponse:
    """Estimate cost for a request."""
    model = get_model(request.model_id)
    if not model:
        return CostEstimateResponse(estimated_cost_usd=0, breakdown={"error": "Model not found"})
    
    pricing = model.pricing
    
    # Base token costs
    if request.use_batch and pricing.batch_input_per_mtok:
        input_cost = (request.input_tokens / 1_000_000) * pricing.batch_input_per_mtok
        output_cost = (request.output_tokens / 1_000_000) * (pricing.batch_output_per_mtok or pricing.output_per_mtok)
    else:
        input_cost = (request.input_tokens / 1_000_000) * pricing.input_per_mtok
        output_cost = (request.output_tokens / 1_000_000) * pricing.output_per_mtok
    
    breakdown = {
        "input_tokens": request.input_tokens,
        "output_tokens": request.output_tokens,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
    }
    
    # Tool costs
    tool_cost = 0.0
    if request.tools_used and request.tool_calls > 0:
        tools = get_all_tools()
        tool_map = {t.name: t for t in tools}
        for tool_name in request.tools_used:
            if tool_name in tool_map:
                tool = tool_map[tool_name]
                if tool.price_per_use:
                    tool_cost += tool.price_per_use * request.tool_calls
                elif tool.price_per_1k:
                    tool_cost += (tool.price_per_1k / 1000) * request.tool_calls
        breakdown["tool_cost"] = round(tool_cost, 6)
    
    total = input_cost + output_cost + tool_cost
    
    return CostEstimateResponse(
        estimated_cost_usd=round(total, 6),
        breakdown=breakdown
    )


def _row_to_model_info(row) -> ModelInfo:
    """Convert database row to ModelInfo."""
    return ModelInfo(
        id=row["id"],
        provider_id=row["provider_id"],
        name=row["name"],
        family=row["family"],
        category=row["category"],
        context_window=row["context_window"],
        max_output_tokens=row["max_output_tokens"],
        pricing=ModelPricing(
            input_per_mtok=row["input_price_per_mtok"] or 0,
            output_per_mtok=row["output_price_per_mtok"] or 0,
            cache_read_per_mtok=row["cache_read_price_per_mtok"],
            cache_write_per_mtok=row["cache_write_price_per_mtok"],
            batch_input_per_mtok=row["batch_input_price_per_mtok"],
            batch_output_per_mtok=row["batch_output_price_per_mtok"],
        ),
        capabilities=ModelCapabilities(
            streaming=bool(row["supports_streaming"]),
            tools=bool(row["supports_tools"]),
            vision=bool(row["supports_vision"]),
            audio=bool(row["supports_audio"]),
            video=bool(row["supports_video"]),
            code_execution=bool(row["supports_code_execution"]),
            web_search=bool(row["supports_web_search"]),
            caching=bool(row["supports_caching"]),
            batch=bool(row["supports_batch"]),
            reasoning=bool(row["supports_reasoning"]),
            json_mode=bool(row["supports_json_mode"]),
            mcp=bool(row["supports_mcp"]),
        ),
        release_date=row["release_date"],
        deprecation_date=row["deprecation_date"],
        status=row["status"],
        notes=row["notes"],
    )


def _row_to_tool_info(row) -> ToolInfo:
    """Convert database row to ToolInfo."""
    models_supported = []
    if row["models_supported"]:
        try:
            models_supported = json.loads(row["models_supported"])
        except:
            pass
    
    params_schema = None
    if row["parameters_schema"]:
        try:
            params_schema = json.loads(row["parameters_schema"])
        except:
            pass
    
    return ToolInfo(
        id=row["id"],
        provider_id=row["provider_id"],
        name=row["name"],
        display_name=row["display_name"],
        description=row["description"],
        price_per_use=row["price_per_use"],
        price_per_1k=row["price_per_1k_uses"],
        token_overhead=row["token_overhead"] or 0,
        models_supported=models_supported,
        free_tier_limit=row["free_tier_limit"],
        parameters_schema=params_schema,
    )


# =============================================================================
# Seeding Functions
# =============================================================================

def seed_providers() -> int:
    """Seed provider data."""
    providers = [
        ProviderInfo(id="anthropic", name="Anthropic", api_base_url="https://api.anthropic.com"),
        ProviderInfo(id="google", name="Google", api_base_url="https://generativelanguage.googleapis.com"),
        ProviderInfo(id="xai", name="xAI", api_base_url="https://api.x.ai"),
        ProviderInfo(id="openai", name="OpenAI", api_base_url="https://api.openai.com"),
        ProviderInfo(id="local", name="Local", api_base_url=None, auth_type="none"),
    ]
    
    count = 0
    for provider in providers:
        if upsert_provider(provider):
            count += 1
    return count


def seed_models() -> int:
    """Seed model data from extracted pricing."""
    models = [
        # Anthropic Claude models
        ModelInfo(
            id="claude-opus-4.5", provider_id="anthropic", name="Claude Opus 4.5",
            family="claude-4.5", category="flagship", context_window=200000,
            pricing=ModelPricing(input_per_mtok=5.0, output_per_mtok=25.0, cache_read_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True),
        ),
        ModelInfo(
            id="claude-opus-4", provider_id="anthropic", name="Claude Opus 4",
            family="claude-4", category="flagship", context_window=200000,
            pricing=ModelPricing(input_per_mtok=15.0, output_per_mtok=75.0, cache_read_per_mtok=1.50),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True),
        ),
        ModelInfo(
            id="claude-sonnet-4.5", provider_id="anthropic", name="Claude Sonnet 4.5",
            family="claude-4.5", category="fast", context_window=200000,
            pricing=ModelPricing(input_per_mtok=3.0, output_per_mtok=15.0, cache_read_per_mtok=0.30, batch_input_per_mtok=1.50, batch_output_per_mtok=7.50),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True, code_execution=True, web_search=True),
        ),
        ModelInfo(
            id="claude-sonnet-4", provider_id="anthropic", name="Claude Sonnet 4",
            family="claude-4", category="fast", context_window=200000,
            pricing=ModelPricing(input_per_mtok=3.0, output_per_mtok=15.0, cache_read_per_mtok=0.30, batch_input_per_mtok=1.50, batch_output_per_mtok=7.50),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True, code_execution=True, web_search=True),
        ),
        ModelInfo(
            id="claude-3-5-sonnet-20241022", provider_id="anthropic", name="Claude 3.5 Sonnet",
            family="claude-3.5", category="fast", context_window=200000,
            pricing=ModelPricing(input_per_mtok=3.0, output_per_mtok=15.0, cache_read_per_mtok=0.30),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True),
        ),
        ModelInfo(
            id="claude-haiku-4.5", provider_id="anthropic", name="Claude Haiku 4.5",
            family="claude-4.5", category="lite", context_window=200000,
            pricing=ModelPricing(input_per_mtok=1.0, output_per_mtok=5.0, cache_read_per_mtok=0.10, batch_input_per_mtok=0.50, batch_output_per_mtok=2.50),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True),
        ),
        ModelInfo(
            id="claude-3-5-haiku-20241022", provider_id="anthropic", name="Claude 3.5 Haiku",
            family="claude-3.5", category="lite", context_window=200000,
            pricing=ModelPricing(input_per_mtok=0.80, output_per_mtok=4.0, cache_read_per_mtok=0.08, batch_input_per_mtok=0.40, batch_output_per_mtok=2.0),
            capabilities=ModelCapabilities(tools=True, vision=True, caching=True, batch=True, json_mode=True),
        ),
        
        # Google Gemini models
        ModelInfo(
            id="gemini-3-pro", provider_id="google", name="Gemini 3 Pro",
            family="gemini-3", category="flagship", context_window=1000000,
            pricing=ModelPricing(input_per_mtok=2.0, output_per_mtok=12.0, batch_input_per_mtok=1.0, batch_output_per_mtok=6.0),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, batch=True, json_mode=True, web_search=True, code_execution=True),
        ),
        ModelInfo(
            id="gemini-2.5-pro", provider_id="google", name="Gemini 2.5 Pro",
            family="gemini-2.5", category="fast", context_window=1000000,
            pricing=ModelPricing(input_per_mtok=0.50, output_per_mtok=3.0, batch_input_per_mtok=0.25, batch_output_per_mtok=1.50),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, batch=True, json_mode=True, web_search=True),
        ),
        ModelInfo(
            id="gemini-2.5-flash", provider_id="google", name="Gemini 2.5 Flash",
            family="gemini-2.5", category="fast", context_window=1000000,
            pricing=ModelPricing(input_per_mtok=0.30, output_per_mtok=2.50, cache_read_per_mtok=0.03, batch_input_per_mtok=0.15, batch_output_per_mtok=1.25),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, batch=True, json_mode=True, web_search=True, reasoning=True),
        ),
        ModelInfo(
            id="gemini-2.5-flash-lite", provider_id="google", name="Gemini 2.5 Flash Lite",
            family="gemini-2.5", category="lite", context_window=1000000,
            pricing=ModelPricing(input_per_mtok=0.10, output_per_mtok=0.40, cache_read_per_mtok=0.01, batch_input_per_mtok=0.05, batch_output_per_mtok=0.20),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, batch=True, json_mode=True, web_search=True),
        ),
        ModelInfo(
            id="gemini-2.0-flash", provider_id="google", name="Gemini 2.0 Flash",
            family="gemini-2.0", category="fast", context_window=1000000,
            pricing=ModelPricing(input_per_mtok=0.10, output_per_mtok=0.40, cache_read_per_mtok=0.025),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, json_mode=True),
        ),
        ModelInfo(
            id="gemini-1.5-pro", provider_id="google", name="Gemini 1.5 Pro",
            family="gemini-1.5", category="flagship", context_window=2000000,
            pricing=ModelPricing(input_per_mtok=1.25, output_per_mtok=10.0, batch_input_per_mtok=0.625, batch_output_per_mtok=5.0),
            capabilities=ModelCapabilities(tools=True, vision=True, audio=True, video=True, caching=True, batch=True, json_mode=True, web_search=True),
        ),
        
        # xAI Grok models (updated from docs.x.ai Jan 2026)
        ModelInfo(
            id="grok-4-1-fast-reasoning", provider_id="xai", name="Grok 4.1 Fast Reasoning",
            family="grok-4.1", category="reasoning", context_window=2000000,
            pricing=ModelPricing(input_per_mtok=0.20, output_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, reasoning=True, web_search=True, mcp=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-4-1-fast-non-reasoning", provider_id="xai", name="Grok 4.1 Fast",
            family="grok-4.1", category="fast", context_window=2000000,
            pricing=ModelPricing(input_per_mtok=0.20, output_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, web_search=True, mcp=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-code-fast-1", provider_id="xai", name="Grok Code Fast",
            family="grok-code", category="code", context_window=256000,
            pricing=ModelPricing(input_per_mtok=0.20, output_per_mtok=1.50),
            capabilities=ModelCapabilities(tools=True, code_execution=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-4-fast-reasoning", provider_id="xai", name="Grok 4 Fast Reasoning",
            family="grok-4", category="reasoning", context_window=2000000,
            pricing=ModelPricing(input_per_mtok=0.20, output_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, reasoning=True, web_search=True, mcp=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-4-fast-non-reasoning", provider_id="xai", name="Grok 4 Fast",
            family="grok-4", category="fast", context_window=2000000,
            pricing=ModelPricing(input_per_mtok=0.20, output_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, web_search=True, mcp=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-4-0709", provider_id="xai", name="Grok 4",
            family="grok-4", category="flagship", context_window=256000,
            pricing=ModelPricing(input_per_mtok=3.0, output_per_mtok=15.0),
            capabilities=ModelCapabilities(tools=True, vision=True, web_search=True, mcp=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-3-mini", provider_id="xai", name="Grok 3 Mini",
            family="grok-3", category="lite", context_window=131072,
            pricing=ModelPricing(input_per_mtok=0.30, output_per_mtok=0.50),
            capabilities=ModelCapabilities(tools=True, json_mode=True),
        ),
        ModelInfo(
            id="grok-3", provider_id="xai", name="Grok 3",
            family="grok-3", category="flagship", context_window=131072,
            pricing=ModelPricing(input_per_mtok=3.0, output_per_mtok=15.0),
            capabilities=ModelCapabilities(tools=True, web_search=True, mcp=True),
        ),
        ModelInfo(
            id="grok-2-vision-1212", provider_id="xai", name="Grok 2 Vision",
            family="grok-2", category="vision", context_window=32768,
            pricing=ModelPricing(input_per_mtok=2.0, output_per_mtok=10.0),
            capabilities=ModelCapabilities(vision=True),
        ),
    ]
    
    count = 0
    for model in models:
        if upsert_model(model):
            count += 1
    return count


def seed_tools() -> int:
    """Seed tool data."""
    tools = [
        # Anthropic tools
        ToolInfo(id="anthropic_web_search", provider_id="anthropic", name="web_search", display_name="Web Search",
                 description="Search the web for information", price_per_1k=10.0, token_overhead=346),
        ToolInfo(id="anthropic_web_fetch", provider_id="anthropic", name="web_fetch", display_name="Web Fetch",
                 description="Fetch content from a URL", token_overhead=0),
        ToolInfo(id="anthropic_code_execution", provider_id="anthropic", name="code_execution", display_name="Code Execution",
                 description="Execute Python code in a sandbox", price_per_use=0.00008, free_tier_limit=1550),
        ToolInfo(id="anthropic_computer_use", provider_id="anthropic", name="computer_use", display_name="Computer Use",
                 description="Control a computer interface", token_overhead=735),
        ToolInfo(id="anthropic_bash", provider_id="anthropic", name="bash", display_name="Bash Tool",
                 description="Execute bash commands", token_overhead=245),
        ToolInfo(id="anthropic_text_editor", provider_id="anthropic", name="text_editor", display_name="Text Editor",
                 description="Edit text files", token_overhead=700),
        
        # Google tools
        ToolInfo(id="google_search_grounding", provider_id="google", name="google_search", display_name="Google Search",
                 description="Ground responses with Google Search", price_per_1k=35.0, free_tier_limit=1500),
        ToolInfo(id="google_maps_grounding", provider_id="google", name="google_maps", display_name="Google Maps",
                 description="Ground responses with Google Maps", price_per_1k=25.0, free_tier_limit=1500),
        ToolInfo(id="google_code_execution", provider_id="google", name="code_execution", display_name="Code Execution",
                 description="Execute code in a sandbox"),
        ToolInfo(id="google_url_context", provider_id="google", name="url_context", display_name="URL Context",
                 description="Fetch and include URL content"),
        ToolInfo(id="google_file_search", provider_id="google", name="file_search", display_name="File Search",
                 description="Search uploaded files"),
        
        # xAI tools
        ToolInfo(id="xai_web_search", provider_id="xai", name="web_search", display_name="Web Search",
                 description="Search the web for information"),
        ToolInfo(id="xai_x_search", provider_id="xai", name="x_search", display_name="X Search",
                 description="Search X (Twitter) posts"),
        ToolInfo(id="xai_code_execution", provider_id="xai", name="code_execution", display_name="Code Execution",
                 description="Execute code in a sandbox"),
        ToolInfo(id="xai_mcp", provider_id="xai", name="mcp", display_name="MCP Integration",
                 description="Connect to MCP tool servers"),
    ]
    
    count = 0
    for tool in tools:
        if upsert_tool(tool):
            count += 1
    return count


def seed_all() -> dict:
    """Seed all registry data."""
    return {
        "providers": seed_providers(),
        "models": seed_models(),
        "tools": seed_tools(),
    }
