"""P2RE Service Layer.

Business logic for trace capture, retrieval, and analysis.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from .database import get_connection
from .models import (
    DailyRollup,
    Evaluation,
    EvaluationCreate,
    P2REStats,
    PromptTemplate,
    PromptTemplateCreate,
    PromptTemplateSummary,
    Trace,
    TraceCreate,
    TraceMessage,
    TraceSession,
    TraceSessionCreate,
    TraceStatus,
    TraceSummary,
    TraceUpdate,
    ToolCall,
    ToolResult,
)


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return f"tr_{uuid.uuid4().hex[:16]}"


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return f"sess_{uuid.uuid4().hex[:12]}"


# =============================================================================
# Trace Operations
# =============================================================================

def create_trace(data: TraceCreate) -> str:
    """Create a new trace record. Returns trace ID."""
    trace_id = generate_trace_id()
    now = datetime.utcnow().isoformat()
    
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO traces (
                id, session_id, parent_trace_id,
                provider, model, request_timestamp,
                system_prompt, user_prompt, prompt_template_id, prompt_variables,
                messages, source_file, source_function, tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                data.session_id,
                data.parent_trace_id,
                data.provider,
                data.model,
                now,
                data.system_prompt,
                data.user_prompt,
                data.prompt_template_id,
                json.dumps(data.prompt_variables) if data.prompt_variables else None,
                json.dumps([m.model_dump() for m in data.messages]) if data.messages else None,
                data.source_file,
                data.source_function,
                json.dumps(data.tags) if data.tags else None,
                json.dumps(data.metadata) if data.metadata else None,
            ),
        )
        conn.commit()
        return trace_id
    finally:
        conn.close()


def update_trace(trace_id: str, data: TraceUpdate) -> bool:
    """Update a trace with response data. Returns success."""
    now = datetime.utcnow().isoformat()
    
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE traces SET
                response_timestamp = ?,
                response_content = ?,
                response_role = ?,
                finish_reason = ?,
                tool_calls = ?,
                tool_results = ?,
                tokens_in = ?,
                tokens_out = ?,
                latency_ms = ?,
                cost_usd = ?,
                status = ?,
                error_message = ?,
                error_type = ?
            WHERE id = ?
            """,
            (
                now,
                data.response_content,
                data.response_role,
                data.finish_reason,
                json.dumps([t.model_dump() for t in data.tool_calls]) if data.tool_calls else None,
                json.dumps([t.model_dump() for t in data.tool_results]) if data.tool_results else None,
                data.tokens_in,
                data.tokens_out,
                data.latency_ms,
                data.cost_usd,
                data.status.value,
                data.error_message,
                data.error_type,
                trace_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_trace(trace_id: str) -> Trace | None:
    """Get a trace by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM traces WHERE id = ?",
            (trace_id,),
        ).fetchone()
        
        if not row:
            return None
        
        return _row_to_trace(row)
    finally:
        conn.close()


def list_traces(
    session_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    status: TraceStatus | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[TraceSummary], int]:
    """List traces with filtering. Returns (items, total_count)."""
    conn = get_connection()
    try:
        conditions = []
        params: list[Any] = []
        
        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        if model:
            conditions.append("model = ?")
            params.append(model)
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        if since:
            conditions.append("request_timestamp >= ?")
            params.append(since.isoformat())
        if until:
            conditions.append("request_timestamp <= ?")
            params.append(until.isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count
        count_row = conn.execute(
            f"SELECT COUNT(*) FROM traces WHERE {where_clause}",
            params,
        ).fetchone()
        total = count_row[0] if count_row else 0
        
        # Get items
        rows = conn.execute(
            f"""
            SELECT * FROM traces 
            WHERE {where_clause}
            ORDER BY request_timestamp DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        
        items = [_row_to_trace_summary(row) for row in rows]
        return items, total
    finally:
        conn.close()


def _row_to_trace(row: Any) -> Trace:
    """Convert a database row to a Trace model."""
    return Trace(
        id=row["id"],
        session_id=row["session_id"],
        parent_trace_id=row["parent_trace_id"],
        provider=row["provider"],
        model=row["model"],
        request_timestamp=datetime.fromisoformat(row["request_timestamp"]),
        system_prompt=row["system_prompt"],
        user_prompt=row["user_prompt"],
        prompt_template_id=row["prompt_template_id"],
        prompt_variables=json.loads(row["prompt_variables"]) if row["prompt_variables"] else None,
        messages=[TraceMessage(**m) for m in json.loads(row["messages"])] if row["messages"] else None,
        response_timestamp=datetime.fromisoformat(row["response_timestamp"]) if row["response_timestamp"] else None,
        response_content=row["response_content"],
        response_role=row["response_role"] or "assistant",
        finish_reason=row["finish_reason"],
        tool_calls=[ToolCall(**t) for t in json.loads(row["tool_calls"])] if row["tool_calls"] else None,
        tool_results=[ToolResult(**t) for t in json.loads(row["tool_results"])] if row["tool_results"] else None,
        tokens_in=row["tokens_in"] or 0,
        tokens_out=row["tokens_out"] or 0,
        latency_ms=row["latency_ms"],
        cost_usd=row["cost_usd"] or 0.0,
        status=TraceStatus(row["status"]) if row["status"] else TraceStatus.SUCCESS,
        error_message=row["error_message"],
        error_type=row["error_type"],
        source_file=row["source_file"],
        source_function=row["source_function"],
        tags=json.loads(row["tags"]) if row["tags"] else None,
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_trace_summary(row: Any) -> TraceSummary:
    """Convert a database row to a TraceSummary model."""
    user_prompt = row["user_prompt"] or ""
    response = row["response_content"] or ""
    
    return TraceSummary(
        id=row["id"],
        provider=row["provider"],
        model=row["model"],
        request_timestamp=datetime.fromisoformat(row["request_timestamp"]),
        user_prompt_preview=user_prompt[:100] + "..." if len(user_prompt) > 100 else user_prompt,
        response_preview=response[:100] + "..." if len(response) > 100 else response if response else None,
        tokens_in=row["tokens_in"] or 0,
        tokens_out=row["tokens_out"] or 0,
        latency_ms=row["latency_ms"],
        cost_usd=row["cost_usd"] or 0.0,
        status=TraceStatus(row["status"]) if row["status"] else TraceStatus.SUCCESS,
        has_tool_calls=bool(row["tool_calls"]),
    )


# =============================================================================
# Session Operations
# =============================================================================

def create_session(data: TraceSessionCreate) -> str:
    """Create a new trace session."""
    now = datetime.utcnow().isoformat()
    
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO trace_sessions (id, title, source, user_id, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.id,
                data.title,
                data.source,
                data.user_id,
                json.dumps(data.metadata) if data.metadata else None,
                now,
                now,
            ),
        )
        conn.commit()
        return data.id
    finally:
        conn.close()


def get_or_create_session(session_id: str, title: str | None = None) -> str:
    """Get existing session or create new one."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM trace_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        
        if row:
            return row["id"]
        
        # Create new session
        return create_session(TraceSessionCreate(
            id=session_id,
            title=title,
            source="chat",
        ))
    finally:
        conn.close()


def get_session(session_id: str) -> TraceSession | None:
    """Get a session by ID."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM trace_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        
        if not row:
            return None
        
        return TraceSession(
            id=row["id"],
            title=row["title"],
            trace_count=row["trace_count"] or 0,
            total_tokens_in=row["total_tokens_in"] or 0,
            total_tokens_out=row["total_tokens_out"] or 0,
            total_cost_usd=row["total_cost_usd"] or 0.0,
            avg_latency_ms=row["avg_latency_ms"],
            source=row["source"],
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
            first_trace_at=datetime.fromisoformat(row["first_trace_at"]) if row["first_trace_at"] else None,
            last_trace_at=datetime.fromisoformat(row["last_trace_at"]) if row["last_trace_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
    finally:
        conn.close()


def list_sessions(limit: int = 50, offset: int = 0) -> tuple[list[TraceSession], int]:
    """List trace sessions."""
    conn = get_connection()
    try:
        count_row = conn.execute("SELECT COUNT(*) FROM trace_sessions").fetchone()
        total = count_row[0] if count_row else 0
        
        rows = conn.execute(
            """
            SELECT * FROM trace_sessions 
            ORDER BY last_trace_at DESC NULLS LAST, created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        
        sessions = []
        for row in rows:
            sessions.append(TraceSession(
                id=row["id"],
                title=row["title"],
                trace_count=row["trace_count"] or 0,
                total_tokens_in=row["total_tokens_in"] or 0,
                total_tokens_out=row["total_tokens_out"] or 0,
                total_cost_usd=row["total_cost_usd"] or 0.0,
                avg_latency_ms=row["avg_latency_ms"],
                source=row["source"],
                user_id=row["user_id"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                first_trace_at=datetime.fromisoformat(row["first_trace_at"]) if row["first_trace_at"] else None,
                last_trace_at=datetime.fromisoformat(row["last_trace_at"]) if row["last_trace_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            ))
        
        return sessions, total
    finally:
        conn.close()


# =============================================================================
# Evaluation Operations
# =============================================================================

def create_evaluation(data: EvaluationCreate) -> int:
    """Create a new evaluation."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO evaluations (
                trace_id, eval_type, evaluator,
                overall_score, relevance_score, accuracy_score, helpfulness_score, safety_score,
                feedback_text, issues, experiment_id, variant
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.trace_id,
                data.eval_type.value,
                data.evaluator,
                data.overall_score,
                data.relevance_score,
                data.accuracy_score,
                data.helpfulness_score,
                data.safety_score,
                data.feedback_text,
                json.dumps(data.issues) if data.issues else None,
                data.experiment_id,
                data.variant,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_evaluations_for_trace(trace_id: str) -> list[Evaluation]:
    """Get all evaluations for a trace."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM evaluations WHERE trace_id = ? ORDER BY created_at DESC",
            (trace_id,),
        ).fetchall()
        
        return [
            Evaluation(
                id=row["id"],
                trace_id=row["trace_id"],
                eval_type=row["eval_type"],
                evaluator=row["evaluator"],
                overall_score=row["overall_score"],
                relevance_score=row["relevance_score"],
                accuracy_score=row["accuracy_score"],
                helpfulness_score=row["helpfulness_score"],
                safety_score=row["safety_score"],
                feedback_text=row["feedback_text"],
                issues=json.loads(row["issues"]) if row["issues"] else None,
                experiment_id=row["experiment_id"],
                variant=row["variant"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
    finally:
        conn.close()


# =============================================================================
# Statistics
# =============================================================================

def get_stats() -> P2REStats:
    """Get overall P2RE statistics."""
    conn = get_connection()
    try:
        today = datetime.utcnow().date().isoformat()
        
        # Overall totals
        totals = conn.execute(
            """
            SELECT 
                COUNT(*) as total_traces,
                COALESCE(SUM(tokens_in), 0) as total_tokens_in,
                COALESCE(SUM(tokens_out), 0) as total_tokens_out,
                COALESCE(SUM(cost_usd), 0) as total_cost
            FROM traces
            """
        ).fetchone()
        
        # Today's stats
        today_stats = conn.execute(
            """
            SELECT 
                COUNT(*) as traces,
                COALESCE(SUM(tokens_in + tokens_out), 0) as tokens,
                COALESCE(SUM(cost_usd), 0) as cost
            FROM traces
            WHERE date(request_timestamp) = ?
            """,
            (today,),
        ).fetchone()
        
        # Counts
        sessions_count = conn.execute(
            "SELECT COUNT(*) FROM trace_sessions WHERE last_trace_at >= datetime('now', '-24 hours')"
        ).fetchone()[0]
        
        templates_count = conn.execute(
            "SELECT COUNT(*) FROM prompt_templates WHERE is_active = 1"
        ).fetchone()[0]
        
        evals_count = conn.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        
        # Top models
        top_models = conn.execute(
            """
            SELECT provider, model, COUNT(*) as count, SUM(tokens_in + tokens_out) as tokens
            FROM traces
            WHERE request_timestamp >= datetime('now', '-7 days')
            GROUP BY provider, model
            ORDER BY count DESC
            LIMIT 5
            """
        ).fetchall()
        
        # Recent errors
        recent_errors = conn.execute(
            """
            SELECT id, model, error_type, error_message, request_timestamp
            FROM traces
            WHERE status = 'error'
            ORDER BY request_timestamp DESC
            LIMIT 5
            """
        ).fetchall()
        
        return P2REStats(
            total_traces=totals["total_traces"] or 0,
            total_tokens_in=totals["total_tokens_in"] or 0,
            total_tokens_out=totals["total_tokens_out"] or 0,
            total_cost_usd=totals["total_cost"] or 0.0,
            traces_today=today_stats["traces"] or 0,
            tokens_today=today_stats["tokens"] or 0,
            cost_today=today_stats["cost"] or 0.0,
            active_sessions=sessions_count or 0,
            prompt_templates=templates_count or 0,
            evaluations=evals_count or 0,
            top_models=[
                {"provider": r["provider"], "model": r["model"], "count": r["count"], "tokens": r["tokens"]}
                for r in top_models
            ],
            recent_errors=[
                {"id": r["id"], "model": r["model"], "error_type": r["error_type"], 
                 "error_message": r["error_message"], "timestamp": r["request_timestamp"]}
                for r in recent_errors
            ],
        )
    finally:
        conn.close()


# =============================================================================
# High-Level Trace Capture (for integration with LLM providers)
# =============================================================================

def capture_trace(
    provider: str,
    model: str,
    user_prompt: str,
    system_prompt: str | None = None,
    messages: list[dict[str, str]] | None = None,
    session_id: str | None = None,
    source_file: str | None = None,
    source_function: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    High-level function to capture a trace at request time.
    Returns trace_id to be used for updating with response.
    """
    # Ensure session exists if provided
    if session_id:
        get_or_create_session(session_id)
    
    trace_data = TraceCreate(
        session_id=session_id,
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        messages=[TraceMessage(**m) for m in messages] if messages else None,
        source_file=source_file,
        source_function=source_function,
        tags=tags,
        metadata=metadata,
    )
    
    return create_trace(trace_data)


def complete_trace(
    trace_id: str,
    response_content: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    latency_ms: int | None = None,
    cost_usd: float = 0.0,
    finish_reason: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    error: Exception | None = None,
) -> bool:
    """
    High-level function to complete a trace with response data.
    """
    if error:
        update_data = TraceUpdate(
            status=TraceStatus.ERROR,
            error_message=str(error),
            error_type=type(error).__name__,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
        )
    else:
        update_data = TraceUpdate(
            response_content=response_content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            finish_reason=finish_reason,
            tool_calls=[ToolCall(**t) for t in tool_calls] if tool_calls else None,
            status=TraceStatus.SUCCESS,
        )
    
    return update_trace(trace_id, update_data)
