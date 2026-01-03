"""Memory Architecture - Chat Flow Integration.

Integrates the memory system with the existing chat endpoints.
Provides helpers for session management and context assembly during chat.
"""

import logging
from typing import Optional

from .models import (
    Memory, MemorySession, MemoryType, MessageRole, MemoryPriority,
    AssembledContext, AssemblyOptions,
)
from . import database as db
from .assembler import assemble_context, estimate_tokens

logger = logging.getLogger(__name__)


# Model context windows (can be enhanced with model registry lookup)
MODEL_CONTEXT_WINDOWS = {
    # Anthropic
    "claude-sonnet-4-20250514": 200000,
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-5-haiku-20241022": 200000,
    # xAI
    "grok-4-0709": 256000,
    "grok-4-fast-reasoning": 2000000,
    "grok-4-1-fast-reasoning": 2000000,
    "grok-4-1-fast-non-reasoning": 2000000,
    "grok-3-beta": 131072,
    # Google
    "gemini-2.0-flash": 1000000,
    "gemini-1.5-pro": 2000000,
}


def get_or_create_session(session_id: Optional[str], name: Optional[str] = None) -> MemorySession:
    """
    Get existing session or create new one.
    
    Args:
        session_id: Optional session ID. If None, creates new session.
        name: Optional name for new session.
    
    Returns:
        MemorySession
    """
    if session_id:
        session = db.get_session(session_id)
        if session:
            return session
    
    # Create new session
    session = MemorySession(
        id=session_id,  # Use provided ID or generate new
        name=name or "Chat Session",
    )
    return db.create_session(session)


def store_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None,
) -> Memory:
    """
    Store a message in the session.
    
    Args:
        session_id: Session ID
        role: Message role (user, assistant, system)
        content: Message content
        metadata: Optional metadata
    
    Returns:
        Created Memory
    """
    memory = Memory(
        session_id=session_id,
        type=MemoryType.MESSAGE,
        role=MessageRole(role),
        content=content,
        tokens=estimate_tokens(content),
        priority=MemoryPriority.MEDIUM if role != "system" else MemoryPriority.HIGH,
        metadata=metadata or {},
    )
    return db.add_memory(memory)


def get_context_for_model(
    session_id: str,
    user_message: str,
    model: str,
    system_prompt: Optional[str] = None,
    use_rag: bool = True,
    custom_options: Optional[AssemblyOptions] = None,
) -> AssembledContext:
    """
    Assemble context optimized for the specified model.
    
    Args:
        session_id: Session ID
        user_message: Current user message
        model: Model ID
        system_prompt: Optional system prompt override
        use_rag: Whether to include RAG results
        custom_options: Optional custom assembly options
    
    Returns:
        AssembledContext with messages ready for LLM
    """
    # Get token budget from model
    token_budget = MODEL_CONTEXT_WINDOWS.get(model, 100000)
    
    # Reserve 20% for response
    token_budget = int(token_budget * 0.8)
    
    # Configure options
    options = custom_options or AssemblyOptions()
    
    if not use_rag:
        options.rag_sources = []
    
    return assemble_context(
        session_id=session_id,
        user_message=user_message,
        model_id=model,
        token_budget=token_budget,
        system_prompt=system_prompt,
        options=options,
    )


def store_chat_exchange(
    session_id: str,
    user_message: str,
    assistant_response: str,
    model: str,
    context_hash: Optional[str] = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost: float = 0.0,
) -> tuple[Memory, Memory]:
    """
    Store a complete chat exchange (user + assistant).
    
    Args:
        session_id: Session ID
        user_message: User's message
        assistant_response: Assistant's response
        model: Model used
        context_hash: Hash of context used (for debugging)
        tokens_in: Input tokens
        tokens_out: Output tokens
        cost: Cost in USD
    
    Returns:
        Tuple of (user_memory, assistant_memory)
    """
    # Store user message
    user_mem = store_message(
        session_id=session_id,
        role="user",
        content=user_message,
        metadata={"context_hash": context_hash},
    )
    
    # Store assistant response
    assistant_mem = store_message(
        session_id=session_id,
        role="assistant",
        content=assistant_response,
        metadata={
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "context_hash": context_hash,
        },
    )
    
    return user_mem, assistant_mem


def summarize_session_if_needed(session_id: str, threshold_tokens: int = 50000) -> bool:
    """
    Summarize older messages if session exceeds token threshold.
    
    This helps keep context manageable for long conversations.
    
    Args:
        session_id: Session ID
        threshold_tokens: Token count threshold to trigger summarization
    
    Returns:
        True if summarization was performed
    """
    session = db.get_session(session_id)
    if not session or session.total_tokens < threshold_tokens:
        return False
    
    # TODO: Implement actual summarization via LLM
    # For now, just log that it would be done
    logger.info(f"Session {session_id} has {session.total_tokens} tokens - summarization needed")
    
    return False


def get_session_stats(session_id: str) -> dict:
    """Get statistics for a session."""
    session = db.get_session(session_id)
    if not session:
        return {}
    
    contexts = db.list_session_contexts(session_id, limit=10)
    
    return {
        "session_id": session_id,
        "name": session.name,
        "total_messages": session.total_messages,
        "total_tokens": session.total_tokens,
        "has_summary": session.summary is not None,
        "recent_contexts": len(contexts),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def link_trace_to_context(context_id: str, trace_id: str) -> None:
    """
    Link a P2RE trace to a context assembly.
    
    This enables tracing from trace → context → memories for debugging.
    """
    context = db.get_context(context_id)
    if context:
        context.trace_id = trace_id
        # Re-save with trace link
        db.save_context(context)
