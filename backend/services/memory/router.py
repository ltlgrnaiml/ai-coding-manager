"""Memory Architecture - API Router.

FastAPI endpoints for the conversation memory system.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from .models import (
    Memory, MemorySession, MemoryType, MessageRole,
    AssembledContext, AssemblyOptions,
    AssembleContextRequest, AssembleContextResponse,
    MemorySearchRequest, MemorySearchResponse, MemorySearchResult,
    SessionCreateRequest, AddMemoryRequest, ContextReplayRequest,
    MemoryStats, MemoryPriority,
)
from . import database as db
from .assembler import assemble_context, replay_context, estimate_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["Memory Architecture"])


# =============================================================================
# Session Endpoints
# =============================================================================

@router.post("/sessions", response_model=MemorySession)
async def create_session(request: SessionCreateRequest):
    """Create a new memory session."""
    session = MemorySession(
        name=request.name,
        metadata=request.metadata,
    )
    
    created = db.create_session(session)
    
    # Add initial system prompt if provided
    if request.initial_system_prompt:
        memory = Memory(
            session_id=created.id,
            type=MemoryType.SYSTEM,
            role=MessageRole.SYSTEM,
            content=request.initial_system_prompt,
            tokens=estimate_tokens(request.initial_system_prompt),
            priority=MemoryPriority.CRITICAL,
        )
        db.add_memory(memory)
    
    logger.info(f"Created session: {created.id}")
    return created


@router.get("/sessions", response_model=list[MemorySession])
async def list_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List memory sessions."""
    return db.list_sessions(limit=limit, offset=offset)


