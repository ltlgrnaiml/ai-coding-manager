"""Research Paper Database Schema and Management.

Dedicated database for academic papers with specialized schema for research metadata,
citations, and integration with the main RAG system.

Citation: [Engineering-Tools-2025] "PDF Paper Extraction Tool"
          https://github.com/ltlgrnaiml/engineering-tools
          Key insight: Structured academic paper storage with metadata indexing
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

# Research paper database path
WORKSPACE_DIR = Path(os.getenv("AI_DEV_WORKSPACE", ".workspace"))
RESEARCH_DB_PATH = WORKSPACE_DIR / "research_papers.db"

RESEARCH_SCHEMA = """
-- Research papers table with academic metadata
CREATE TABLE IF NOT EXISTS research_papers (
    id TEXT PRIMARY KEY,
    arxiv_id TEXT UNIQUE,
    doi TEXT UNIQUE,
    title TEXT NOT NULL,
    authors TEXT NOT NULL, -- JSON array of authors
    abstract TEXT,
    publication_date TEXT,
    venue TEXT,
    keywords TEXT, -- JSON array of keywords
    source_path TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    page_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    table_count INTEGER DEFAULT 0,
    extraction_date TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Paper sections table for structured content
CREATE TABLE IF NOT EXISTS paper_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    section_name TEXT NOT NULL,
    section_content TEXT NOT NULL,
    section_order INTEGER DEFAULT 0,
    UNIQUE(paper_id, section_name)
);

-- Paper chunks table for RAG integration
CREATE TABLE IF NOT EXISTS paper_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    section_id INTEGER REFERENCES paper_sections(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    chunk_type TEXT DEFAULT 'text', -- text, abstract, conclusion, etc.
    UNIQUE(paper_id, chunk_index)
);

-- Paper embeddings table
CREATE TABLE IF NOT EXISTS paper_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL REFERENCES paper_chunks(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Paper images table with BLOB storage
CREATE TABLE IF NOT EXISTS paper_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    image_index INTEGER NOT NULL,
    width INTEGER DEFAULT 0,
    height INTEGER DEFAULT 0,
    image_path TEXT, -- Legacy path, nullable for BLOB storage
    image_data BLOB, -- Image data stored as BLOB
    mime_type TEXT, -- image/png, image/jpeg, etc.
    file_size INTEGER, -- Size in bytes
    caption TEXT,
    extracted_text TEXT, -- OCR text if available
    is_plot BOOLEAN DEFAULT 0, -- Whether this is a plot/graph/chart
    plot_type TEXT, -- 'chart', 'diagram', 'graph', 'figure'
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, page_number, image_index)
);

-- Paper tables table
CREATE TABLE IF NOT EXISTS paper_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    table_index INTEGER NOT NULL,
    headers TEXT NOT NULL, -- JSON array
    rows TEXT NOT NULL, -- JSON array of arrays
    caption TEXT,
    extracted_data TEXT, -- Structured data if parsed
    UNIQUE(paper_id, page_number, table_index)
);

-- Paper citations and references
CREATE TABLE IF NOT EXISTS paper_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    cited_paper_id TEXT REFERENCES research_papers(id) ON DELETE SET NULL,
    citation_text TEXT,
    citation_context TEXT, -- Surrounding text
    citation_type TEXT DEFAULT 'reference', -- reference, self_citation, etc.
    created_at TEXT DEFAULT (datetime('now'))
);

-- Research categories and tags
CREATE TABLE IF NOT EXISTS paper_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'manual', -- manual, auto_classified, etc.
    UNIQUE(paper_id, category)
);

-- Paper files table for storing PDFs and other files as BLOBs
CREATE TABLE IF NOT EXISTS paper_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    file_type TEXT NOT NULL, -- 'pdf', 'supplementary', 'attachment'
    file_name TEXT NOT NULL,
    file_data BLOB NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0, -- Whether this is the main PDF
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, file_name)
);

-- FTS5 virtual table for research paper search
CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(
    title, abstract, content, authors, keywords, 
    paper_id UNINDEXED, 
    content='', 
    tokenize='porter'
);

-- Triggers for FTS sync
CREATE TRIGGER IF NOT EXISTS research_papers_ai AFTER INSERT ON research_papers BEGIN
    INSERT INTO research_fts(paper_id, title, abstract, authors, keywords) 
    VALUES (new.id, new.title, new.abstract, new.authors, new.keywords);
