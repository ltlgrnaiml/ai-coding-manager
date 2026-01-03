"""Research Paper Semantic Search API - FastAPI Endpoint.

Provides:
- Semantic search across papers by meaning
- Concept search and co-occurrence
- Citation graph queries
- Download queue management

Usage:
    uvicorn backend.services.research_api:app --reload --port 8001
"""

from fastapi import FastAPI, APIRouter, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Add scripts to path for organizer import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

try:
    from research_enhanced_organizer import ResearchEnhancedOrganizer
except ImportError:
    ResearchEnhancedOrganizer = None

# GPU-accelerated service
try:
    from backend.services.gpu_service import get_gpu_service, GPUSearchService, init_gpu_tables
    GPU_SERVICE_AVAILABLE = True
    # Initialize GPU tables on import
    init_gpu_tables()
except ImportError:
    GPU_SERVICE_AVAILABLE = False
    get_gpu_service = None


app = FastAPI(
    title="AICM Research API",
    description="Semantic search and knowledge graph API for research papers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router for inclusion in main app (avoids shadowing main routes)
router = APIRouter(tags=["research"])

# Lazy-loaded organizer
_organizer = None

def get_organizer() -> ResearchEnhancedOrganizer:
    global _organizer
    if _organizer is None:
        if ResearchEnhancedOrganizer is None:
            raise HTTPException(500, "Research organizer not available")
        _organizer = ResearchEnhancedOrganizer()
    return _organizer


# === Models ===

class SearchResult(BaseModel):
    paper_id: str
    title: Optional[str]
    abstract: Optional[str]
    similarity: float

class ConceptResult(BaseModel):
    paper_id: str
    title: Optional[str]
    concept: str
    concept_type: str
    frequency: int

class CitationStats(BaseModel):
    total_citations: int
    resolved_citations: int
    most_cited_internal: List[Dict[str, Any]]
    most_cited_external: List[Dict[str, Any]]

class DownloadQueueItem(BaseModel):
    arxiv_id: Optional[str]
    title: str
    citation_count: int
    status: str

class StatsResponse(BaseModel):
    papers: int
    concepts: int
    citations: int
    resolved: int
    queued: int
    downloaded: int


# === Endpoints ===

@app.get("/")
async def root():
    return {"status": "ok", "service": "AICM Research API", "version": "1.0.0"}


@app.get("/search", response_model=List[SearchResult])
async def semantic_search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results")
):
    """Semantic search across all papers by meaning."""
    org = get_organizer()
    results = org.semantic_search(q, top_k=top_k)
    return [SearchResult(**r) for r in results]