@router.get("/sessions/{session_id}", response_model=MemorySession)
async def get_session(session_id: str):
    """Get a session by ID."""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its memories."""
    success = db.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return {"deleted": session_id}


@router.get("/sessions/{session_id}/memories", response_model=list[Memory])
async def get_session_memories(
    session_id: str,
    types: Optional[str] = Query(None, description="Comma-separated memory types"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    pinned_only: bool = Query(False),
):
    """Get memories for a session."""
    type_list = None
    if types:
        type_list = [MemoryType(t.strip()) for t in types.split(",")]
    
    return db.get_session_memories(
        session_id=session_id,
        types=type_list,
        limit=limit,
        offset=offset,
        pinned_only=pinned_only,
    )


# =============================================================================
# Memory Endpoints
# =============================================================================

@router.post("/memories", response_model=Memory)
async def add_memory(request: AddMemoryRequest):
    """Add a memory to a session."""
    # Verify session exists
    session = db.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")
    
    memory = Memory(
        session_id=request.session_id,
        type=request.type,
        role=request.role,
        content=request.content,
        tokens=estimate_tokens(request.content),
        priority=request.priority,
        pinned=request.pinned,
        metadata=request.metadata,
    )
    
    created = db.add_memory(memory)
    logger.info(f"Added memory {created.id} to session {request.session_id}")
    return created


@router.get("/memories/{memory_id}", response_model=Memory)
async def get_memory(memory_id: str):
    """Get a memory by ID."""
    memory = db.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory not found: {memory_id}")
    return memory


@router.post("/memories/{memory_id}/pin")
async def pin_memory(
    memory_id: str,
    session_id: str = Query(...),
    label: Optional[str] = Query(None),
):
    """Pin a memory for persistent inclusion."""
    success = db.pin_memory(session_id, memory_id, label)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to pin memory")
    return {"pinned": memory_id, "session_id": session_id}


@router.delete("/memories/{memory_id}/pin")
async def unpin_memory(
    memory_id: str,
    session_id: str = Query(...),
):
    """Unpin a memory."""
    success = db.unpin_memory(session_id, memory_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unpin memory")
    return {"unpinned": memory_id, "session_id": session_id}


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(request: MemorySearchRequest):
    """Search memories semantically."""
    # Full-text search
    results = db.search_memories_fts(
        query=request.query,
        session_id=request.session_id,
        limit=request.limit,
    )
    
    search_results = []
    for memory in results:
        # Create snippet
        content = memory.content
        snippet = content[:200] + "..." if len(content) > 200 else content
        
        search_results.append(MemorySearchResult(
            memory=memory,
            score=0.8,  # Placeholder score
            snippet=snippet,
        ))
    
    return MemorySearchResponse(
        results=search_results,
        total=len(search_results),
        query_embedding_cached=False,
    )


# =============================================================================
# Context Assembly Endpoints
# =============================================================================

@router.post("/context/assemble", response_model=AssembleContextResponse)
async def assemble_context_endpoint(request: AssembleContextRequest):
    """Assemble context for an LLM call."""
    # Verify session exists or create it
    session = db.get_session(request.session_id)
    if not session:
        session = MemorySession(id=request.session_id)
        db.create_session(session)
    
    # Get token budget from model if not specified
    token_budget = request.token_budget
    if not token_budget:
        # Default based on model (can be enhanced with model registry lookup)
        token_budget = 100000
    
    # Assemble context
    context = assemble_context(
        session_id=request.session_id,
        user_message=request.user_message,
        model_id=request.model_id,
        token_budget=token_budget,
        options=request.options,
    )
    
    # Check for warnings
    warnings = []
    if context.budget_utilization > 0.9:
        warnings.append(f"High context utilization: {context.budget_utilization:.1%}")
    if context.tokens_used > token_budget:
        warnings.append("Context exceeds budget - some content may be truncated")
    
    return AssembleContextResponse(
        context=context,
        ready_for_llm=True,
        warnings=warnings,
    )


@router.get("/context/{context_id}", response_model=AssembledContext)
async def get_context(context_id: str):
    """Get a previously assembled context."""
    context = db.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    return context


@router.get("/context/by-hash/{context_hash:path}", response_model=AssembledContext)
async def get_context_by_hash(context_hash: str):
    """Get context by its deterministic hash."""
    context = db.get_context_by_hash(context_hash)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context not found for hash: {context_hash}")
    return context


@router.post("/context/replay", response_model=AssembledContext)
async def replay_context_endpoint(request: ContextReplayRequest):
    """Replay a context assembly with optional modifications."""
    context = replay_context(request.context_id, request.with_modifications)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context not found: {request.context_id}")
    return context


@router.get("/sessions/{session_id}/contexts")
async def list_session_contexts(
    session_id: str,
    limit: int = Query(20, ge=1, le=100),
):
    """List context assemblies for a session."""
    return db.list_session_contexts(session_id, limit)


# =============================================================================
# Debug Endpoints
# =============================================================================

@router.get("/debug/{context_id}")
async def get_context_debug(context_id: str):
    """Get detailed debug information for a context assembly."""
    context = db.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    
    return {
        "context_id": context.context_id,
        "context_hash": context.context_hash,
        "model_id": context.model_id,
        "token_budget": context.token_budget,
        "tokens_used": context.tokens_used,
        "budget_utilization": context.budget_utilization,
        "section_breakdown": [
            {
                "type": s.type.value,
                "tokens": s.tokens,
                "percentage": s.tokens / max(context.tokens_used, 1),
                "sources": len(s.source_ids),
                "content_preview": s.content[:100] + "..." if len(s.content) > 100 else s.content,
            }
            for s in context.sections
        ],
        "debug_info": context.debug_info.model_dump() if context.debug_info else None,
        "messages_count": len(context.messages),
        "trace_id": context.trace_id,
    }


@router.get("/debug/{context_id}/diff/{other_context_id}")
async def diff_contexts(context_id: str, other_context_id: str):
    """Compare two context assemblies."""
    ctx1 = db.get_context(context_id)
    ctx2 = db.get_context(other_context_id)
    
    if not ctx1:
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
    if not ctx2:
        raise HTTPException(status_code=404, detail=f"Context not found: {other_context_id}")
    
    # Build comparison
    sections1 = {s.type.value: s for s in ctx1.sections}
    sections2 = {s.type.value: s for s in ctx2.sections}
    
    all_types = set(sections1.keys()) | set(sections2.keys())
    
    section_diffs = []
    for section_type in all_types:
        s1 = sections1.get(section_type)
        s2 = sections2.get(section_type)
        
        diff = {
            "type": section_type,
            "in_first": s1 is not None,
            "in_second": s2 is not None,
        }
        
        if s1 and s2:
            diff["tokens_diff"] = s2.tokens - s1.tokens
            diff["content_changed"] = s1.content_hash != s2.content_hash
        
        section_diffs.append(diff)
    
    return {
        "context_1": {"id": ctx1.context_id, "hash": ctx1.context_hash, "tokens": ctx1.tokens_used},
        "context_2": {"id": ctx2.context_id, "hash": ctx2.context_hash, "tokens": ctx2.tokens_used},
        "tokens_diff": ctx2.tokens_used - ctx1.tokens_used,
        "hash_match": ctx1.context_hash == ctx2.context_hash,
        "section_diffs": section_diffs,
    }


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats():
    """Get memory system statistics."""
    stats = db.get_stats()
    
    return MemoryStats(
        total_sessions=stats["total_sessions"],
        total_memories=stats["total_memories"],
        total_tokens=stats["total_tokens"],
        total_contexts_assembled=stats["total_contexts"],
        cache_hit_rate=0.0,  # TODO: Implement cache tracking
        avg_assembly_time_ms=0.0,  # TODO: Implement timing tracking
        memories_by_type=stats["memories_by_type"],
        top_sessions=stats["top_sessions"],
    )


@router.get("/health")
async def memory_health():
    """Health check for memory system."""
    try:
        stats = db.get_stats()
        return {
            "healthy": True,
            "sessions": stats["total_sessions"],
            "memories": stats["total_memories"],
            "database": str(db.get_memory_db_path()),
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
        }
