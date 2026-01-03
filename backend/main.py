"""AI Dev Orchestrator - FastAPI Backend.

Provides:
- Workflow artifact management (discussions, ADRs, plans)
- AI streaming chat with xAI/Grok
- Knowledge base search
- Phoenix tracing for observability
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.devtools_service import router as devtools_router
from backend.services.research_api import router as research_router
from backend.services.chatlog_service import router as chatlog_router
from backend.services.p2re import router as p2re_router
from backend.services.p2re import model_router
from backend.services.p2re.database import init_database as init_p2re_database
from backend.services.knowledge.database import init_database
from backend.services.knowledge.archive_service import ArchiveService
from backend.services.knowledge.sync_service import SyncService

# Global sync service for watchdog
_sync_service: SyncService | None = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phoenix tracing initialization (sends to external Phoenix container)
# IMPORTANT: Must be initialized at module load time, BEFORE any LLM clients are imported
_tracer_provider = None

def init_phoenix():
    """Initialize Phoenix tracing - sends traces to external Phoenix collector."""
    global _tracer_provider
    
    phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4317")
    
    try:
        # Use Phoenix OTEL for simpler setup
        from phoenix.otel import register
        
        _tracer_provider = register(
            project_name="ai-dev-orchestrator",
            endpoint=phoenix_endpoint,
        )
        
        # Instrument OpenAI SDK (works for xAI too)
        from openinference.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
        
        # Instrument Anthropic SDK
        try:
            from openinference.instrumentation.anthropic import AnthropicInstrumentor
            AnthropicInstrumentor().instrument(tracer_provider=_tracer_provider)
            logger.info("Anthropic SDK instrumented for tracing")
        except ImportError:
            logger.warning("Anthropic instrumentation not available")
        
        logger.info(f"Phoenix tracing initialized - sending to {phoenix_endpoint}")
        logger.info("Phoenix UI available at http://localhost:6006")
        return True
    except ImportError as e:
        logger.warning(f"Phoenix OTEL not available: {e}")
        # Fallback to manual OTEL setup
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from openinference.instrumentation.openai import OpenAIInstrumentor
            
            exporter = OTLPSpanExporter(endpoint=phoenix_endpoint, insecure=True)
            _tracer_provider = TracerProvider()
            _tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
            trace.set_tracer_provider(_tracer_provider)
            
            OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
            
            try:
                from openinference.instrumentation.anthropic import AnthropicInstrumentor
                AnthropicInstrumentor().instrument(tracer_provider=_tracer_provider)
                logger.info("Anthropic SDK instrumented for tracing (fallback)")
            except ImportError:
                pass
            
            logger.info(f"Phoenix tracing initialized (fallback) - sending to {phoenix_endpoint}")
            return True
        except Exception as e2:
            logger.error(f"Failed to initialize Phoenix tracing: {e2}")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix tracing: {e}")
        return False

# Initialize Phoenix at module load time - BEFORE any LLM SDK imports
# This ensures instrumentation patches are applied before clients are created
init_phoenix()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    global _sync_service
    
    # Startup
    logger.info("Starting AI Dev Orchestrator...")
    
    # Initialize SQLite knowledge database
    try:
        init_database()
        logger.info("SQLite knowledge database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize P2RE trace database
    try:
        init_p2re_database()
        logger.info("P2RE trace database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize P2RE database: {e}")
    
    # Note: Phoenix tracing already initialized at module load time
    
    # Initialize sync service and run backfill
    try:
        archive = ArchiveService()
        _sync_service = SyncService(archive)
        
        # Backfill: sync all workspace documents to database
        sync_count = _sync_service.sync_all()
        logger.info(f"Backfill complete: {sync_count} documents synced to AIKH")
        
        # Start watchdog file watcher
        if _sync_service.start_watching():
            logger.info("Watchdog file watcher started - monitoring workspace for changes")
        else:
            logger.warning("Watchdog not available - install 'watchdog' for auto-sync")
    except Exception as e:
        logger.error(f"Failed to initialize sync service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Stop watchdog
    if _sync_service:
        try:
            _sync_service.stop_watching()
            logger.info("Watchdog stopped")
        except:
            pass
    
    if _tracer_provider:
        try:
            _tracer_provider.force_flush()  # Ensure all spans are exported
            _tracer_provider.shutdown()
        except:
            pass


# Initialize FastAPI with lifespan
app = FastAPI(
    title="AI Dev Orchestrator",
    description="Workflow management + AI streaming chat + Phoenix tracing",
    version="2025.12.01",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
app.include_router(research_router, tags=["research"])
app.include_router(chatlog_router, tags=["chatlogs"])
app.include_router(p2re_router, tags=["P2RE - Trace Observability"])
app.include_router(model_router, tags=["Model Registry"])

# Workspace paths
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "."))


# =============================================================================
# Models
# =============================================================================

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: str | None = None


class ToolRequest(BaseModel):
    """Request to use a specific tool."""
    name: str = Field(..., description="Tool name (e.g., 'web_search', 'code_execution')")
    parameters: dict | None = Field(None, description="Tool-specific parameters")


class MCPToolRequest(BaseModel):
    """Request to use an MCP server tool."""
    server_id: str = Field(..., description="MCP server ID")
    tool_name: str = Field(..., description="Tool name from the MCP server")
    parameters: dict | None = Field(None, description="Tool parameters")


class ChatRequest(BaseModel):
    """
    Comprehensive chat request with tool selection and capability checks.
    
    The model field can be:
    - A specific model ID (e.g., 'claude-sonnet-4', 'gemini-2.5-flash')
    - 'auto' to let the system select based on requirements
    
    Tools are validated against the selected model's capabilities.
    """
    messages: list[ChatMessage]
    model: str = Field("grok-4-fast-reasoning", description="Model ID or 'auto' for automatic selection")
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Tool selection
    tools: list[ToolRequest] | None = Field(None, description="Provider tools to enable (validated against model capabilities)")
    mcp_tools: list[MCPToolRequest] | None = Field(None, description="MCP server tools to enable")
    
    # Auto-selection hints (used when model='auto')
    task_hint: str | None = Field(None, description="Task type hint for model selection (e.g., 'code_review', 'chat', 'reasoning')")
    required_capabilities: list[str] | None = Field(None, description="Required capabilities (e.g., ['vision', 'tools', 'reasoning'])")
    max_cost_per_mtok: float | None = Field(None, description="Maximum acceptable cost per million tokens")
    prefer_provider: str | None = Field(None, description="Preferred provider (e.g., 'anthropic', 'google', 'xai')")
    
    # Session tracking
    session_id: str | None = Field(None, description="Session ID for conversation grouping")
    use_rag: bool = Field(True, description="Whether to use RAG context injection")


class ArtifactSummary(BaseModel):
    """Summary of a workflow artifact."""
    id: str
    type: str
    title: str
    status: str
    file_path: str
    updated_at: str | None = None


class WorkflowStats(BaseModel):
    """Statistics about workflow artifacts."""
    discussions: int = 0
    adrs: int = 0
    plans: int = 0
    sessions: int = 0
    questions: int = 0


# =============================================================================
# Workflow Endpoints
# =============================================================================

@app.get("/api/workflow/stats", response_model=WorkflowStats)
async def get_workflow_stats():
    """Get counts of all workflow artifacts."""
    stats = WorkflowStats()
    
    dirs = {
        "discussions": ".discussions",
        "adrs": ".adrs",
        "plans": ".plans",
        "sessions": ".sessions",
        "questions": ".questions",
    }
    
    for stat_name, dir_name in dirs.items():
        dir_path = WORKSPACE_ROOT / dir_name
        if dir_path.exists():
            # Count files (excluding templates and index)
            count = len([
                f for f in dir_path.glob("*") 
                if f.is_file() 
                and not f.name.startswith(".")
                and f.name not in ("INDEX.md", "AGENTS.md")
                and ".templates" not in str(f)
            ])
            setattr(stats, stat_name, count)
    
    return stats


@app.get("/api/workflow/artifacts", response_model=list[ArtifactSummary])
async def list_artifacts(
    artifact_type: str | None = Query(None, description="Filter by type"),
):
    """List all workflow artifacts."""
    artifacts = []
    
    type_dirs = {
        "discussion": ".discussions",
        "adr": ".adrs",
        "plan": ".plans",
        "session": ".sessions",
        "question": ".questions",
    }
    
    # Filter to specific type or list all
    dirs_to_scan = (
        {artifact_type: type_dirs[artifact_type]} 
        if artifact_type and artifact_type in type_dirs 
        else type_dirs
    )
    
    for art_type, dir_name in dirs_to_scan.items():
        dir_path = WORKSPACE_ROOT / dir_name
        if not dir_path.exists():
            continue
            
        for file_path in dir_path.glob("*"):
            if not file_path.is_file():
                continue
            if file_path.name.startswith("."):
                continue
            if file_path.name in ("INDEX.md", "AGENTS.md"):
                continue
            if ".templates" in str(file_path):
                continue
                
            # Parse artifact info from filename
            artifact_id = file_path.stem
            title = artifact_id
            status = "active"
            
            # Try to extract better title/status from content
            try:
                content = file_path.read_text(encoding="utf-8")
                if file_path.suffix == ".json":
                    data = json.loads(content)
                    title = data.get("title", artifact_id)
                    status = data.get("status", "active")
                elif file_path.suffix == ".md":
                    # Extract title from first # heading
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break
            except Exception:
                pass
            
            artifacts.append(ArtifactSummary(
                id=artifact_id,
                type=art_type,
                title=title,
                status=status,
                file_path=str(file_path.relative_to(WORKSPACE_ROOT)),
                updated_at=datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
            ))
    
    # Sort by updated_at descending
    artifacts.sort(key=lambda a: a.updated_at or "", reverse=True)
    return artifacts


@app.get("/api/workflow/artifact/{artifact_type}/{artifact_id}")
async def get_artifact(artifact_type: str, artifact_id: str):
    """Get a specific artifact's content."""
    type_dirs = {
        "discussion": ".discussions",
        "adr": ".adrs",
        "plan": ".plans",
        "session": ".sessions",
        "question": ".questions",
    }
    
    if artifact_type not in type_dirs:
        raise HTTPException(400, f"Unknown artifact type: {artifact_type}")
    
    dir_path = WORKSPACE_ROOT / type_dirs[artifact_type]
    
    # Try different extensions
    for ext in [".json", ".md"]:
        file_path = dir_path / f"{artifact_id}{ext}"
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            if ext == ".json":
                return {"type": "json", "data": json.loads(content)}
            else:
                return {"type": "markdown", "content": content}
    
    raise HTTPException(404, f"Artifact not found: {artifact_id}")


