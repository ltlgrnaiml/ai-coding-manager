"""Memory Architecture - Core Models.

Pydantic models for the conversation memory system.
All models are designed for deterministic hashing and full observability.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, computed_field


class MemoryType(str, Enum):
    """Types of memories stored in the system."""
    MESSAGE = "message"           # Chat message
    FACT = "fact"                 # Extracted fact/preference
    TOOL_OUTPUT = "tool_output"   # Tool execution result
    SUMMARY = "summary"           # Compressed history
    RAG_RESULT = "rag_result"     # Retrieved content
    SYSTEM = "system"             # System prompt
    AGENT_STATE = "agent_state"   # Agentic workflow state


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContextSectionType(str, Enum):
    """Types of sections in assembled context."""
    SYSTEM = "system"
    WORKING_MEMORY = "working_memory"
    PINNED = "pinned"
    RAG = "rag"
    HISTORY = "history"
    SUMMARY = "summary"
    USER_MESSAGE = "user_message"


class MemoryPriority(int, Enum):
    """Priority levels for memory inclusion."""
    CRITICAL = 100    # Always include (system, current message)
    HIGH = 80         # Strongly prefer (pinned, recent)
    MEDIUM = 50       # Include if space (RAG, history)
    LOW = 20          # Include if plenty of space
    MINIMAL = 10      # Only if nothing else


# =============================================================================
# Core Memory Models
# =============================================================================

class Memory(BaseModel):
    """A single memory unit in the system."""
    id: str = Field(default_factory=lambda: f"mem_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    session_id: Optional[str] = None
    type: MemoryType
    role: Optional[MessageRole] = None
    content: str
    tokens: int = 0
    priority: int = MemoryPriority.MEDIUM
    pinned: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    
    @computed_field
    @property
    def content_hash(self) -> str:
        """SHA-256 hash of content for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]
    
    def to_message(self) -> dict:
        """Convert to LLM message format."""
        return {
            "role": self.role.value if self.role else "user",
            "content": self.content,
        }


