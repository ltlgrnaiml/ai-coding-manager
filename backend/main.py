"""AI Dev Orchestrator - FastAPI Backend.

Provides:
- Workflow artifact management (discussions, ADRs, plans)
- AI streaming chat with xAI/Grok
- Knowledge base search
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.devtools_service import router as devtools_router

# Initialize FastAPI
app = FastAPI(
    title="AI Dev Orchestrator",
    description="Workflow management + AI streaming chat",
    version="2025.12.01",
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
) -> AsyncGenerator[str, None]:
    """Stream chat response from xAI API."""
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
        # Convert to OpenAI format
        oai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        # Stream response
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
                yield f"data: {json.dumps({'content': content})}\n\n"
        
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
            {"id": "grok-4-1-fast-reasoning", "name": "Grok 4.1 Fast (Reasoning)", "category": "fast"},
            {"id": "grok-4-fast-reasoning", "name": "Grok 4 Fast (Reasoning)", "category": "fast"},
            {"id": "grok-4-1-fast-non-reasoning", "name": "Grok 4.1 Fast", "category": "fast"},
            {"id": "grok-3-fast", "name": "Grok 3 Fast", "category": "budget"},
            {"id": "grok-3-mini-fast", "name": "Grok 3 Mini Fast", "category": "budget"},
            {"id": "grok-vision-beta", "name": "Grok Vision Beta", "category": "vision"},
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