# =============================================================================
# Chat Endpoints
# =============================================================================

# Model pricing per 1M tokens (input, output) in USD
MODEL_PRICING = {
    # Anthropic
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    # xAI
    "grok-4-0709": (3.00, 15.00),
    "grok-4-fast-reasoning": (5.00, 25.00),
    "grok-4-1-fast-reasoning": (5.00, 25.00),
    "grok-3-beta": (3.00, 15.00),
    # Google
    "gemini-2.0-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}

def _calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Calculate cost in USD based on model pricing."""
    pricing = MODEL_PRICING.get(model, (1.0, 3.0))  # Default fallback
    cost_in = (tokens_in / 1_000_000) * pricing[0]
    cost_out = (tokens_out / 1_000_000) * pricing[1]
    return round(cost_in + cost_out, 6)


async def stream_chat_response(
    messages: list[ChatMessage],
    model: str,
    temperature: float,
    max_tokens: int,
    use_rag: bool = True,
    session_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream chat response from appropriate provider based on model."""
    import logging
    import time
    from backend.services.llm.registry import get_provider_for_model
    from backend.services.llm.types import ChatMessage as LLMMessage
    from backend.services.p2re import capture_trace, complete_trace
    
    logging.info(f"Chat request using model: {model}")
    
    # Inject RAG context if enabled and there are user messages
    if use_rag and messages:
        messages = _inject_rag_context(messages)
    
    # Extract user prompt for trace capture
    user_prompt = ""
    system_prompt = None
    for msg in messages:
        if msg.role == "user":
            user_prompt = msg.content
        elif msg.role == "system":
            system_prompt = msg.content
    
    # Determine provider name
    is_gemini = model.startswith("gemini")
    provider_name = "google" if is_gemini else "xai"
    provider = None if is_gemini else get_provider_for_model(model)
    if provider:
        provider_name = provider.name
    
    # Capture trace at request time
    trace_id = None
    start_time = time.time()
    try:
        trace_id = capture_trace(
            provider=provider_name,
            model=model,
            user_prompt=user_prompt or "No user message",
            system_prompt=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            session_id=session_id,
            source_file="backend/main.py",
            source_function="stream_chat_response",
            tags=["chat", "streaming"],
        )
    except Exception as e:
        logging.warning(f"Failed to capture trace: {e}")
    
    # Estimate input tokens from messages (rough: ~4 chars per token)
    input_text = "".join(m.content for m in messages)
    tokens_in_estimate = len(input_text) // 4
    
    # Collect full response for trace completion
    full_response = []
    tokens_out = 0
    error_occurred = None
    
    try:
        if is_gemini:
            async for chunk in _stream_gemini(messages, model, temperature, max_tokens):
                yield chunk
                # Extract content from SSE data
                if chunk.startswith("data: ") and "content" in chunk:
                    try:
                        data = json.loads(chunk[6:])
                        if "content" in data:
                            full_response.append(data["content"])
                    except:
                        pass
        else:
            if provider:
                llm_messages = [LLMMessage(role=m.role, content=m.content) for m in messages]
                async for chunk in provider.chat_stream(llm_messages, model, temperature, max_tokens):
                    # Handle error content (may come with is_final=True)
                    if chunk.content:
                        if chunk.content.startswith("Error:"):
                            # Send error as proper error payload
                            yield f"data: {json.dumps({'error': chunk.content, 'model': model, 'provider': provider.name})}\n\n"
                            error_occurred = Exception(chunk.content)
                        else:
                            full_response.append(chunk.content)
                            yield f"data: {json.dumps({'content': chunk.content, 'model': model, 'provider': provider.name})}\n\n"
                    if chunk.is_final:
                        yield "data: [DONE]\n\n"
            else:
                async for chunk in _stream_xai(messages, model, temperature, max_tokens):
                    yield chunk
                    if chunk.startswith("data: ") and "content" in chunk:
                        try:
                            data = json.loads(chunk[6:])
                            if "content" in data:
                                full_response.append(data["content"])
                        except:
                            pass
    except Exception as e:
        error_occurred = e
        logging.error(f"Error during streaming: {e}")
        raise
    finally:
        # Complete trace with response data
        if trace_id:
            latency_ms = int((time.time() - start_time) * 1000)
            response_text = "".join(full_response)
            tokens_out_final = tokens_out or len(response_text) // 4
            
            # Calculate cost based on model pricing (per 1M tokens)
            cost_usd = _calculate_cost(model, tokens_in_estimate, tokens_out_final)
            
            try:
                complete_trace(
                    trace_id=trace_id,
                    response_content=response_text,
                    tokens_in=tokens_in_estimate,
                    tokens_out=tokens_out_final,
                    latency_ms=latency_ms,
                    cost_usd=cost_usd,
                    error=error_occurred,
                )
            except Exception as e:
                logging.warning(f"Failed to complete trace: {e}")


def _inject_rag_context(messages: list[ChatMessage]) -> list[ChatMessage]:
    """Inject relevant knowledge context into the conversation."""
    try:
        from backend.services.knowledge.retrieval import get_knowledge_context
        
        # Get the last user message for context retrieval
        last_user_msg = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break
        
        if not last_user_msg:
            return messages
        
        # Retrieve relevant context
        context = get_knowledge_context(last_user_msg, max_tokens=1500)
        
        if not context:
            return messages
        
        # Inject context as system message at the start
        system_msg = ChatMessage(
            role="system",
            content=f"Use the following knowledge context to help answer the user's question:\n\n{context}"
        )
        
        # Check if there's already a system message
        if messages and messages[0].role == "system":
            # Append context to existing system message
            messages[0].content += f"\n\n{context}"
            return messages
        else:
            # Add new system message
            return [system_msg] + list(messages)
    
    except Exception as e:
        import logging
        logging.warning(f"RAG context injection failed: {e}")
        return messages


async def _stream_xai(
    messages: list[ChatMessage],
    model: str,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    """Stream from xAI/Grok API."""
    from openai import OpenAI
    
    api_key = os.getenv("XAI_API_KEY", "")
    if not api_key:
        yield f"data: {json.dumps({'error': 'XAI_API_KEY not configured'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )
    
    try:
        oai_messages = [{"role": m.role, "content": m.content} for m in messages]
        stream = client.chat.completions.create(
            model=model,
            messages=oai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'content': content, 'model': model, 'provider': 'xai'})}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


