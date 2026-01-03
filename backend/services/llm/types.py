"""Shared types for LLM providers."""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for parameters


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool call."""
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ChatMessage:
    """A message in a chat conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None  # For tool result messages
    name: str | None = None  # Tool name for tool results


@dataclass
class ChatResponse:
    """Response from a chat completion."""
    content: str
    model: str
    provider: str
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass
class StreamChunk:
    """A chunk of streamed response."""
    content: str
    model: str
    provider: str
    tool_calls: list[ToolCall] | None = None
    is_final: bool = False


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    provider: str
    context_window: int
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    category: str = "general"
    input_price: float = 0.0  # Per million tokens
    output_price: float = 0.0  # Per million tokens
    metadata: dict[str, Any] = field(default_factory=dict)
