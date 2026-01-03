"""xAI/Grok LLM provider."""

import json
import os
from collections.abc import AsyncGenerator
from typing import Any

from openai import OpenAI

from backend.services.llm.base import LLMProvider
from backend.services.llm.types import (
    ChatMessage,
    ChatResponse,
    StreamChunk,
    ToolDefinition,
    ToolCall,
    ModelInfo,
)


class XAIProvider(LLMProvider):
    """LLM provider for xAI/Grok models."""
    
    def __init__(self):
        self._api_key = os.getenv("XAI_API_KEY", "")
        self._base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        self._client: OpenAI | None = None
    
    @property
    def name(self) -> str:
        return "xai"
    
    @property
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=60,
            )
        return self._client
    
    def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="grok-4-1-fast-reasoning",
                name="Grok 4.1 Fast (Reasoning)",
                provider="xai",
                context_window=2_000_000,
                supports_tools=True,
                category="reasoning",
                input_price=0.20,
                output_price=0.50,
            ),
            ModelInfo(
                id="grok-4-fast-reasoning",
                name="Grok 4 Fast (Reasoning)",
                provider="xai",
                context_window=2_000_000,
                supports_tools=True,
                category="reasoning",
                input_price=0.20,
                output_price=0.50,
            ),
            ModelInfo(
                id="grok-4-1-fast-non-reasoning",
                name="Grok 4.1 Fast",
                provider="xai",
                context_window=2_000_000,
                supports_tools=True,
                category="fast",
                input_price=0.20,
                output_price=0.50,
            ),
            ModelInfo(
                id="grok-4-fast-non-reasoning",
                name="Grok 4 Fast",
                provider="xai",
                context_window=2_000_000,
                supports_tools=True,
                category="fast",
                input_price=0.20,
                output_price=0.50,
            ),
            ModelInfo(
                id="grok-code-fast-1",
                name="Grok Code Fast",
                provider="xai",
                context_window=256_000,
                supports_tools=True,
                category="code",
                input_price=0.20,
                output_price=1.50,
            ),
            ModelInfo(
                id="grok-4-0709",
                name="Grok 4 (Premium)",
                provider="xai",
                context_window=256_000,
                supports_tools=True,
                category="premium",
                input_price=3.00,
                output_price=15.00,
            ),
            ModelInfo(
                id="grok-3",
                name="Grok 3",
                provider="xai",
                context_window=131_072,
                supports_tools=True,
                category="premium",
                input_price=3.00,
                output_price=15.00,
            ),
            ModelInfo(
                id="grok-3-mini",
                name="Grok 3 Mini",
                provider="xai",
                context_window=131_072,
                supports_tools=True,
                category="budget",
                input_price=0.30,
                output_price=0.50,
            ),
            ModelInfo(
                id="grok-2-vision-1212",
                name="Grok 2 Vision",
                provider="xai",
                context_window=32_768,
                supports_tools=False,
                supports_vision=True,
                category="vision",
                input_price=2.00,
                output_price=10.00,
            ),
        ]
    
    def _convert_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Convert ChatMessage to OpenAI format."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            result.append(m)
        return result
    
    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert ToolDefinition to OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
    ) -> ChatResponse:
        client = self._get_client()
        oai_messages = self._convert_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": oai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        response = client.chat.completions.create(**kwargs)
        
        choice = response.choices[0]
        content = choice.message.content or ""
        
        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in choice.message.tool_calls
            ]
        
        return ChatResponse(
            content=content,
            model=model,
            provider="xai",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        client = self._get_client()
        oai_messages = self._convert_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": oai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        try:
            stream = client.chat.completions.create(**kwargs)
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamChunk(
                        content=chunk.choices[0].delta.content,
                        model=model,
                        provider="xai",
                    )
            
            yield StreamChunk(content="", model=model, provider="xai", is_final=True)
            
        except Exception as e:
            yield StreamChunk(
                content=f"Error: {e}",
                model=model,
                provider="xai",
                is_final=True,
            )
