"""P2RE - Prompts to Response Ecosystem.

LLM interaction observability for the AI Dev Orchestrator.
"""

from .database import get_connection, init_database
from .models import (
    Evaluation,
    EvaluationCreate,
    EvaluationType,
    P2REStats,
    PromptCategory,
    PromptTemplate,
    PromptTemplateCreate,
    Trace,
    TraceCreate,
    TraceListResponse,
    TraceMessage,
    TraceResponse,
    TraceSession,
    TraceSessionCreate,
    TraceStatus,
    TraceSummary,
    TraceUpdate,
)
from .router import router
from .service import (
    capture_trace,
    complete_trace,
    create_evaluation,
    create_session,
    create_trace,
    get_evaluations_for_trace,
    get_or_create_session,
    get_session,
    get_stats,
    get_trace,
    list_sessions,
    list_traces,
    update_trace,
)

__all__ = [
    # Database
    "init_database",
    "get_connection",
    # Router
    "router",
    # Models
    "Trace",
    "TraceCreate",
    "TraceUpdate",
    "TraceSummary",
    "TraceMessage",
    "TraceStatus",
    "TraceSession",
    "TraceSessionCreate",
    "TraceListResponse",
    "TraceResponse",
    "Evaluation",
    "EvaluationCreate",
    "EvaluationType",
    "PromptTemplate",
    "PromptTemplateCreate",
    "PromptCategory",
    "P2REStats",
    # Service functions
    "capture_trace",
    "complete_trace",
    "create_trace",
    "update_trace",
    "get_trace",
    "list_traces",
    "create_session",
    "get_session",
    "get_or_create_session",
    "list_sessions",
    "create_evaluation",
    "get_evaluations_for_trace",
    "get_stats",
]
