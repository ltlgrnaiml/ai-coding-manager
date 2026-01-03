"""Anthropic Claude LLM provider."""

import json
import os
from collections.abc import AsyncGenerator
from typing import Any

from backend.services.llm.base import LLMProvider
from backend.services.llm.types import (
    ChatMessage,
    ChatResponse,
    StreamChunk,
    ToolDefinition,
    ToolCall,
    ModelInfo,
)


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models."""
    
    def __init__(self):
        self._api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self._client = None
        self._async_client = None
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def is_available(self) -> bool:
        return bool(self._api_key)
    
    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client
    
    def _get_async_client(self):
        if self._async_client is None:
            import anthropic
            self._async_client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._async_client
    
    def get_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="claude-sonnet-4-20250514",
                name="Claude Sonnet 4",
                provider="anthropic",
                context_window=200_000,
                supports_tools=True,
                category="flagship",
                input_price=3.00,
                output_price=15.00,
            ),
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                context_window=200_000,
                supports_tools=True,
                category="balanced",
                input_price=3.00,
                output_price=15.00,
            ),
            ModelInfo(
                id="claude-3-5-haiku-20241022",
                name="Claude 3.5 Haiku",
                provider="anthropic",
                context_window=200_000,
                supports_tools=True,
                category="fast",
                input_price=0.80,
                output_price=4.00,
            ),
            ModelInfo(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider="anthropic",
                context_window=200_000,
                supports_tools=True,
                category="premium",
                input_price=15.00,
                output_price=75.00,
            ),
        ]
    
    def _convert_messages(self, messages: list[ChatMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert ChatMessage to Anthropic format.
        
        Returns:
            Tuple of (system_prompt, messages)
        """
        system_prompt = None
        result = []
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue
            
            if msg.role == "tool":
                # Tool result message
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                content: list[dict[str, Any]] = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                result.append({"role": "assistant", "content": content})
            else:
                # Regular message
                result.append({"role": msg.role, "content": msg.content})
        
        return system_prompt, result
    
    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict[str, Any]]:
        """Convert ToolDefinition to Anthropic format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
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
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        response = client.messages.create(**kwargs)
        
        content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )
        
        return ChatResponse(
            content=content,
            model=model,
            provider="anthropic",
            tool_calls=tool_calls if tool_calls else None,
            finish_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        client = self._get_async_client()
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
        
        try:
            async with client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(
                        content=text,
                        model=model,
                        provider="anthropic",
                    )
            
            yield StreamChunk(content="", model=model, provider="anthropic", is_final=True)
            
        except Exception as e:
            yield StreamChunk(
                content=f"Error: {e}",
                model=model,
                provider="anthropic",
                is_final=True,
            )