END;

CREATE TRIGGER IF NOT EXISTS research_papers_ad AFTER DELETE ON research_papers BEGIN
    DELETE FROM research_fts WHERE paper_id = old.id;
END;

CREATE TRIGGER IF NOT EXISTS research_papers_au AFTER UPDATE ON research_papers BEGIN
    DELETE FROM research_fts WHERE paper_id = old.id;
    INSERT INTO research_fts(paper_id, title, abstract, authors, keywords) 
    VALUES (new.id, new.title, new.abstract, new.authors, new.keywords);
END;

-- Updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_research_papers_timestamp 
AFTER UPDATE ON research_papers BEGIN
    UPDATE research_papers SET updated_at = datetime('now') WHERE id = new.id;
END;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_papers_arxiv ON research_papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON research_papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_date ON research_papers(publication_date);
CREATE INDEX IF NOT EXISTS idx_papers_venue ON research_papers(venue);
CREATE INDEX IF NOT EXISTS idx_sections_paper ON paper_sections(paper_id);
CREATE INDEX IF NOT EXISTS idx_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON paper_chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk ON paper_embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_images_paper ON paper_images(paper_id);
CREATE INDEX IF NOT EXISTS idx_tables_paper ON paper_tables(paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON paper_citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON paper_citations(cited_paper_id);
CREATE INDEX IF NOT EXISTS idx_categories_paper ON paper_categories(paper_id);
CREATE INDEX IF NOT EXISTS idx_categories_category ON paper_categories(category);
CREATE INDEX IF NOT EXISTS idx_files_paper ON paper_files(paper_id);
CREATE INDEX IF NOT EXISTS idx_files_type ON paper_files(file_type);
CREATE INDEX IF NOT EXISTS idx_images_plot ON paper_images(is_plot);
CREATE INDEX IF NOT EXISTS idx_images_type ON paper_images(plot_type);
"""


@dataclass
class ResearchPaperRecord:
    """Research paper database record."""
    
    id: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    title: str = ""
    authors: List[str] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = None
    keywords: List[str] = None
    source_path: str = ""
    content_hash: str = ""
    page_count: int = 0
    word_count: int = 0
    image_count: int = 0
    table_count: int = 0
    extraction_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []


def get_research_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get research database connection with row factory.
    
    Args:
        db_path: Optional custom database path.
        
    Returns:
        SQLite connection with Row factory enabled.
    """
    path = db_path or RESEARCH_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_research_database(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize research database with schema.
    
    Args:
        db_path: Optional custom database path.
        
    Returns:
        Initialized database connection.
    """
    conn = get_research_connection(db_path)
    conn.executescript(RESEARCH_SCHEMA)
    conn.commit()
    return conn


def insert_research_paper(
    conn: sqlite3.Connection,
    paper_data: Dict[str, Any]
) -> str:
    """Insert a research paper into the database.
    
    Args:
        conn: Database connection.
        paper_data: Paper data from PDF extraction.
        
    Returns:
        Paper ID.
    """
    # Generate paper ID from content hash
    paper_id = f"paper_{paper_data['content_hash'][:12]}"
    
    # Prepare data
    authors_json = json.dumps(paper_data.get('metadata', {}).get('authors', []))
    keywords_json = json.dumps(paper_data.get('metadata', {}).get('keywords', []))
    
    # Insert main paper record
    conn.execute("""
        INSERT OR REPLACE INTO research_papers (
            id, arxiv_id, doi, title, authors, abstract, publication_date,
            venue, keywords, source_path, content_hash, page_count, word_count,
            image_count, table_count, extraction_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        paper_id,
        paper_data.get('metadata', {}).get('arxiv_id'),
        paper_data.get('metadata', {}).get('doi'),
        paper_data.get('metadata', {}).get('title', 'Untitled'),
        authors_json,
        paper_data.get('metadata', {}).get('abstract'),
        paper_data.get('metadata', {}).get('publication_date'),
        paper_data.get('metadata', {}).get('venue'),
        keywords_json,
        paper_data.get('source_path', ''),
        paper_data.get('content_hash', ''),
        paper_data.get('page_count', 0),
        paper_data.get('word_count', 0),
        len(paper_data.get('images', [])),
        len(paper_data.get('tables', [])),
        paper_data.get('extraction_date')
    ))
    
    # Insert sections
    sections = paper_data.get('sections', {})
    for order, (section_name, content) in enumerate(sections.items()):
        section_id = conn.execute("""
            INSERT OR REPLACE INTO paper_sections (
                paper_id, section_name, section_content, section_order
            ) VALUES (?, ?, ?, ?)
        """, (paper_id, section_name, content, order)).lastrowid
    
    # Insert images
    for img in paper_data.get('images', []):
        conn.execute("""
            INSERT OR REPLACE INTO paper_images (
                paper_id, page_number, image_index, width, height, 
                image_path, caption
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_id, img['page_number'], img['image_index'],
            img['width'], img['height'], img['image_path'], img.get('caption')
        ))
    
    # Insert tables
    for tbl in paper_data.get('tables', []):
        conn.execute("""
            INSERT OR REPLACE INTO paper_tables (
                paper_id, page_number, table_index, headers, rows, caption
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            paper_id, tbl['page_number'], tbl['table_index'],
            json.dumps(tbl['headers']), json.dumps(tbl['rows']), tbl.get('caption')
        ))
    
    conn.commit()
    return paper_id


def search_research_papers(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search research papers using FTS5.
    
    Args:
        conn: Database connection.
        query: Search query.
        limit: Maximum results to return.
        category_filter: Optional category filter.
        
    Returns:
        List of matching papers.
    """
    base_query = """
        SELECT p.*, 
               snippet(research_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
        FROM research_papers p
        JOIN research_fts fts ON p.id = fts.paper_id
        WHERE research_fts MATCH ?
    """
    
    params = [query]
    
    if category_filter:
        base_query += """
            AND p.id IN (
                SELECT paper_id FROM paper_categories 
                WHERE category = ?
            )
        """
        params.append(category_filter)
    
    base_query += " ORDER BY rank LIMIT ?"
    params.append(limit)
    
    cursor = conn.execute(base_query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_paper_by_id(
    conn: sqlite3.Connection,
    paper_id: str
) -> Optional[Dict[str, Any]]:
    """Get a research paper by ID with all related data.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        
    Returns:
        Paper data with sections, images, tables.
    """
    # Get main paper record
    cursor = conn.execute(
        "SELECT * FROM research_papers WHERE id = ?", (paper_id,)
    )
    paper = cursor.fetchone()
    if not paper:
        return None
    
    paper_dict = dict(paper)
    
    # Parse JSON fields
    paper_dict['authors'] = json.loads(paper_dict['authors'] or '[]')
    paper_dict['keywords'] = json.loads(paper_dict['keywords'] or '[]')
    
    # Get sections
    cursor = conn.execute("""
        SELECT section_name, section_content 
        FROM paper_sections 
        WHERE paper_id = ? 
        ORDER BY section_order
    """, (paper_id,))
    paper_dict['sections'] = {row['section_name']: row['section_content'] 
                             for row in cursor.fetchall()}
    
    # Get images
    cursor = conn.execute("""
        SELECT * FROM paper_images WHERE paper_id = ?
        ORDER BY page_number, image_index
    """, (paper_id,))
    paper_dict['images'] = [dict(row) for row in cursor.fetchall()]
    
    # Get tables
    cursor = conn.execute("""
        SELECT * FROM paper_tables WHERE paper_id = ?
        ORDER BY page_number, table_index
    """, (paper_id,))
    tables = []
    for row in cursor.fetchall():
        table_dict = dict(row)
        table_dict['headers'] = json.loads(table_dict['headers'])
        table_dict['rows'] = json.loads(table_dict['rows'])
        tables.append(table_dict)
    paper_dict['tables'] = tables
    
    # Get categories
    cursor = conn.execute("""
        SELECT category, confidence, source 
        FROM paper_categories 
        WHERE paper_id = ?
    """, (paper_id,))
    paper_dict['categories'] = [dict(row) for row in cursor.fetchall()]
    
    return paper_dict


def add_paper_category(
    conn: sqlite3.Connection,
    paper_id: str,
    category: str,
    confidence: float = 1.0,
    source: str = 'manual'
) -> None:
    """Add a category to a research paper.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        category: Category name.
        confidence: Confidence score (0.0-1.0).
        source: Source of categorization.
    """
    conn.execute("""
        INSERT OR REPLACE INTO paper_categories (
            paper_id, category, confidence, source
        ) VALUES (?, ?, ?, ?)
    """, (paper_id, category, confidence, source))
    conn.commit()


def get_papers_by_category(
    conn: sqlite3.Connection,
    category: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get papers by category.
    
    Args:
        conn: Database connection.
        category: Category name.
        limit: Maximum results.
        
    Returns:
        List of papers in category.
    """
    cursor = conn.execute("""
        SELECT p.*, pc.confidence, pc.source as category_source
        FROM research_papers p
        JOIN paper_categories pc ON p.id = pc.paper_id
        WHERE pc.category = ?
        ORDER BY pc.confidence DESC, p.created_at DESC
        LIMIT ?
    """, (category, limit))
    
    return [dict(row) for row in cursor.fetchall()]


def store_paper_file(
    conn: sqlite3.Connection,
    paper_id: str,
    file_path: str,
    file_type: str = "pdf",
    is_primary: bool = True
) -> int:
    """Store a file (PDF, etc.) as BLOB in the database.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        file_path: Path to the file to store.
        file_type: Type of file (pdf, supplementary, etc.).
        is_primary: Whether this is the primary file.
        
    Returns:
        File ID.
    """
    import os
    from pathlib import Path
    import mimetypes
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read file data
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Get file info
    file_size = len(file_data)
    mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
    
    # Insert into database
    cursor = conn.execute("""
        INSERT OR REPLACE INTO paper_files (
            paper_id, file_type, file_name, file_data, file_size, mime_type, is_primary
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (paper_id, file_type, file_path.name, file_data, file_size, mime_type, is_primary))
    
    conn.commit()
    return cursor.lastrowid


def store_paper_image_blob(
    conn: sqlite3.Connection,
    paper_id: str,
    image_path: str,
    page_number: int,
    image_index: int,
    width: int = 0,
    height: int = 0,
    caption: Optional[str] = None,
    is_plot: bool = False,
    plot_type: Optional[str] = None
) -> int:
    """Store an image as BLOB in the database.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        image_path: Path to the image file.
        page_number: Page number where image appears.
        image_index: Index of image on the page.
        width: Image width in pixels.
        height: Image height in pixels.
        caption: Image caption if available.
        is_plot: Whether this is a plot/graph/chart.
        plot_type: Type of plot if is_plot is True.
        
    Returns:
        Image ID.
    """
    import os
    from pathlib import Path
    import mimetypes
    
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Read image data
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Get image info
    file_size = len(image_data)
    mime_type = mimetypes.guess_type(str(image_path))[0] or 'image/jpeg'
    
    # Insert into database
    cursor = conn.execute("""
        INSERT OR REPLACE INTO paper_images (
            paper_id, page_number, image_index, width, height, 
            image_path, image_data, mime_type, file_size, caption, 
            is_plot, plot_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        paper_id, page_number, image_index, width, height,
        str(image_path), image_data, mime_type, file_size, caption,
        is_plot, plot_type
    ))
    
    conn.commit()
    return cursor.lastrowid


def get_paper_file(
    conn: sqlite3.Connection,
    paper_id: str,
    file_type: str = "pdf"
) -> Optional[Dict[str, Any]]:
    """Get a paper file from the database.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        file_type: Type of file to retrieve.
        
    Returns:
        File data dictionary or None if not found.
    """
    cursor = conn.execute("""
        SELECT id, file_name, file_data, file_size, mime_type, is_primary, created_at
        FROM paper_files 
        WHERE paper_id = ? AND file_type = ?
        ORDER BY is_primary DESC, created_at DESC
        LIMIT 1
    """, (paper_id, file_type))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        'id': row['id'],
        'file_name': row['file_name'],
        'file_data': row['file_data'],
        'file_size': row['file_size'],
        'mime_type': row['mime_type'],
        'is_primary': bool(row['is_primary']),
        'created_at': row['created_at']
    }


def get_paper_images(
    conn: sqlite3.Connection,
    paper_id: str,
    include_plots_only: bool = False
) -> List[Dict[str, Any]]:
    """Get all images for a paper.
    
    Args:
        conn: Database connection.
        paper_id: Paper ID.
        include_plots_only: If True, only return plots/graphs.
        
    Returns:
        List of image data dictionaries.
    """
    query = """
        SELECT id, page_number, image_index, width, height, image_data, 
               mime_type, file_size, caption, is_plot, plot_type, created_at
        FROM paper_images 
        WHERE paper_id = ?
    """
    
    params = [paper_id]
    
    if include_plots_only:
        query += " AND is_plot = 1"
    
    query += " ORDER BY page_number, image_index"
    
    cursor = conn.execute(query, params)
    
    images = []
    for row in cursor.fetchall():
        images.append({
            'id': row['id'],
            'page_number': row['page_number'],
            'image_index': row['image_index'],
            'width': row['width'],
            'height': row['height'],
            'image_data': row['image_data'],
            'mime_type': row['mime_type'],
            'file_size': row['file_size'],
            'caption': row['caption'],
            'is_plot': bool(row['is_plot']),
            'plot_type': row['plot_type'],
            'created_at': row['created_at']
        })
    
    return images


def classify_image_as_plot(image_path: str) -> Tuple[bool, Optional[str]]:
    """Classify an image as a plot/graph/chart using simple heuristics.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Tuple of (is_plot, plot_type).
    """
    from pathlib import Path
    
    # Simple heuristics based on filename and context
    filename = Path(image_path).name.lower()
    
    # Keywords that suggest plots/graphs
    plot_keywords = [
        'fig', 'figure', 'chart', 'graph', 'plot', 'diagram',
        'histogram', 'scatter', 'bar', 'line', 'pie', 'box',
        'heatmap', 'network', 'tree', 'flow', 'architecture'
    ]
    
    # Check filename for plot indicators
    for keyword in plot_keywords:
        if keyword in filename:
            if any(x in filename for x in ['arch', 'flow', 'network', 'tree']):
                return True, 'diagram'
            elif any(x in filename for x in ['chart', 'bar', 'pie', 'histogram']):
                return True, 'chart'
            elif any(x in filename for x in ['graph', 'plot', 'scatter', 'line']):
                return True, 'graph'
            else:
                return True, 'figure'
    
    # Default: assume it's not a plot
    return False, None


def get_research_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get research database statistics.
    
    Args:
        conn: Database connection.
        
    Returns:
        Statistics dictionary.
    """
    stats = {}
    
    # Paper counts
    cursor = conn.execute("SELECT COUNT(*) as count FROM research_papers")
    stats['total_papers'] = cursor.fetchone()['count']
    
    # Category distribution
    cursor = conn.execute("""
        SELECT category, COUNT(*) as count 
        FROM paper_categories 
        GROUP BY category 
        ORDER BY count DESC
    """)
    stats['categories'] = [dict(row) for row in cursor.fetchall()]
    
    # Venue distribution
    cursor = conn.execute("""
        SELECT venue, COUNT(*) as count 
        FROM research_papers 
        WHERE venue IS NOT NULL 
        GROUP BY venue 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats['top_venues'] = [dict(row) for row in cursor.fetchall()]
    
    # Recent papers
    cursor = conn.execute("""
        SELECT COUNT(*) as count 
        FROM research_papers 
        WHERE created_at >= date('now', '-30 days')
    """)
    stats['recent_papers'] = cursor.fetchone()['count']
    
    # File storage stats
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_files,
            SUM(file_size) as total_size,
            AVG(file_size) as avg_size
        FROM paper_files
    """)
    file_stats = cursor.fetchone()
    stats['files'] = {
        'total_files': file_stats['total_files'] or 0,
        'total_size_mb': (file_stats['total_size'] or 0) / (1024 * 1024),
        'avg_size_kb': (file_stats['avg_size'] or 0) / 1024
    }
    
    # Image stats
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_images,
            SUM(CASE WHEN is_plot = 1 THEN 1 ELSE 0 END) as plot_count,
            SUM(file_size) as total_image_size
        FROM paper_images
        WHERE image_data IS NOT NULL
    """)
    image_stats = cursor.fetchone()
    stats['images'] = {
        'total_images': image_stats['total_images'] or 0,
        'plot_count': image_stats['plot_count'] or 0,
        'total_size_mb': (image_stats['total_image_size'] or 0) / (1024 * 1024)
    }
    
    return stats
