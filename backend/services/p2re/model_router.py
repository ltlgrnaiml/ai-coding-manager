"""Model Registry API Router.

Endpoints for querying models, tools, and cost estimation.
"""

from fastapi import APIRouter, HTTPException, Query

from .model_registry import (
    CostEstimateRequest,
    CostEstimateResponse,
    ModelInfo,
    ModelSelectionRequest,
    ProviderInfo,
    ToolInfo,
    estimate_cost,
    get_all_models,
    get_all_providers,
    get_all_tools,
    get_model,
    get_tools_for_model,
    seed_all,
    select_model,
)
from .chat_helpers import get_available_tools_for_model

router = APIRouter(prefix="/api/models", tags=["Model Registry"])


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    """Get all active providers."""
    return get_all_providers()


@router.get("", response_model=list[ModelInfo])
async def list_models(
    provider: str | None = Query(None, description="Filter by provider ID"),
    capability: str | None = Query(None, description="Filter by capability (e.g., 'vision', 'tools', 'reasoning')"),
):
    """Get all active models with optional filters."""
    return get_all_models(provider_id=provider, capability=capability)


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools(
    provider: str | None = Query(None, description="Filter by provider ID"),
):
    """Get all available tools."""
    return get_all_tools(provider_id=provider)


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model_info(model_id: str):
    """Get detailed information for a specific model."""
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    return model


@router.get("/{model_id}/tools", response_model=list[ToolInfo])
async def get_model_tools(model_id: str):
    """Get tools available for a specific model."""
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    return get_tools_for_model(model_id)


@router.post("/select", response_model=ModelInfo | None)
async def select_best_model(request: ModelSelectionRequest):
    """
    Select the best model based on requirements.
    
    Returns the model that best matches the criteria, or null if none found.
    """
    model = select_model(request)
    if not model:
        raise HTTPException(
            status_code=404, 
            detail="No model matches the specified requirements"
        )
    return model


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_request_cost(request: CostEstimateRequest):
    """
    Estimate the cost for a request.
    
    Provides detailed breakdown of input, output, and tool costs.
    """
    return estimate_cost(request)


@router.post("/seed")
async def seed_registry():
    """
    Seed the model registry with initial data.
    
    This populates providers, models, and tools from the extracted pricing data.
    """
    result = seed_all()
    return {
        "success": True,
        "seeded": result,
        "message": f"Seeded {result['providers']} providers, {result['models']} models, {result['tools']} tools"
    }


@router.get("/{model_id}/capabilities")
async def get_model_capabilities(model_id: str):
    """Get capability flags for a model (for UI autocomplete)."""
    model = get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
    
    caps = model.capabilities.model_dump()
    available = [k for k, v in caps.items() if v]
    
    return {
        "model_id": model_id,
        "capabilities": caps,
        "available": available,
        "tools": [t.model_dump() for t in get_tools_for_model(model_id)]
    }


@router.get("/{model_id}/autocomplete")
async def get_model_autocomplete(model_id: str):
    """
    Get complete autocomplete data for a model.
    
    Returns all tools, capabilities, and metadata for UI autocomplete.
    Used by the chat input to show available tools based on selected model.
    """
    data = get_available_tools_for_model(model_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/refresh/status")
async def get_refresh_status():
    """Get the status of the pricing refresh system."""
    from .database import get_connection
    
    conn = get_connection()
    try:
        # Get last refresh time from pricing_history
        row = conn.execute(
            "SELECT MAX(recorded_at) as last_refresh FROM pricing_history"
        ).fetchone()
        
        last_refresh = row["last_refresh"] if row else None
        
        # Count models
        model_count = conn.execute("SELECT COUNT(*) as c FROM models").fetchone()["c"]
        tool_count = conn.execute("SELECT COUNT(*) as c FROM model_tools").fetchone()["c"]
        
        return {
            "last_refresh": last_refresh,
            "models_count": model_count,
            "tools_count": tool_count,
            "refresh_interval": "weekly",
            "next_refresh": "Manual trigger required (POST /api/models/refresh)"
        }
    finally:
        conn.close()


@router.post("/refresh")
async def trigger_refresh():
    """
    Trigger a manual pricing refresh.
    
    Re-seeds the database with latest pricing data and records history.
    In production, this would fetch from provider APIs.
    """
    from datetime import datetime
    from .database import get_connection
    
    # Re-seed data
    result = seed_all()
    
    # Record in pricing history
    conn = get_connection()
    try:
        models = get_all_models()
        for model in models:
            conn.execute(
                """
                INSERT INTO pricing_history (model_id, input_price, output_price, source)
                VALUES (?, ?, ?, ?)
                """,
                (model.id, model.pricing.input_per_mtok, model.pricing.output_per_mtok, "manual_refresh")
            )
        conn.commit()
    finally:
        conn.close()
    
    return {
        "success": True,
        "refreshed_at": datetime.utcnow().isoformat(),
        "models_updated": result["models"],
        "tools_updated": result["tools"],
    }
