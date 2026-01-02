"""Observability module - Phoenix tracing for LLM calls.

This module provides:
- OpenTelemetry-based tracing for LangChain/LangGraph calls
- Phoenix UI integration for local observability
- Custom span creation for tracking operations
"""

from ai_dev_orchestrator.observability.phoenix_tracer import (
    init_phoenix,
    shutdown_phoenix,
    get_tracer,
    trace_span,
    is_tracing_enabled,
)

__all__ = [
    "init_phoenix",
    "shutdown_phoenix",
    "get_tracer",
    "trace_span",
    "is_tracing_enabled",
]
