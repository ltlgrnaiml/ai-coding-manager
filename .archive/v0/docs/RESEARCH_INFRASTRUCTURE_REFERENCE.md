# PRIMARY REFERENCE: Research Infrastructure

> **Status**: Active | **Type**: Primary Reference | **SESSION_009**

This document serves as the **PRIMARY REFERENCE** for all research-related tooling in AICM. All AI sessions should consult this document when working with research papers.

---

## Overview

The AICM Research Infrastructure provides a complete pipeline for:

1. **PDF Extraction** → Structured text, images, tables from academic papers
2. **Research Database** → Dedicated SQLite storage with academic metadata
3. **RAG Integration** → Vector embeddings + FTS5 hybrid search
4. **API Access** → CLI and REST endpoints for all operations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AICM Research Infrastructure                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PDF Files          Extraction           Database           Search         │
│   ──────────        ───────────          ─────────          ───────         │
│                                                                              │
│   paper.pdf    ───▶  extract_pdf    ───▶  research    ───▶  hybrid    ───▶  │
│                      _papers.py          _database.py       search          │
│                           │                   │                │            │
│                           ▼                   ▼                ▼            │
│                      - Full text         - Metadata       - FTS5           │
│                      - Sections          - Sections       - Vector         │
│                      - Images            - Chunks         - RRF rank       │
│                      - Tables            - Embeddings                       │
│                      - Metadata          - Categories                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Reference

### 1. PDF Extraction Tool

**Location**: `scripts/extract_pdf_papers.py`

**Purpose**: Extract structured content from academic PDFs

**Key Features**:

- PyMuPDF (fitz) for text and image extraction
- pdfplumber for table extraction
- Automatic metadata parsing (arXiv ID, DOI, abstract, keywords)
- Section detection with academic paper patterns
- Content hashing for deduplication

**Usage**:

```bash
# Single file extraction
python scripts/extract_pdf_papers.py paper.pdf [output_dir]

# Batch processing with category
python scripts/extract_pdf_papers.py --batch <category> paper1.pdf paper2.pdf ...
```

**Output Structure**:

```
extracted_papers/<category>/
├── paper_name_hash/           # Asset directory
│   ├── page1_img1.png         # Extracted images
│   └── ...
├── paper_name_extraction.json # Full structured data
├── paper_name_fulltext.txt    # Plain text content
└── paper_name_summary.md      # Markdown summary
```

**Data Classes**:

- `ExtractedPaper` - Complete extraction result
- `PaperMetadata` - Title, authors, abstract, DOI, arXiv ID, keywords
- `ExtractedImage` - Image with page number, dimensions, path
- `ExtractedTable` - Table with headers, rows, caption

---

### 2. Research Database

**Location**: `src/ai_dev_orchestrator/knowledge/research_database.py`

**Purpose**: Persistent storage for research papers with academic metadata

**Database Path**: `.workspace/research_papers.db`

**Core Tables**:

| Table | Purpose |
|-------|---------|
| `research_papers` | Paper metadata (title, authors, abstract, DOI, arXiv) |
| `paper_sections` | Structured sections (introduction, methods, etc.) |
| `paper_chunks` | Text chunks for embedding generation |
| `paper_embeddings` | Vector embeddings for semantic search |
| `paper_images` | Extracted images with BLOB storage |
| `paper_tables` | Extracted tables with structured data |
| `paper_categories` | Paper categorization and tagging |
| `paper_citations` | Citation relationships between papers |
| `paper_files` | PDF storage as BLOB (optional) |
| `research_fts` | FTS5 virtual table for full-text search |

**Key Functions**:

```python
from ai_dev_orchestrator.knowledge.research_database import (
    init_research_database,      # Initialize database with schema
    insert_research_paper,       # Insert paper from extraction JSON
    search_research_papers,      # FTS5 search with snippets
    get_paper_by_id,             # Get paper with all related data
    add_paper_category,          # Categorize a paper
    get_papers_by_category,      # List papers in category
    store_paper_file,            # Store PDF as BLOB
    store_paper_image_blob,      # Store image as BLOB
    get_research_stats,          # Database statistics
)
```

---

### 3. Research Ingestion Pipeline

**Location**: `src/ai_dev_orchestrator/knowledge/research_ingestion.py`

**Purpose**: End-to-end pipeline from PDF to searchable database

**Features**:

- Automatic chunking with configurable size and overlap
- Embedding generation (all-mpnet-base-v2 or fallback)
- Category assignment (manual or auto-classified)
- Duplicate detection via content hash

**Usage**:

```python
from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion

ingestion = ResearchPaperIngestion()

# Ingest single paper
paper_id, result = ingestion.ingest_pdf("paper.pdf", category="machine-learning")

# Get ingestion statistics
stats = ingestion.get_ingestion_stats()
```

---

### 4. Research RAG Service

**Location**: `src/ai_dev_orchestrator/knowledge/research_rag.py`

**Purpose**: Search and retrieval for LLM context building

**Search Methods**:

| Method | Use Case | Speed |
|--------|----------|-------|
| `semantic` | Conceptual similarity | Slower |
| `fulltext` | Exact keyword matching | Fast |
| `hybrid` | Combined with RRF ranking | Recommended |

**Usage**:

```python
from ai_dev_orchestrator.knowledge.research_rag import ResearchRAGService

rag = ResearchRAGService()

# Hybrid search (recommended)
results = rag.search_papers_hybrid("transformer attention mechanism", limit=5)

# Get context for RAG prompt
context = rag.get_paper_context(paper_id, "specific query", max_chunks=3)
```

---

### 5. Auto-Sync Tool

**Location**: `scripts/research_paper_sync.py`

**Purpose**: Monitor source folders and auto-ingest new PDFs

**Commands**:

```bash
# Check what needs syncing
python scripts/research_paper_sync.py status ~/papers

# One-shot sync (ingest all new papers)
python scripts/research_paper_sync.py sync ~/papers --category "ai-research"

# Dry run (show what would be done)
python scripts/research_paper_sync.py sync ~/papers --dry-run

# Watch mode (continuous monitoring - requires watchdog)
python scripts/research_paper_sync.py watch ~/papers --category "ai-research"
```

**Features**:

- Tracks processed files via state file (`.workspace/paper_sync_state.json`)
- Deduplication by file hash and content hash
- Watch mode with debouncing for large file copies
- Polling fallback if watchdog not installed

---

### 6. CLI Interface

**Location**: `scripts/research_paper_cli.py`

**Commands**:

```bash
# Ingest papers
python scripts/research_paper_cli.py ingest paper.pdf --category "ml"
python scripts/research_paper_cli.py ingest *.pdf --category "nlp"

# Search papers
python scripts/research_paper_cli.py search "attention mechanism" --method hybrid

# Show paper details
python scripts/research_paper_cli.py show paper_abc123def456

# List by category
python scripts/research_paper_cli.py list --category "machine-learning"

# Database statistics
python scripts/research_paper_cli.py stats
```

---

### 7. API Endpoints

**Location**: `backend/services/research_service.py`

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/research/search` | GET | Search papers |
| `/api/research/papers/{id}` | GET | Get paper details |
| `/api/research/papers/{id}/context` | GET | Get RAG context |
| `/api/research/categories` | GET | List categories |
| `/api/research/categories/{name}/papers` | GET | Papers by category |
| `/api/research/stats` | GET | Database statistics |
| `/api/research/ingest` | POST | Ingest new paper |

---

## Current State

### Extracted Papers (~24 papers)

**Location**: `extracted_papers/research/`

**Categories Present** (based on content analysis):

- Agentic AI / Agent Systems
- RAG / Retrieval Systems
- Multimodal Learning
- Graph Neural Networks
- LLM Reasoning

### Database Status

- Research database: `.workspace/research_papers.db`
- FTS5 indexes: Active
- Embeddings: Partial (depends on ingestion)

---

## Workflow for Adding Research

### Step 1: Acquire PDFs

Use research prompts from `.research_prompts/` to search:

- arXiv
- Semantic Scholar
- Google Scholar
- ACL Anthology
- Conference proceedings

### Step 2: Extract

```bash
# Single paper
python scripts/extract_pdf_papers.py ~/Downloads/paper.pdf extracted_papers/research

# Batch by category
python scripts/extract_pdf_papers.py --batch agentic-systems paper1.pdf paper2.pdf
```

### Step 3: Ingest to Database

```bash
python scripts/research_paper_cli.py ingest extracted_papers/research/paper_extraction.json --category "agentic-systems"
```

### Step 4: Verify

```bash
python scripts/research_paper_cli.py stats
python scripts/research_paper_cli.py search "your topic" --method hybrid
```

---

## Dependencies

**Required Python Packages**:

```
PyMuPDF (fitz)      # PDF text/image extraction
pdfplumber          # PDF table extraction
sentence-transformers  # Embedding generation
sqlite3             # Database (stdlib)
```

**Optional**:

```
sqlite-vec          # Vector similarity search extension
```

---

## Configuration

**Environment Variables**:

```bash
AI_DEV_WORKSPACE=.workspace          # Workspace directory
KNOWLEDGE_EMBEDDING_MODE=local       # Embedding mode (local/api)
```

**Chunking Parameters** (in ingestion service):

- Chunk size: 1000 tokens (default)
- Overlap: 200 tokens (default)
- Sentence-aware boundaries

**Embedding Models**:

- Primary: `all-mpnet-base-v2` (768 dim)
- Fallback: `all-MiniLM-L6-v2` (384 dim)

---

## Related Documentation

- `docs/RESEARCH_PAPER_RAG.md` - Detailed RAG system documentation
- `.discussions/DISC-006_Knowledge-Archive-RAG-System.md` - Original design
- `.discussions/DISC-015_AI-Native-Documentation-Architecture.md` - Chunking research

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial PRIMARY REFERENCE creation |