class MemorySession(BaseModel):
    """A conversation session containing memories."""
    id: str = Field(default_factory=lambda: f"ses_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
    summary: Optional[str] = None
    summary_hash: Optional[str] = None
    total_messages: int = 0
    total_tokens: int = 0
    
    model_config = {"extra": "allow"}


class PinnedMemory(BaseModel):
    """User-pinned memory for persistent inclusion."""
    id: str
    session_id: str
    memory_id: str
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Context Assembly Models
# =============================================================================

class ContextSection(BaseModel):
    """A section of the assembled context."""
    type: ContextSectionType
    content: str
    tokens: int
    priority: int
    source_ids: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    
    @computed_field
    @property
    def content_hash(self) -> str:
        """Hash of section content."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


class AssemblyOptions(BaseModel):
    """Options for context assembly."""
    role: str = "assistant"
    history_limit: int = 50
    rag_sources: list[str] = Field(default_factory=lambda: ["research", "traces", "code"])
    include_summary: bool = True
    include_related_traces: bool = True
    max_rag_results: int = 5
    compression_threshold: float = 0.9  # Compress if > 90% budget used
    
    # Budget allocation percentages
    system_budget_pct: float = 0.05
    working_memory_budget_pct: float = 0.10
    user_message_budget_pct: float = 0.05
    pinned_budget_pct: float = 0.10
    rag_budget_pct: float = 0.20
    history_budget_pct: float = 0.40
    summary_budget_pct: float = 0.05
    related_budget_pct: float = 0.05


class TokenAttribution(BaseModel):
    """Token usage attribution for debugging."""
    section_type: ContextSectionType
    tokens: int
    percentage: float
    source_count: int
    sources: list[str]  # Memory IDs or descriptions


class DebugInfo(BaseModel):
    """Debug information for context assembly."""
    candidates_considered: int
    candidates_included: int
    candidates_excluded: int
    compression_applied: bool
    token_attributions: list[TokenAttribution]
    assembly_time_ms: float
    cache_hits: int
    cache_misses: int
    excluded_reasons: dict[str, int] = Field(default_factory=dict)


class AssembledContext(BaseModel):
    """The fully assembled context ready for LLM."""
    context_id: str = Field(default_factory=lambda: f"ctx_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    session_id: str
    assembled_at: datetime = Field(default_factory=datetime.utcnow)
    model_id: str
    token_budget: int
    tokens_used: int
    sections: list[ContextSection]
    messages: list[dict]  # LLM-ready message format
    debug_info: Optional[DebugInfo] = None
    trace_id: Optional[str] = None  # Link to P2RE trace
    
    @computed_field
    @property
    def context_hash(self) -> str:
        """Deterministic hash of assembled context."""
        normalized = {
            "schema_version": "1.0.0",
            "sections": [
                {
                    "type": s.type.value,
                    "content_hash": s.content_hash,
                    "priority": s.priority,
                }
                for s in sorted(self.sections, key=lambda x: x.type.value)
            ]
        }
        content = json.dumps(normalized, sort_keys=True)
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:32]}"
    
    @computed_field
    @property
    def budget_utilization(self) -> float:
        """Percentage of token budget used."""
        return self.tokens_used / max(self.token_budget, 1)


# =============================================================================
# Agentic Communication Models
# =============================================================================

class AgentScope(str, Enum):
    """Scope for shared memory visibility."""
    PRIVATE = "private"       # Only this agent
    SESSION = "session"       # All agents in session
    WORKFLOW = "workflow"     # All agents in workflow
    GLOBAL = "global"         # All agents


class SharedMemoryEntry(BaseModel):
    """Entry in shared agent memory."""
    key: str
    value: Any
    scope: AgentScope
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    version: int = 1


class AgentHandoff(BaseModel):
    """State transfer between agents."""
    id: str = Field(default_factory=lambda: f"hnd_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    from_agent: str
    to_agent: str
    session_id: str
    state: dict
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# API Request/Response Models
# =============================================================================

class AssembleContextRequest(BaseModel):
    """Request to assemble context for a session."""
    session_id: str
    user_message: str
    model_id: str
    token_budget: Optional[int] = None  # Auto-detect from model
    options: AssemblyOptions = Field(default_factory=AssemblyOptions)
    include_debug: bool = True


class AssembleContextResponse(BaseModel):
    """Response with assembled context."""
    context: AssembledContext
    ready_for_llm: bool = True
    warnings: list[str] = Field(default_factory=list)


class MemorySearchRequest(BaseModel):
    """Request to search memories semantically."""
    query: str
    session_id: Optional[str] = None  # None = search all sessions
    types: list[MemoryType] = Field(default_factory=list)  # Empty = all types
    limit: int = 10
    min_score: float = 0.5


class MemorySearchResult(BaseModel):
    """Single search result."""
    memory: Memory
    score: float
    snippet: str


class MemorySearchResponse(BaseModel):
    """Response with search results."""
    results: list[MemorySearchResult]
    total: int
    query_embedding_cached: bool


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    name: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    initial_system_prompt: Optional[str] = None


class AddMemoryRequest(BaseModel):
    """Request to add a memory to a session."""
    session_id: str
    type: MemoryType
    role: Optional[MessageRole] = None
    content: str
    priority: int = MemoryPriority.MEDIUM
    pinned: bool = False
    metadata: dict = Field(default_factory=dict)


class ContextReplayRequest(BaseModel):
    """Request to replay a context assembly."""
    context_id: str
    with_modifications: dict = Field(default_factory=dict)


class MemoryStats(BaseModel):
    """Statistics for the memory system."""
    total_sessions: int
    total_memories: int
    total_tokens: int
    total_contexts_assembled: int
    cache_hit_rate: float
    avg_assembly_time_ms: float
    memories_by_type: dict[str, int]
    top_sessions: list[dict]