async def _stream_gemini(
    messages: list[ChatMessage],
    model: str,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[str, None]:
    """Stream from Google Gemini API."""
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        yield f"data: {json.dumps({'error': 'GOOGLE_API_KEY not configured'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    try:
        genai.configure(api_key=api_key)
        
        # Convert messages to Gemini format
        gemini_messages = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            gemini_messages.append({"role": role, "parts": [m.content]})
        
        # Create model and generate
        gemini_model = genai.GenerativeModel(model)
        
        # Use streaming
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            stream=True,
        )
        
        for chunk in response:
            if chunk.text:
                yield f"data: {json.dumps({'content': chunk.text, 'model': model, 'provider': 'google'})}\n\n"
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat completion from xAI."""
    return StreamingResponse(
        stream_chat_response(
            request.messages,
            request.model,
            request.temperature,
            request.max_tokens,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/chat/models")
async def list_models():
    """List available chat models from all providers."""
    from backend.services.llm.registry import get_models_for_api, get_available_providers
    
    models = get_models_for_api()
    providers = [p.name for p in get_available_providers()]
    
    # Add Gemini models (not yet in adapter system)
    gemini_models = [
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "category": "gemini", "context": "1M", "provider": "google", "supports_tools": True, "supports_vision": False},
        {"id": "gemini-2.0-flash-thinking", "name": "Gemini 2.0 Flash Thinking", "category": "gemini-reasoning", "context": "32K", "provider": "google", "supports_tools": True, "supports_vision": False},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "category": "gemini", "context": "2M", "provider": "google", "supports_tools": True, "supports_vision": True},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "category": "gemini", "context": "1M", "provider": "google", "supports_tools": True, "supports_vision": False},
    ]
    
    return {
        "models": models + gemini_models,
        "providers": providers + (["google"] if os.getenv("GOOGLE_API_KEY") else []),
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key = os.getenv("XAI_API_KEY", "")
    return {
        "status": "healthy",
        "api_key_configured": bool(api_key),
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# Knowledge Search
# =============================================================================

@app.get("/api/knowledge/search")
async def search_knowledge(q: str = Query(..., description="Search query")):
    """Search knowledge base."""
    # Simple file-based search for now
    results = []
    
    for dir_name in [".discussions", ".adrs", ".plans"]:
        dir_path = WORKSPACE_ROOT / dir_name
        if not dir_path.exists():
            continue
            
        for file_path in dir_path.glob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                if q.lower() in content.lower():
                    results.append({
                        "file": str(file_path.relative_to(WORKSPACE_ROOT)),
                        "snippet": content[:200] + "..." if len(content) > 200 else content,
                    })
            except Exception:
                pass
    
    return {"query": q, "results": results[:20]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
