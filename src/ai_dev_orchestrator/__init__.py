"""AI Dev Orchestrator - Framework for structured, AI-assisted code development.

This package provides:
- LLM integration (xAI/Grok with structured output)
- Knowledge/RAG system with SQLite-backed storage
- Phoenix observability for LLM tracing
- LangChain adapters and chains
- Workflow automation tools

Example:
    from ai_dev_orchestrator import get_xai_chat_model, create_rag_chain
    
    # Simple LLM usage
    llm = get_xai_chat_model()
    response = llm.invoke("Hello!")
    
    # RAG chain with knowledge archive
    chain = create_rag_chain()
    answer = chain.invoke("What ADRs relate to authentication?")
"""

__version__ = "2025.12.01"

# Re-export key components for convenience
from ai_dev_orchestrator.llm.xai_langchain import get_xai_chat_model, XAIChatModel
from ai_dev_orchestrator.llm.service import (
    generate_structured,
    generate_text,
    check_health,
    is_available,
    get_llm_usage_stats,
    get_available_models,
    get_current_model,
    set_current_model,
)
from ai_dev_orchestrator.llm.rag_chain import create_rag_chain, RAGChain, RAGResponse
from ai_dev_orchestrator.knowledge.database import init_database, get_connection
from ai_dev_orchestrator.observability.phoenix_tracer import init_phoenix, shutdown_phoenix

__all__ = [
    # Version
    "__version__",
    # LLM
    "get_xai_chat_model",
    "XAIChatModel",
    "generate_structured",
    "generate_text",
    "check_health",
    "is_available",
    "get_llm_usage_stats",
    "get_available_models",
    "get_current_model",
    "set_current_model",
    # RAG
    "create_rag_chain",
    "RAGChain",
    "RAGResponse",
    # Knowledge
    "init_database",
    "get_connection",
    # Observability
    "init_phoenix",
    "shutdown_phoenix",
]
