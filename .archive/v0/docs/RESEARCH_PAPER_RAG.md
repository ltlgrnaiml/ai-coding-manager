# Research Paper RAG System

A dedicated database and RAG system for academic papers with semantic search, metadata extraction, and integration with the main knowledge system.

## Overview

The Research Paper RAG system provides:

- **Dedicated Database**: Separate SQLite database optimized for academic papers
- **PDF Extraction**: Automated text, image, and table extraction from PDFs
- **Semantic Search**: Vector embeddings for similarity-based retrieval
- **Full-Text Search**: FTS5-powered text search with snippets
- **Hybrid Search**: Combined semantic and full-text with RRF ranking
- **RAG Integration**: Context-aware retrieval for LLM prompts
- **API Endpoints**: RESTful API for frontend integration

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   PDF Documents     │───▶│  Extraction Pipeline │───▶│  Research Database  │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           │
                                      ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Text Chunks       │◀───│  Chunking Service    │    │   Embedding Store   │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                      │                           │
                                      ▼                           ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Search Results    │◀───│   RAG Service        │◀───│   Vector Search     │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## Database Schema

### Core Tables

- **`research_papers`**: Paper metadata (title, authors, abstract, DOI, arXiv ID)
- **`paper_sections`**: Structured sections (introduction, methods, results, etc.)
- **`paper_chunks`**: Text chunks for embedding generation
- **`paper_embeddings`**: Vector embeddings for semantic search
- **`paper_images`**: Extracted images with metadata
- **`paper_tables`**: Extracted tables with structured data
- **`paper_categories`**: Paper categorization and tagging
- **`paper_citations`**: Citation relationships between papers

### Search Infrastructure

- **`research_fts`**: FTS5 virtual table for full-text search
- **Indexes**: Optimized for arXiv ID, DOI, categories, and dates

## Usage

### CLI Interface

```bash
# Ingest a single paper
python scripts/research_paper_cli.py ingest paper.pdf --category "machine-learning"

# Ingest multiple papers
python scripts/research_paper_cli.py ingest *.pdf --category "nlp"

# Search papers
python scripts/research_paper_cli.py search "transformer architecture" --method hybrid

# Show paper details
python scripts/research_paper_cli.py show paper_abc123def456

# List papers by category
python scripts/research_paper_cli.py list --category "machine-learning"

# Show statistics
python scripts/research_paper_cli.py stats
```

### API Endpoints

#### Search Papers
```http
GET /api/research/search?query=transformer&method=hybrid&limit=10&category=nlp
```

#### Get Paper Details
```http
GET /api/research/papers/{paper_id}?query=attention+mechanism
```

#### Get RAG Context
```http
GET /api/research/papers/{paper_id}/context?query=attention&max_chunks=3
```

#### List Categories
```http
GET /api/research/categories
```

#### Get Papers by Category
```http
GET /api/research/categories/machine-learning/papers?limit=20
```

#### Database Statistics
```http
GET /api/research/stats
```

#### Ingest Paper
```http
POST /api/research/ingest
Content-Type: application/json

{
  "pdf_path": "/path/to/paper.pdf",
  "category": "machine-learning"
}
```

### Python API

```python
from ai_dev_orchestrator.knowledge.research_rag import ResearchRAGService
from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion

# Initialize services
rag_service = ResearchRAGService()
ingestion = ResearchPaperIngestion()

# Ingest a paper
paper_id, result = ingestion.ingest_pdf("paper.pdf", category="ml")

# Search papers
results = rag_service.search_papers_hybrid("attention mechanism", limit=5)

# Get paper context for RAG
context = rag_service.get_paper_context(paper_id, "transformer architecture")
```

## Search Methods

### 1. Semantic Search
- Uses vector embeddings for similarity matching
- Best for conceptual queries and related work discovery
- Requires embedding generation (slower ingestion)

### 2. Full-Text Search
- Uses FTS5 for fast keyword matching
- Best for exact term searches and author names
- Provides highlighted snippets

### 3. Hybrid Search (Recommended)
- Combines semantic and full-text using Reciprocal Rank Fusion (RRF)
- Balances precision and recall
- Configurable weighting between methods

## RAG Integration

### Context Building
The system provides optimized context for LLM prompts:

