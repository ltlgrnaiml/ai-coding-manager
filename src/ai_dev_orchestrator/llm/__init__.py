"""LLM module - xAI/Grok integration with structured output and logging.

This module provides:
- XAIChatModel: LangChain-compatible chat model for xAI
- Structured output generation with Pydantic validation
- SQLite logging for all LLM calls
- Cost estimation and usage tracking
"""

from ai_dev_orchestrator.llm.xai_langchain import (
    get_xai_chat_model,
    XAIChatModel,
    list_available_models as list_xai_models,
)
from ai_dev_orchestrator.llm.service import (
    generate_structured,
    generate_text,
    check_health,
    is_available,
    get_llm_usage_stats,
    get_available_models,
    get_current_model,
    set_current_model,
    LLMStatus,
    LLMHealthCheck,
    LLMResponse,
    ModelInfo,
)
from ai_dev_orchestrator.llm.rag_chain import (
    create_rag_chain,
    RAGChain,
    RAGResponse,
)

__all__ = [
    # xAI LangChain
    "get_xai_chat_model",
    "XAIChatModel",
    "list_xai_models",
    # Service
    "generate_structured",
    "generate_text",
    "check_health",
    "is_available",
    "get_llm_usage_stats",
    "get_available_models",
    "get_current_model",
    "set_current_model",
    "LLMStatus",
    "LLMHealthCheck",
    "LLMResponse",
    "ModelInfo",
    # RAG
    "create_rag_chain",
    "RAGChain",
    "RAGResponse",
]
