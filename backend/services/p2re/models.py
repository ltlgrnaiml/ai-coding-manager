"""P2RE Pydantic Models.

Data models for the Prompts to Response Ecosystem.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TraceStatus(str, Enum):
    """Status of an LLM trace."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class EvaluationType(str, Enum):
    """Type of evaluation."""
    HUMAN = "human"
    AUTO = "auto"
    LLM_JUDGE = "llm_judge"


class ExperimentStatus(str, Enum):
    """Status of an experiment."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class PromptCategory(str, Enum):
    """Category of prompt template."""
    SYSTEM = "system"
    TASK = "task"
    EXTRACTION = "extraction"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    CHAT = "chat"


# =============================================================================
# Trace Models
# =============================================================================

class TraceMessage(BaseModel):
    """A single message in a trace."""
    role: str
    content: str


class ToolCall(BaseModel):
    """A tool call in a trace."""
    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool call."""
    tool_call_id: str
    content: str
    is_error: bool = False


class TraceCreate(BaseModel):
    """Model for creating a new trace."""
    session_id: str | None = None
    parent_trace_id: str | None = None
    
    provider: str
    model: str
    
    system_prompt: str | None = None
    user_prompt: str
    prompt_template_id: str | None = None
    prompt_variables: dict[str, Any] | None = None
    
    messages: list[TraceMessage] | None = None
    
    source_file: str | None = None
    source_function: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class TraceUpdate(BaseModel):
    """Model for updating a trace with response."""
    response_content: str | None = None
    response_role: str = "assistant"
    finish_reason: str | None = None
    
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None
    
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int | None = None
    cost_usd: float = 0.0
    
    status: TraceStatus = TraceStatus.SUCCESS
    error_message: str | None = None
    error_type: str | None = None


class Trace(BaseModel):
    """Full trace model."""
    id: str
    session_id: str | None = None
    parent_trace_id: str | None = None
    
    provider: str
    model: str
    request_timestamp: datetime
    
    system_prompt: str | None = None
    user_prompt: str
    prompt_template_id: str | None = None
    prompt_variables: dict[str, Any] | None = None
    
    messages: list[TraceMessage] | None = None
    
    response_timestamp: datetime | None = None
    response_content: str | None = None
    response_role: str = "assistant"
    finish_reason: str | None = None
    
    tool_calls: list[ToolCall] | None = None
    tool_results: list[ToolResult] | None = None
    
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int | None = None
    cost_usd: float = 0.0
    
    status: TraceStatus = TraceStatus.SUCCESS
    error_message: str | None = None
    error_type: str | None = None
    
    source_file: str | None = None
    source_function: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    
    created_at: datetime


class TraceSummary(BaseModel):
    """Summary view of a trace for listings."""
    id: str
    provider: str
    model: str
    request_timestamp: datetime
    
    user_prompt_preview: str = Field(..., description="First 100 chars of user prompt")
    response_preview: str | None = Field(None, description="First 100 chars of response")
    
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int | None = None
    cost_usd: float = 0.0
    
    status: TraceStatus = TraceStatus.SUCCESS
    has_tool_calls: bool = False


# =============================================================================
# Prompt Template Models
# =============================================================================

class PromptTemplateCreate(BaseModel):
    """Model for creating a prompt template."""
    id: str
    name: str
    description: str | None = None
    category: PromptCategory = PromptCategory.TASK
    
    system_template: str | None = None
    user_template: str
    
    variables_schema: dict[str, Any] | None = None


class PromptTemplate(BaseModel):
    """Full prompt template model."""
    id: str
    name: str
    description: str | None = None
    category: PromptCategory
    
    system_template: str | None = None
    user_template: str
    
    variables_schema: dict[str, Any] | None = None
    
    version: int = 1
    is_active: bool = True
    
    usage_count: int = 0
    avg_tokens_in: float = 0
    avg_tokens_out: float = 0
    avg_latency_ms: float = 0
    avg_quality_score: float | None = None
    
    created_at: datetime
    updated_at: datetime


class PromptTemplateSummary(BaseModel):
    """Summary view of a prompt template."""
    id: str
    name: str
    category: PromptCategory
    version: int
    is_active: bool
    usage_count: int
    avg_quality_score: float | None = None


# =============================================================================
# Evaluation Models
# =============================================================================

class EvaluationCreate(BaseModel):
    """Model for creating an evaluation."""
    trace_id: str
    eval_type: EvaluationType
    evaluator: str | None = None
    
    overall_score: float | None = Field(None, ge=0.0, le=1.0)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    accuracy_score: float | None = Field(None, ge=0.0, le=1.0)
    helpfulness_score: float | None = Field(None, ge=0.0, le=1.0)
    safety_score: float | None = Field(None, ge=0.0, le=1.0)
    
    feedback_text: str | None = None
    issues: list[str] | None = None
    
    experiment_id: str | None = None
    variant: str | None = None


class Evaluation(BaseModel):
    """Full evaluation model."""
    id: int
    trace_id: str
    eval_type: EvaluationType
    evaluator: str | None = None
    
    overall_score: float | None = None
    relevance_score: float | None = None
    accuracy_score: float | None = None
    helpfulness_score: float | None = None
    safety_score: float | None = None
    
    feedback_text: str | None = None
    issues: list[str] | None = None
    
    experiment_id: str | None = None
    variant: str | None = None
    
    created_at: datetime


# =============================================================================
# Session Models
# =============================================================================

class TraceSessionCreate(BaseModel):
    """Model for creating a trace session."""
    id: str
    title: str | None = None
    source: str = "chat"
    user_id: str | None = None
    metadata: dict[str, Any] | None = None


class TraceSession(BaseModel):
    """Full trace session model."""
    id: str
    title: str | None = None
    
    trace_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float | None = None
    
    source: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] | None = None
    
    first_trace_at: datetime | None = None
    last_trace_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Statistics Models
# =============================================================================

class DailyRollup(BaseModel):
    """Daily aggregated statistics."""
    date: str
    provider: str
    model: str
    
    trace_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    
    latency_p50: int | None = None
    latency_p90: int | None = None
    latency_p99: int | None = None
    
    avg_quality_score: float | None = None


class P2REStats(BaseModel):
    """Overall P2RE statistics."""
    total_traces: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    
    traces_today: int = 0
    tokens_today: int = 0
    cost_today: float = 0.0
    
    active_sessions: int = 0
    prompt_templates: int = 0
    evaluations: int = 0
    
    top_models: list[dict[str, Any]] = Field(default_factory=list)
    recent_errors: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# API Response Models
# =============================================================================

class TraceListResponse(BaseModel):
    """Response for trace list endpoint."""
    items: list[TraceSummary]
    total: int
    page: int = 1
    page_size: int = 50


class TraceResponse(BaseModel):
    """Response for single trace endpoint."""
    trace: Trace
    evaluations: list[Evaluation] = Field(default_factory=list)