```json
{
  "paper_id": "paper_abc123",
  "title": "Attention Is All You Need",
  "authors": ["Vaswani", "Shazeer", "..."],
  "abstract": "The dominant sequence transduction models...",
  "relevant_content": [
    {
      "content": "The Transformer model architecture...",
      "type": "introduction",
      "relevance": 0.92
    }
  ],
  "metadata": {
    "arxiv_id": "1706.03762",
    "venue": "NIPS 2017",
    "categories": ["attention-mechanisms", "transformers"]
  }
}
```

### Integration with Main RAG System
- Separate database prevents contamination of general knowledge
- Unified search interface across both systems
- Cross-referencing between papers and project documents

## Categories and Organization

### Automatic Categorization
Papers can be automatically categorized based on:
- Keywords extraction from abstract and content
- Venue and journal classification
- Citation analysis

### Manual Categorization
- CLI and API support for manual category assignment
- Confidence scoring for category assignments
- Multiple categories per paper

### Suggested Categories
- `machine-learning`
- `natural-language-processing`
- `computer-vision`
- `reinforcement-learning`
- `agentic-workflows`
- `attention-mechanisms`
- `transformers`
- `retrieval-augmented-generation`

## Performance Considerations

### Ingestion
- PDF extraction: ~2-5 seconds per paper
- Chunking: ~1 second per paper
- Embedding generation: ~10-30 seconds per paper (depends on model)
- Database insertion: ~1 second per paper

### Search
- Full-text search: ~10-50ms
- Semantic search: ~100-500ms (depends on corpus size)
- Hybrid search: ~200-800ms

### Storage
- Database size: ~1-5MB per paper (without embeddings)
- Embeddings: ~500KB-2MB per paper (depends on model dimensions)
- Extracted assets: Variable (images, tables)

## Configuration

### Environment Variables
```bash
AI_DEV_WORKSPACE=.workspace          # Workspace directory
KNOWLEDGE_EMBEDDING_MODE=local       # Embedding mode (local/api)
```

### Chunking Parameters
- Default chunk size: 1000 tokens
- Default overlap: 200 tokens
- Sentence-aware chunking for better semantic boundaries

### Embedding Models
- Primary: `all-mpnet-base-v2` (768 dimensions)
- Fallback: `all-MiniLM-L6-v2` (384 dimensions)
- Auto-fallback on memory constraints

## Monitoring and Maintenance

### Statistics Tracking
- Paper ingestion rates and success/failure counts
- Search query patterns and performance metrics
- Database size and growth trends
- Category distribution and balance

### Health Checks
```bash
# Check database status
python scripts/research_paper_cli.py stats

# Verify embeddings
python -c "from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion; print(ResearchPaperIngestion().get_ingestion_stats())"
```

### Backup and Recovery
- SQLite database: Standard backup procedures
- Extracted assets: File system backup
- Embeddings: Can be regenerated from text content

## Future Enhancements

### Planned Features
- Citation network analysis and visualization
- Author disambiguation and tracking
- Automatic paper recommendations
- Integration with reference managers (Zotero, Mendeley)
- Multi-language support
- OCR for scanned papers

### Scalability
- PostgreSQL backend for larger deployments
- Distributed embedding generation
- Caching layer for frequent queries
- Batch processing optimizations

## Troubleshooting

### Common Issues

#### PDF Extraction Fails
- Check PDF is not password-protected
- Verify PyMuPDF and pdfplumber installations
- Try with different PDF versions

#### Embedding Generation Slow
- Check available memory
- Consider using smaller embedding model
- Enable batch processing for multiple papers

#### Search Returns No Results
- Verify papers are properly ingested
- Check category filters
- Try different search methods

#### Database Corruption
- Check disk space and permissions
- Verify SQLite integrity: `PRAGMA integrity_check`
- Restore from backup if necessary

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/research_paper_cli.py search "query" --method hybrid
```

## Contributing

### Adding New Features
1. Follow existing code patterns and documentation
2. Add comprehensive tests
3. Update API documentation
4. Consider backward compatibility

### Code Organization
- `research_database.py`: Database schema and operations
- `research_ingestion.py`: PDF processing and ingestion pipeline
- `research_rag.py`: Search and retrieval services
- `research_service.py`: API service layer
- `research_paper_cli.py`: Command-line interface