@app.get("/concepts/{concept}")
async def find_by_concept(
    concept: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Find papers containing a specific concept."""
    org = get_organizer()
    with org._get_conn() as conn:
        cursor = conn.execute("""
            SELECT p.id as paper_id, p.title, e.concept, e.concept_type, e.frequency
            FROM research_papers p
            JOIN extracted_concepts e ON p.id = e.paper_id
            WHERE e.normalized_concept LIKE ?
            ORDER BY e.frequency DESC LIMIT ?
        """, (f"%{concept.lower()}%", limit))
        return [dict(row) for row in cursor.fetchall()]


@app.get("/concepts")
async def list_concepts(
    type: Optional[str] = Query(None, description="Filter by type: models, techniques, datasets, etc."),
    min_freq: int = Query(2, description="Minimum frequency")
):
    """List all extracted concepts."""
    org = get_organizer()
    with org._get_conn() as conn:
        query = """
            SELECT normalized_concept as concept, concept_type, SUM(frequency) as total_freq
            FROM extracted_concepts
            WHERE 1=1
        """
        params = []
        if type:
            query += " AND concept_type = ?"
            params.append(type)
        query += " GROUP BY normalized_concept HAVING total_freq >= ? ORDER BY total_freq DESC"
        params.append(min_freq)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


@app.get("/cooccurrence/{concept}")
async def concept_cooccurrence(concept: str, limit: int = Query(20)):
    """Find concepts that co-occur with a given concept."""
    org = get_organizer()
    with org._get_conn() as conn:
        cursor = conn.execute("""
            SELECT concept_b as related_concept, cooccurrence_count
            FROM concept_cooccurrence
            WHERE concept_a = ?
            UNION
            SELECT concept_a as related_concept, cooccurrence_count
            FROM concept_cooccurrence
            WHERE concept_b = ?
            ORDER BY cooccurrence_count DESC
            LIMIT ?
        """, (concept.lower(), concept.lower(), limit))
        return [dict(row) for row in cursor.fetchall()]


@app.get("/citations/stats")
async def citation_stats():
    """Get citation statistics."""
    org = get_organizer()
    with org._get_conn() as conn:
        stats = {
            "total_citations": conn.execute("SELECT COUNT(*) FROM paper_citations").fetchone()[0],
            "resolved_citations": conn.execute("SELECT COUNT(*) FROM paper_citations WHERE resolved=1").fetchone()[0],
        }
        
        # Most cited in our DB
        cursor = conn.execute("""
            SELECT p.title, COUNT(c.id) as citation_count
            FROM research_papers p
            JOIN paper_citations c ON p.id = c.cited_paper_id
            GROUP BY p.id ORDER BY citation_count DESC LIMIT 10
        """)
        stats["most_cited_internal"] = [dict(row) for row in cursor.fetchall()]
        
        # Most cited external
        cursor = conn.execute("""
            SELECT cited_arxiv_id, COUNT(*) as citation_count
            FROM paper_citations
            WHERE cited_paper_id IS NULL AND cited_arxiv_id IS NOT NULL
            GROUP BY cited_arxiv_id ORDER BY citation_count DESC LIMIT 10
        """)
        stats["most_cited_external"] = [dict(row) for row in cursor.fetchall()]
    
    return stats


@app.get("/download-queue")
async def get_download_queue(
    status: Optional[str] = Query(None, description="Filter by status: pending, completed, failed")
):
    """Get download queue status."""
    org = get_organizer()
    with org._get_conn() as conn:
        query = "SELECT arxiv_id, title, citation_count, status FROM download_queue"
        if status:
            query += " WHERE status = ?"
            cursor = conn.execute(query + " ORDER BY priority DESC", (status,))
        else:
            cursor = conn.execute(query + " ORDER BY priority DESC")
        return [dict(row) for row in cursor.fetchall()]


@app.post("/download-queue/process")
async def process_downloads(max_downloads: int = Query(5, ge=1, le=20)):
    """Trigger download of queued papers."""
    org = get_organizer()
    downloaded = org.process_download_queue(max_downloads)
    return {"downloaded": downloaded}


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get overall research database statistics."""
    org = get_organizer()
    with org._get_conn() as conn:
        return StatsResponse(
            papers=conn.execute("SELECT COUNT(*) FROM research_papers").fetchone()[0],
            concepts=conn.execute("SELECT COUNT(DISTINCT normalized_concept) FROM extracted_concepts").fetchone()[0],
            citations=conn.execute("SELECT COUNT(*) FROM paper_citations").fetchone()[0],
            resolved=conn.execute("SELECT COUNT(*) FROM paper_citations WHERE resolved=1").fetchone()[0],
            queued=conn.execute("SELECT COUNT(*) FROM download_queue WHERE status='pending'").fetchone()[0],
            downloaded=conn.execute("SELECT COUNT(*) FROM download_queue WHERE status='completed'").fetchone()[0],
        )


@app.get("/graph/papers")
async def get_paper_graph():
    """Get paper similarity graph data for visualization."""
    org = get_organizer()
    with org._get_conn() as conn:
        nodes = [dict(row) for row in conn.execute(
            "SELECT id, title, arxiv_id as arxiv FROM research_papers"
        ).fetchall()]
        
        links = [dict(row) for row in conn.execute("""
            SELECT source_paper_id as source, target_paper_id as target, similarity_score as value
            FROM paper_links WHERE link_type='similar' AND similarity_score > 0.4
        """).fetchall()]
    
    return {"nodes": nodes, "links": links}


@app.get("/graph/concepts")
async def get_concept_graph(min_cooccurrence: int = Query(2)):
    """Get concept co-occurrence graph data for visualization."""
    org = get_organizer()
    with org._get_conn() as conn:
        nodes = [dict(row) for row in conn.execute("""
            SELECT normalized_concept as id, normalized_concept as name, concept_type as type, SUM(frequency) as freq
            FROM extracted_concepts GROUP BY normalized_concept HAVING freq >= 2
        """).fetchall()]
        
        node_ids = {n["id"] for n in nodes}
        
        links = [dict(row) for row in conn.execute("""
            SELECT concept_a as source, concept_b as target, cooccurrence_count as value
            FROM concept_cooccurrence WHERE cooccurrence_count >= ?
        """, (min_cooccurrence,)).fetchall()]
        
        links = [l for l in links if l["source"] in node_ids and l["target"] in node_ids]
    
    return {"nodes": nodes, "links": links}


@app.post("/ingest/scan")
async def scan_for_pdfs(folder: str = Query("research_papers")):
    """Scan folder for new PDFs to ingest."""
    org = get_organizer()
    new_files = org.scan_for_new_pdfs(folder)
    return {"new_files": len(new_files), "files": new_files[:20]}


# =============================================================================
# AIKH (AI Knowledge Hub) Endpoints - Phase 1
# =============================================================================

AIKH_SCHEMA = """
CREATE TABLE IF NOT EXISTS artifact_knowledge_refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_type TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    paper_id TEXT,
    concept TEXT,
    citation_context TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_akr_artifact ON artifact_knowledge_refs(artifact_type, artifact_id);

CREATE TABLE IF NOT EXISTS knowledge_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    user_note TEXT,
    highlight_text TEXT,
    tags TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ka_paper ON knowledge_annotations(paper_id);

CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    method TEXT,
    result_count INTEGER,
    clicked_paper_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

def _init_aikh_schema():
    """Initialize AIKH cross-reference tables."""
    org = get_organizer()
    with org._get_conn() as conn:
        conn.executescript(AIKH_SCHEMA)
        conn.commit()


class EnrichRequest(BaseModel):
    message: str
    max_papers: int = 3
    include_concepts: bool = True


class EnrichResponse(BaseModel):
    papers: List[Dict[str, Any]]
    concepts: List[str]
    related_concepts: List[Dict[str, Any]]


@router.post("/api/aikh/enrich", response_model=EnrichResponse)
async def enrich_context(request: EnrichRequest):
    """Enrich a message with relevant papers and concepts for AI context."""
    org = get_organizer()
    
    # Semantic search for relevant papers
    papers = org.semantic_search(request.message, top_k=request.max_papers)
    
    # Extract concepts from message
    message_lower = request.message.lower()
    found_concepts = []
    related = []
    
    if request.include_concepts:
        with org._get_conn() as conn:
            # Find matching concepts
            cursor = conn.execute("""
                SELECT DISTINCT normalized_concept, concept_type, SUM(frequency) as freq
                FROM extracted_concepts
                GROUP BY normalized_concept
                HAVING freq >= 2
            """)
            for row in cursor.fetchall():
                if row["normalized_concept"] and row["normalized_concept"] in message_lower:
                    found_concepts.append(row["normalized_concept"])
            
            # Get related concepts via co-occurrence
            if found_concepts:
                placeholders = ",".join("?" * len(found_concepts))
                cursor = conn.execute(f"""
                    SELECT concept_b as concept, cooccurrence_count as strength
                    FROM concept_cooccurrence
                    WHERE concept_a IN ({placeholders})
                    UNION
                    SELECT concept_a as concept, cooccurrence_count as strength
                    FROM concept_cooccurrence
                    WHERE concept_b IN ({placeholders})
                    ORDER BY strength DESC LIMIT 10
                """, found_concepts + found_concepts)
                related = [dict(row) for row in cursor.fetchall()]
    
    return EnrichResponse(
        papers=papers,
        concepts=found_concepts,
        related_concepts=related
    )


class AutocompleteResult(BaseModel):
    value: str
    type: str
    display: str
    metadata: Optional[Dict[str, Any]] = None


@router.get("/api/aikh/autocomplete", response_model=List[AutocompleteResult])
async def autocomplete(
    prefix: str = Query(..., min_length=2, description="Search prefix"),
    type: Optional[str] = Query(None, description="Filter: paper, concept, author"),
    limit: int = Query(10, ge=1, le=50)
):
    """Fast autocomplete for papers, concepts, and authors."""
    org = get_organizer()
    results = []
    prefix_lower = prefix.lower()
    
    with org._get_conn() as conn:
        # Search papers by title
        if type is None or type == "paper":
            cursor = conn.execute("""
                SELECT id, title, arxiv_id FROM research_papers
                WHERE LOWER(title) LIKE ? LIMIT ?
            """, (f"%{prefix_lower}%", limit))
            for row in cursor.fetchall():
                results.append(AutocompleteResult(
                    value=row["id"],
                    type="paper",
                    display=row["title"][:60] + ("..." if len(row["title"] or "") > 60 else ""),
                    metadata={"arxiv_id": row["arxiv_id"]}
                ))
        
        # Search concepts
        if type is None or type == "concept":
            cursor = conn.execute("""
                SELECT normalized_concept, concept_type, SUM(frequency) as freq
                FROM extracted_concepts
                WHERE normalized_concept LIKE ?
                GROUP BY normalized_concept
                ORDER BY freq DESC LIMIT ?
            """, (f"%{prefix_lower}%", limit))
            for row in cursor.fetchall():
                results.append(AutocompleteResult(
                    value=row["normalized_concept"],
                    type="concept",
                    display=f"{row['normalized_concept']} ({row['concept_type']})",
                    metadata={"frequency": row["freq"], "concept_type": row["concept_type"]}
                ))
        
        # Search authors (from paper metadata)
        if type is None or type == "author":
            cursor = conn.execute("""
                SELECT DISTINCT authors FROM research_papers
                WHERE LOWER(authors) LIKE ? LIMIT ?
            """, (f"%{prefix_lower}%", limit))
            for row in cursor.fetchall():
                if row["authors"]:
                    results.append(AutocompleteResult(
                        value=row["authors"],
                        type="author",
                        display=row["authors"][:60] + ("..." if len(row["authors"]) > 60 else ""),
                        metadata=None
                    ))
    
    return results[:limit]


@router.get("/api/aikh/papers/{paper_id}/bibtex")
async def get_bibtex(paper_id: str):
    """Generate BibTeX citation for a paper."""
    org = get_organizer()
    with org._get_conn() as conn:
        row = conn.execute("""
            SELECT id, title, authors, arxiv_id, doi, publication_date, venue, abstract
            FROM research_papers WHERE id = ?
        """, (paper_id,)).fetchone()
        
        if not row:
            raise HTTPException(404, "Paper not found")
        
        # Generate citation key
        first_author = (row["authors"] or "Unknown").split(",")[0].split()[-1].lower()
        year = (row["publication_date"] or "2025")[:4]
        title_word = (row["title"] or "paper").split()[0].lower()
        cite_key = f"{first_author}{year}{title_word}"
        
        # Build BibTeX
        bibtex_lines = [f"@article{{{cite_key},"]
        bibtex_lines.append(f'  title = {{{row["title"] or "Unknown Title"}}},')
        bibtex_lines.append(f'  author = {{{row["authors"] or "Unknown Author"}}},')
        bibtex_lines.append(f'  year = {{{year}}},')
        
        if row["arxiv_id"]:
            bibtex_lines.append(f'  eprint = {{{row["arxiv_id"]}}},')
            bibtex_lines.append('  archivePrefix = {arXiv},')
        if row["doi"]:
            bibtex_lines.append(f'  doi = {{{row["doi"]}}},')
        if row["venue"]:
            bibtex_lines.append(f'  journal = {{{row["venue"]}}},')
        if row["abstract"]:
            abstract_short = row["abstract"][:300].replace("{", "").replace("}", "")
            bibtex_lines.append(f'  abstract = {{{abstract_short}...}},')
        
        bibtex_lines.append("}")
        
        return {
            "bibtex": "\n".join(bibtex_lines),
            "cite_key": cite_key,
            "paper_id": paper_id
        }


@router.post("/api/aikh/refs/create")
async def create_reference(
    artifact_type: str = Query(..., description="disc, adr, spec, plan"),
    artifact_id: str = Query(..., description="e.g., DISC-0022"),
    paper_id: Optional[str] = None,
    concept: Optional[str] = None,
    context: Optional[str] = None
):
    """Create a cross-reference between an artifact and knowledge."""
    org = get_organizer()
    _init_aikh_schema()
    
    with org._get_conn() as conn:
        conn.execute("""
            INSERT INTO artifact_knowledge_refs (artifact_type, artifact_id, paper_id, concept, citation_context)
            VALUES (?, ?, ?, ?, ?)
        """, (artifact_type, artifact_id, paper_id, concept, context))
        conn.commit()
    
    return {"status": "created", "artifact": f"{artifact_type}:{artifact_id}"}


@router.get("/api/aikh/refs/artifact/{artifact_type}/{artifact_id}")
async def get_artifact_refs(artifact_type: str, artifact_id: str):
    """Get all knowledge references for an artifact."""
    org = get_organizer()
    _init_aikh_schema()
    
    with org._get_conn() as conn:
        cursor = conn.execute("""
            SELECT r.*, p.title as paper_title
            FROM artifact_knowledge_refs r
            LEFT JOIN research_papers p ON r.paper_id = p.id
            WHERE r.artifact_type = ? AND r.artifact_id = ?
        """, (artifact_type, artifact_id))
        return [dict(row) for row in cursor.fetchall()]


@app.on_event("startup")
async def startup_event():
    """Initialize AIKH schema on startup."""
    try:
        _init_aikh_schema()
    except Exception:
        pass  # Schema may already exist or DB not ready


# =============================================================================
# GPU-Accelerated Endpoints
# =============================================================================

class GPUSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    search_type: str = "hybrid"  # paper, chunk, hybrid
    min_similarity: float = 0.3


class GPUSearchResult(BaseModel):
    paper_id: str
    title: Optional[str]
    abstract: Optional[str]
    similarity: float
    chunk_id: Optional[int] = None
    chunk_content: Optional[str] = None


@router.post("/api/gpu/search", response_model=List[GPUSearchResult])
async def gpu_search(request: GPUSearchRequest):
    """GPU-accelerated semantic search.
    
    Uses RTX 5090 for high-throughput embedding comparison.
    Supports paper-level, chunk-level, or hybrid search.
    """
    if not GPU_SERVICE_AVAILABLE:
        raise HTTPException(503, "GPU service not available")
    
    gpu = get_gpu_service()
    
    if request.search_type == "paper":
        results = gpu.semantic_search_papers(
            request.query, 
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
    elif request.search_type == "chunk":
        results = gpu.semantic_search_chunks(
            request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
    else:  # hybrid
        results = gpu.hybrid_search(
            request.query,
            top_k=request.top_k
        )
    
    return [
        GPUSearchResult(
            paper_id=r.paper_id,
            title=r.title,
            abstract=r.abstract,
            similarity=r.similarity,
            chunk_id=r.chunk_id,
            chunk_content=r.chunk_content
        )
        for r in results
    ]


@router.get("/api/gpu/stats")
async def gpu_stats():
    """Get GPU and embedding statistics."""
    if not GPU_SERVICE_AVAILABLE:
        return {
            "gpu_available": False,
            "message": "GPU service not available"
        }
    
    gpu = get_gpu_service()
    return gpu.get_gpu_stats()


@router.post("/api/gpu/embed-paper/{paper_id}")
async def embed_paper(paper_id: str):
    """Generate GPU embedding for a specific paper.
    
    Call after ingesting a new paper to enable GPU search.
    """
    if not GPU_SERVICE_AVAILABLE:
        raise HTTPException(503, "GPU service not available")
    
    gpu = get_gpu_service()
    success = gpu.embed_new_paper(paper_id)
    
    if success:
        return {"status": "embedded", "paper_id": paper_id}
    else:
        raise HTTPException(404, "Paper not found or could not be embedded")


@router.post("/api/gpu/batch-embed")
async def trigger_batch_embed(
    papers_only: bool = Query(False),
    chunks_only: bool = Query(False)
):
    """Trigger GPU batch embedding for all papers/chunks.
    
    Runs the gpu_batch_embedder in background.
    """
    import subprocess
    
    cmd = [sys.executable, "scripts/gpu_batch_embedder.py"]
    if papers_only:
        cmd.append("--papers-only")
    elif chunks_only:
        cmd.append("--chunks-only")
    
    # Run in background
    subprocess.Popen(cmd, cwd=Path(__file__).parent.parent.parent)
    
    return {
        "status": "started",
        "command": " ".join(cmd),
        "message": "Batch embedding started in background"
    }


# Override the enrich endpoint to use GPU when available
@router.post("/api/aikh/enrich/gpu", response_model=EnrichResponse)
async def enrich_context_gpu(request: EnrichRequest):
    """GPU-accelerated context enrichment.
    
    Uses GPU embeddings for faster, more accurate paper matching.
    """
    if GPU_SERVICE_AVAILABLE:
        gpu = get_gpu_service()
        
        # Use GPU search for papers
        gpu_results = gpu.hybrid_search(request.message, top_k=request.max_papers)
        papers = [
            {
                "paper_id": r.paper_id,
                "title": r.title,
                "abstract": r.abstract,
                "similarity": r.similarity
            }
            for r in gpu_results
        ]
    else:
        # Fallback to CPU search
        org = get_organizer()
        papers = org.semantic_search(request.message, top_k=request.max_papers)
    
    # Extract concepts from message
    message_lower = request.message.lower()
    found_concepts = []
    related = []
    
    if request.include_concepts:
        org = get_organizer()
        with org._get_conn() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT normalized_concept, concept_type, SUM(frequency) as freq
                FROM extracted_concepts
                GROUP BY normalized_concept
                HAVING freq >= 2
            """)
            for row in cursor.fetchall():
                if row["normalized_concept"] and row["normalized_concept"] in message_lower:
                    found_concepts.append(row["normalized_concept"])
            
            if found_concepts:
                placeholders = ",".join("?" * len(found_concepts))
                cursor = conn.execute(f"""
                    SELECT concept_b as concept, cooccurrence_count as strength
                    FROM concept_cooccurrence
                    WHERE concept_a IN ({placeholders})
                    UNION
                    SELECT concept_a as concept, cooccurrence_count as strength
                    FROM concept_cooccurrence
                    WHERE concept_b IN ({placeholders})
                    ORDER BY strength DESC LIMIT 10
                """, found_concepts + found_concepts)
                related = [dict(row) for row in cursor.fetchall()]
    
    return EnrichResponse(
        papers=papers,
        concepts=found_concepts,
        related_concepts=related
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
