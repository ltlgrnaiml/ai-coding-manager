"""LLM provider registry and routing."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from backend.services.llm.base import LLMProvider
from backend.services.llm.types import (
    ChatMessage,
    StreamChunk,
    ToolDefinition,
    ModelInfo,
)
from backend.services.llm.xai_provider import XAIProvider
from backend.services.llm.anthropic_provider import AnthropicProvider


# Singleton instances
_providers: dict[str, LLMProvider] = {}


def _init_providers() -> None:
    """Initialize all provider instances."""
    global _providers
    if _providers:
        return
    
    _providers = {
        "xai": XAIProvider(),
        "anthropic": AnthropicProvider(),
    }


def get_provider(name: str) -> LLMProvider | None:
    """Get a provider by name."""
    _init_providers()
    return _providers.get(name)


def get_available_providers() -> list[LLMProvider]:
    """Get all available (configured) providers."""
    _init_providers()
    return [p for p in _providers.values() if p.is_available]


def get_all_models() -> list[ModelInfo]:
    """Get all models from all available providers."""
    _init_providers()
    models = []
    for provider in _providers.values():
        if provider.is_available:
            models.extend(provider.get_models())
    return models


def get_provider_for_model(model_id: str) -> LLMProvider | None:
    """Find the provider that supports a given model."""
    _init_providers()
    
    # Check model prefix for quick routing
    if model_id.startswith("claude"):
        provider = _providers.get("anthropic")
        if provider and provider.is_available:
            return provider
    elif model_id.startswith("grok"):
        provider = _providers.get("xai")
        if provider and provider.is_available:
            return provider
    elif model_id.startswith("gemini"):
        # TODO: Add Google provider
        pass
    
    # Fallback: search all providers
    for provider in _providers.values():
        if provider.is_available and provider.supports_model(model_id):
            return provider
    
    return None


async def stream_chat(
    messages: list[ChatMessage],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    tools: list[ToolDefinition] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from appropriate provider.
    
    Yields SSE-formatted strings for direct use in StreamingResponse.
    """
    provider = get_provider_for_model(model)
    
    if not provider:
        yield f"data: {json.dumps({'error': f'No provider available for model: {model}'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    try:
        async for chunk in provider.chat_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        ):
            if chunk.is_final:
                yield "data: [DONE]\n\n"
            elif chunk.content:
                yield f"data: {json.dumps({'content': chunk.content, 'model': model, 'provider': provider.name})}\n\n"
    
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


def get_models_for_api() -> list[dict[str, Any]]:
    """Get models formatted for /api/chat/models endpoint."""
    models = get_all_models()
    return [
        {
            "id": m.id,
            "name": m.name,
            "provider": m.provider,
            "category": m.category,
            "context": _format_context(m.context_window),
            "supports_tools": m.supports_tools,
            "supports_vision": m.supports_vision,
        }
        for m in models
    ]


def _format_context(tokens: int) -> str:
    """Format context window size for display."""
    if tokens >= 1_000_000:
        return f"{tokens // 1_000_000}M"
    elif tokens >= 1_000:
        return f"{tokens // 1_000}K"
    return str(tokens)
