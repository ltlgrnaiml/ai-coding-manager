"""Memory Architecture Package.

Conversation memory system for LLM context management.

This package provides:
- Multi-tier memory storage (episodic, semantic, procedural, working)
- Deterministic context assembly
- Token budget allocation
- Full debug and observability
- Agentic communication interface

Usage:
    from backend.services.memory import (
        assemble_context,
        create_session,
        add_message,
        create_agent,
        create_workflow,
    )
    
    # Create a session
    session = create_session(name="My Chat")
    
    # Add a user message
    add_message(session.id, "user", "Hello, how are you?")
    
    # Assemble context for LLM call
    context = assemble_context(
        session_id=session.id,
        user_message="What's Python?",
        model_id="grok-4-1-fast-reasoning",
        token_budget=2000000,
    )
    
    # Use context.messages for LLM API call
    response = llm_client.chat(messages=context.messages)
    
    # For agentic workflows:
    agent = create_agent("planner", session.id)
    agent.publish("task_plan", {"steps": [...]})
    agent.handoff("coder", state={"task": "implement feature"})
"""

from .models import (
    # Core types
    Memory,
    MemorySession,
    MemoryType,
    MessageRole,
    MemoryPriority,
    
    # Context assembly
    AssembledContext,
    ContextSection,
    ContextSectionType,
    AssemblyOptions,
    DebugInfo,
    TokenAttribution,
    
    # Agentic
    AgentScope,
    SharedMemoryEntry,
    AgentHandoff,
    
    # API models
    AssembleContextRequest,
    AssembleContextResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    SessionCreateRequest,
    AddMemoryRequest,
    MemoryStats,
)

from .database import (
    init_database,
    get_connection,
    get_memory_db_path,
    
    # Session operations
    create_session as db_create_session,
    get_session,
    list_sessions,
    update_session,
    delete_session,
    
    # Memory operations
    add_memory,
    get_memory,
    get_session_memories,
    get_recent_memories,
    search_memories_fts,
    pin_memory,
    unpin_memory,
    
    # Context operations
    save_context,
    get_context,
    get_context_by_hash,
    list_session_contexts,
    
    # Stats
    get_stats,
)

from .assembler import (
    assemble_context,
    replay_context,
    ContextAssembler,
    estimate_tokens,
)

from .agentic import (
    AgentMemoryInterface,
    WorkflowCoordinator,
    create_agent,
    create_workflow,
)

from .integration import (
    get_or_create_session,
    store_message,
    get_context_for_model,
    store_chat_exchange,
    summarize_session_if_needed,
    get_session_stats,
    link_trace_to_context,
    MODEL_CONTEXT_WINDOWS,
)

from .router import router


# =============================================================================
# Convenience Functions
# =============================================================================

def create_session(
    name: str = None,
    metadata: dict = None,
    system_prompt: str = None,
) -> MemorySession:
    """Create a new memory session."""
    session = MemorySession(
        name=name,
        metadata=metadata or {},
    )
    created = db_create_session(session)
    
    if system_prompt:
        add_message(created.id, "system", system_prompt, priority=MemoryPriority.CRITICAL)
    
    return created


def add_message(
    session_id: str,
    role: str,
    content: str,
    priority: int = MemoryPriority.MEDIUM,
    pinned: bool = False,
    metadata: dict = None,
) -> Memory:
    """Add a message to a session."""
    memory = Memory(
        session_id=session_id,
        type=MemoryType.MESSAGE,
        role=MessageRole(role),
        content=content,
        tokens=estimate_tokens(content),
        priority=priority,
        pinned=pinned,
        metadata=metadata or {},
    )
    return add_memory(memory)


def get_context_for_chat(
    session_id: str,
    user_message: str,
    model_id: str,
    token_budget: int = None,
    system_prompt: str = None,
) -> tuple[list[dict], str]:
    """
    Get context ready for LLM chat API.
    
    Returns:
        Tuple of (messages, context_hash)
    """
    if token_budget is None:
        token_budget = 100000  # Default
    
    context = assemble_context(
        session_id=session_id,
        user_message=user_message,
        model_id=model_id,
        token_budget=token_budget,
        system_prompt=system_prompt,
    )
    
    return context.messages, context.context_hash


__all__ = [
    # Core types
    "Memory",
    "MemorySession", 
    "MemoryType",
    "MessageRole",
    "MemoryPriority",
    
    # Context assembly
    "AssembledContext",
    "ContextSection",
    "ContextSectionType",
    "AssemblyOptions",
    "DebugInfo",
    "TokenAttribution",
    
    # Agentic
    "AgentScope",
    "SharedMemoryEntry",
    "AgentHandoff",
    "AgentMemoryInterface",
    "WorkflowCoordinator",
    
    # API models
    "AssembleContextRequest",
    "AssembleContextResponse",
    "MemorySearchRequest",
    "MemorySearchResponse",
    "SessionCreateRequest",
    "AddMemoryRequest",
    "MemoryStats",
    
    # Functions
    "init_database",
    "create_session",
    "get_session",
    "list_sessions",
    "add_message",
    "add_memory",
    "get_memory",
    "get_session_memories",
    "assemble_context",
    "replay_context",
    "get_context_for_chat",
    "create_agent",
    "create_workflow",
    "estimate_tokens",
    "get_stats",
    
    # Integration
    "get_or_create_session",
    "store_message",
    "get_context_for_model",
    "store_chat_exchange",
    "summarize_session_if_needed",
    "get_session_stats",
    "link_trace_to_context",
    "MODEL_CONTEXT_WINDOWS",
    
    # Router
    "router",
]
