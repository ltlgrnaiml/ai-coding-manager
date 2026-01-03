"""Chat Helper Functions.

Validation and utility functions for the comprehensive chat API.
"""

from typing import Any

from .model_registry import (
    ModelInfo,
    ModelSelectionRequest,
    ToolInfo,
    get_all_tools,
    get_model,
    get_tools_for_model,
    select_model,
)


class ToolValidationError(Exception):
    """Raised when a tool request is invalid for the selected model."""
    def __init__(self, tool_name: str, model_id: str, reason: str):
        self.tool_name = tool_name
        self.model_id = model_id
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' not available for model '{model_id}': {reason}")


class ModelNotFoundError(Exception):
    """Raised when a model is not found in the registry."""
    def __init__(self, model_id: str):
        self.model_id = model_id
        super().__init__(f"Model not found: {model_id}")


def resolve_model(
    model_id: str,
    required_capabilities: list[str] | None = None,
    max_cost_per_mtok: float | None = None,
    prefer_provider: str | None = None,
    task_hint: str | None = None,
) -> ModelInfo:
    """
    Resolve model ID to ModelInfo.
    
    If model_id is 'auto', selects best model based on requirements.
    Otherwise, looks up the specific model.
    """
    if model_id == "auto":
        # Map task hints to capabilities
        task_capabilities = {
            "code_review": ["tools", "reasoning"],
            "code": ["tools"],
            "reasoning": ["reasoning"],
            "vision": ["vision"],
            "chat": [],
            "search": ["web_search"],
        }
        
        caps = list(required_capabilities or [])
        if task_hint and task_hint in task_capabilities:
            caps.extend(task_capabilities[task_hint])
        caps = list(set(caps))  # Dedupe
        
        request = ModelSelectionRequest(
            task_type=task_hint,
            required_capabilities=caps,
            max_cost_per_mtok=max_cost_per_mtok,
            prefer_provider=prefer_provider,
        )
        
        model = select_model(request)
        if not model:
            raise ModelNotFoundError("auto (no matching model found)")
        return model
    
    model = get_model(model_id)
    if not model:
        raise ModelNotFoundError(model_id)
    return model


def validate_tools(
    model: ModelInfo,
    tool_names: list[str],
) -> list[ToolInfo]:
    """
    Validate that requested tools are available for the model.
    
    Returns list of validated ToolInfo objects.
    Raises ToolValidationError if any tool is not available.
    """
    if not tool_names:
        return []
    
    # Check model has tools capability
    if not model.capabilities.tools:
        raise ToolValidationError(
            tool_names[0], 
            model.id, 
            "Model does not support tool use"
        )
    
    # Get available tools for this model's provider
    available_tools = get_all_tools(provider_id=model.provider_id)
    available_map = {t.name: t for t in available_tools}
    
    validated = []
    for name in tool_names:
        if name not in available_map:
            raise ToolValidationError(
                name, 
                model.id, 
                f"Tool not available for provider '{model.provider_id}'"
            )
        
        tool = available_map[name]
        
        # Check specific capability requirements
        if name == "web_search" and not model.capabilities.web_search:
            raise ToolValidationError(name, model.id, "Model does not support web search")
        if name == "code_execution" and not model.capabilities.code_execution:
            raise ToolValidationError(name, model.id, "Model does not support code execution")
        if name == "vision" and not model.capabilities.vision:
            raise ToolValidationError(name, model.id, "Model does not support vision")
        
        validated.append(tool)
    
    return validated


def get_available_tools_for_model(model_id: str) -> dict[str, Any]:
    """
    Get all available tools for a model (for UI autocomplete).
    
    Returns structured data for frontend consumption.
    """
    model = get_model(model_id)
    if not model:
        return {"error": f"Model not found: {model_id}", "tools": [], "capabilities": {}}
    
    # Get provider tools
    provider_tools = get_all_tools(provider_id=model.provider_id)
    
    # Filter based on model capabilities
    available = []
    for tool in provider_tools:
        # Check if tool requires a capability the model doesn't have
        if tool.name == "web_search" and not model.capabilities.web_search:
            continue
        if tool.name == "code_execution" and not model.capabilities.code_execution:
            continue
        
        available.append({
            "id": tool.id,
            "name": tool.name,
            "display_name": tool.display_name or tool.name,
            "description": tool.description,
            "price_per_use": tool.price_per_use,
            "price_per_1k": tool.price_per_1k,
            "token_overhead": tool.token_overhead,
            "parameters_schema": tool.parameters_schema,
        })
    
    # Get capability flags
    caps = model.capabilities.model_dump()
    enabled_caps = [k for k, v in caps.items() if v]
    
    return {
        "model_id": model_id,
        "model_name": model.name,
        "provider_id": model.provider_id,
        "capabilities": caps,
        "enabled_capabilities": enabled_caps,
        "tools": available,
        "supports_tools": model.capabilities.tools,
        "supports_mcp": model.capabilities.mcp,
    }


def estimate_request_tokens(messages: list[dict]) -> int:
    """Estimate token count from messages (rough: ~4 chars per token)."""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return total_chars // 4


def calculate_tool_overhead(tools: list[ToolInfo]) -> int:
    """Calculate total token overhead from tools."""
    return sum(t.token_overhead for t in tools)
