"""P2RE API Router.

REST endpoints for trace management and observability.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .database import init_database
from .models import (
    Evaluation,
    EvaluationCreate,
    P2REStats,
    Trace,
    TraceListResponse,
    TraceResponse,
    TraceSession,
    TraceSummary,
    TraceStatus,
)
from .service import (
    create_evaluation,
    get_evaluations_for_trace,
    get_session,
    get_stats,
    get_trace,
    list_sessions,
    list_traces,
)

router = APIRouter(prefix="/api/p2re", tags=["P2RE - Trace Observability"])


@router.on_event("startup")
async def startup():
    """Initialize P2RE database on startup."""
    init_database()


# =============================================================================
# Trace Endpoints
# =============================================================================

@router.get("/traces", response_model=TraceListResponse)
async def list_traces_endpoint(
    session_id: str | None = Query(None, description="Filter by session"),
    provider: str | None = Query(None, description="Filter by provider (xai, anthropic, google)"),
    model: str | None = Query(None, description="Filter by model"),
    status: TraceStatus | None = Query(None, description="Filter by status"),
    since: datetime | None = Query(None, description="Filter traces after this time"),
    until: datetime | None = Query(None, description="Filter traces before this time"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
) -> TraceListResponse:
    """List traces with optional filtering."""
    offset = (page - 1) * page_size
    items, total = list_traces(
        session_id=session_id,
        provider=provider,
        model=model,
        status=status,
        since=since,
        until=until,
        limit=page_size,
        offset=offset,
    )
    return TraceListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/traces/{trace_id}", response_model=TraceResponse)
async def get_trace_endpoint(trace_id: str) -> TraceResponse:
    """Get a single trace with its evaluations."""
    trace = get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    evaluations = get_evaluations_for_trace(trace_id)
    return TraceResponse(trace=trace, evaluations=evaluations)


# =============================================================================
# Session Endpoints
# =============================================================================

@router.get("/sessions")
async def list_sessions_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """List trace sessions."""
    offset = (page - 1) * page_size
    sessions, total = list_sessions(limit=page_size, offset=offset)
    return {
        "items": [s.model_dump() for s in sessions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/sessions/{session_id}")
async def get_session_endpoint(session_id: str) -> dict[str, Any]:
    """Get a session with its traces."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    traces, _ = list_traces(session_id=session_id, limit=100)
    return {
        "session": session.model_dump(),
        "traces": [t.model_dump() for t in traces],
    }


# =============================================================================
# Evaluation Endpoints
# =============================================================================

@router.post("/evaluations", response_model=dict[str, Any])
async def create_evaluation_endpoint(data: EvaluationCreate) -> dict[str, Any]:
    """Create an evaluation for a trace."""
    # Verify trace exists
    trace = get_trace(data.trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {data.trace_id} not found")
    
    eval_id = create_evaluation(data)
    return {"id": eval_id, "message": f"Evaluation created for trace {data.trace_id}"}


@router.get("/traces/{trace_id}/evaluations", response_model=list[Evaluation])
async def get_trace_evaluations(trace_id: str) -> list[Evaluation]:
    """Get all evaluations for a trace."""
    return get_evaluations_for_trace(trace_id)


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/stats", response_model=P2REStats)
async def get_stats_endpoint() -> P2REStats:
    """Get P2RE usage statistics."""
    return get_stats()


@router.get("/stats/daily")
async def get_daily_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    provider: str | None = Query(None),
    model: str | None = Query(None),
) -> dict[str, Any]:
    """Get daily aggregated statistics."""
    from .database import get_connection
    
    conn = get_connection()
    try:
        conditions = ["1=1"]
        params: list[Any] = []
        
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        if model:
            conditions.append("model = ?")
            params.append(model)
        
        where_clause = " AND ".join(conditions)
        
        rows = conn.execute(
            f"""
            SELECT 
                date(request_timestamp) as date,
                provider,
                model,
                COUNT(*) as trace_count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(tokens_in) as tokens_in,
                SUM(tokens_out) as tokens_out,
                SUM(cost_usd) as cost_usd,
                AVG(latency_ms) as avg_latency
            FROM traces
            WHERE request_timestamp >= datetime('now', '-{days} days')
            AND {where_clause}
            GROUP BY date(request_timestamp), provider, model
            ORDER BY date DESC
            """,
            params,
        ).fetchall()
        
        return {
            "days": days,
            "data": [
                {
                    "date": r["date"],
                    "provider": r["provider"],
                    "model": r["model"],
                    "trace_count": r["trace_count"],
                    "success_count": r["success_count"],
                    "error_count": r["error_count"],
                    "tokens_in": r["tokens_in"] or 0,
                    "tokens_out": r["tokens_out"] or 0,
                    "cost_usd": r["cost_usd"] or 0.0,
                    "avg_latency_ms": r["avg_latency"],
                }
                for r in rows
            ],
        }
    finally:
        conn.close()


# =============================================================================
# Model Statistics
# =============================================================================

@router.get("/models")
async def get_model_stats() -> dict[str, Any]:
    """Get statistics per model."""
    from .database import get_connection
    
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT 
                provider,
                model,
                COUNT(*) as total_traces,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                SUM(tokens_in) as total_tokens_in,
                SUM(tokens_out) as total_tokens_out,
                SUM(cost_usd) as total_cost,
                AVG(latency_ms) as avg_latency,
                MIN(request_timestamp) as first_used,
                MAX(request_timestamp) as last_used
            FROM traces
            GROUP BY provider, model
            ORDER BY total_traces DESC
            """
        ).fetchall()
        
        return {
            "models": [
                {
                    "provider": r["provider"],
                    "model": r["model"],
                    "total_traces": r["total_traces"],
                    "success_rate": r["success_count"] / r["total_traces"] if r["total_traces"] > 0 else 0,
                    "total_tokens_in": r["total_tokens_in"] or 0,
                    "total_tokens_out": r["total_tokens_out"] or 0,
                    "total_cost_usd": r["total_cost"] or 0.0,
                    "avg_latency_ms": r["avg_latency"],
                    "first_used": r["first_used"],
                    "last_used": r["last_used"],
                }
                for r in rows
            ]
        }
    finally:
        conn.close()
