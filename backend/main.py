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
from backend.services.knowledge.database import init_database

# Import research API as sub-application
try:
    from backend.services.research_api import app as research_app
    RESEARCH_API_AVAILABLE = True
except ImportError as e:
    RESEARCH_API_AVAILABLE = False
    research_app = None
    print(f"Research API not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Phoenix tracing initialization (sends to external Phoenix container)
_tracer_provider = None

def init_phoenix():
    """Initialize Phoenix tracing - sends traces to external Phoenix collector."""
    global _tracer_provider
    
    phoenix_endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4317")
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from openinference.instrumentation.openai import OpenAIInstrumentor
        
        # Create OTLP exporter pointing to Phoenix collector
        exporter = OTLPSpanExporter(endpoint=phoenix_endpoint, insecure=True)
        
        # Set up tracer provider with batch processor
        _tracer_provider = TracerProvider()
        _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(_tracer_provider)
        
        # Instrument OpenAI SDK (works for xAI too)
        OpenAIInstrumentor().instrument(tracer_provider=_tracer_provider)
        
        logger.info(f"Phoenix tracing initialized - sending to {phoenix_endpoint}")
        logger.info("Phoenix UI available at http://localhost:6006")
        return True
    except ImportError as e:
        logger.warning(f"OpenTelemetry/Phoenix instrumentation not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix tracing: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting AI Dev Orchestrator...")
    
    # Initialize SQLite knowledge database
    try:
        init_database()
        logger.info("SQLite knowledge database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize Phoenix tracing (connects to external Phoenix container)
    init_phoenix()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if _tracer_provider:
        try:
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

# Include research API routes (GPU search, AIKH endpoints)
# NOTE: We import and include the router, not mount the app, to avoid shadowing main routes
if RESEARCH_API_AVAILABLE:
    try:
        from backend.services.research_api import router as research_router
        app.include_router(research_router)
        logger.info("Research API router included (provides /api/gpu/*, /api/aikh/*)")
    except ImportError as e:
        logger.warning(f"Could not import research router: {e}")

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


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list[ChatMessage]
    model: str = "grok-4-fast-reasoning"
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 4096


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

async def stream_chat_response(
    messages: list[ChatMessage],
    model: str,
    temperature: float,
    max_tokens: int,
    use_rag: bool = True,
) -> AsyncGenerator[str, None]:
    """Stream chat response from xAI or Google API based on model."""
    import logging
    logging.info(f"Chat request using model: {model}")
    
    # Inject RAG context if enabled and there are user messages
    if use_rag and messages:
        messages = _inject_rag_context(messages)
    
    # Route to appropriate provider based on model
    is_gemini = model.startswith("gemini")
    
    if is_gemini:
        # Use Google Gemini API
        async for chunk in _stream_gemini(messages, model, temperature, max_tokens):
            yield chunk
    else:
        # Use xAI API
        async for chunk in _stream_xai(messages, model, temperature, max_tokens):
            yield chunk


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
    """List available chat models."""
    return {
        "models": [
            # Fast reasoning models (2M context)
            {"id": "grok-4-1-fast-reasoning", "name": "Grok 4.1 Fast (Reasoning)", "category": "reasoning", "context": "2M"},
            {"id": "grok-4-fast-reasoning", "name": "Grok 4 Fast (Reasoning)", "category": "reasoning", "context": "2M"},
            # Fast non-reasoning models (2M context)
            {"id": "grok-4-1-fast-non-reasoning", "name": "Grok 4.1 Fast", "category": "fast", "context": "2M"},
            {"id": "grok-4-fast-non-reasoning", "name": "Grok 4 Fast", "category": "fast", "context": "2M"},
            # Code-optimized model (256K context)
            {"id": "grok-code-fast-1", "name": "Grok Code Fast", "category": "code", "context": "256K"},
            # Premium models
            {"id": "grok-4-0709", "name": "Grok 4 (Premium)", "category": "premium", "context": "256K"},
            {"id": "grok-3", "name": "Grok 3", "category": "premium", "context": "131K"},
            # Budget model
            {"id": "grok-3-mini", "name": "Grok 3 Mini", "category": "budget", "context": "131K"},
            # Vision model
            {"id": "grok-2-vision-1212", "name": "Grok 2 Vision", "category": "vision", "context": "32K"},
            # Google Gemini models
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "category": "gemini", "context": "1M", "provider": "google"},
            {"id": "gemini-2.0-flash-thinking", "name": "Gemini 2.0 Flash Thinking", "category": "gemini-reasoning", "context": "32K", "provider": "google"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "category": "gemini", "context": "2M", "provider": "google"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "category": "gemini", "context": "1M", "provider": "google"},
        ]
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
