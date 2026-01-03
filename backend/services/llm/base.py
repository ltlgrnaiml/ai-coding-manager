"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from backend.services.llm.types import (
    ChatMessage,
    ChatResponse,
    StreamChunk,
    ToolDefinition,
    ModelInfo,
)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across different APIs.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'xai', 'anthropic', 'google')."""
        ...
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        ...
    
    @abstractmethod
    def get_models(self) -> list[ModelInfo]:
        """Get list of available models from this provider."""
        ...
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
    ) -> ChatResponse:
        """Send a chat completion request.
        
        Args:
            messages: Conversation history.
            model: Model ID to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            tools: Optional list of tools the model can call.
            
        Returns:
            ChatResponse with content and optional tool calls.
        """
        ...
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat completion response.
        
        Args:
            messages: Conversation history.
            model: Model ID to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            tools: Optional list of tools the model can call.
            
        Yields:
            StreamChunk objects with partial content.
        """
        ...
    
    def supports_model(self, model_id: str) -> bool:
        """Check if this provider supports a given model."""
        return any(m.id == model_id for m in self.get_models())
    
    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Get info for a specific model."""
        for m in self.get_models():
            if m.id == model_id:
                return m
        return None
