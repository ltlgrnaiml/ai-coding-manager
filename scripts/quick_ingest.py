#!/usr/bin/env python3
"""Minimal paper ingestion script - bypasses complex dependencies."""

import sys
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
def _get_aikh_db() -> Path:
    if aikh_home := os.getenv("AIKH_HOME"):
        return Path(aikh_home) / "research.db"
    return Path.home() / ".aikh" / "research.db"
DB_PATH = _get_aikh_db()

def get_content_hash(text: str) -> str:
    """Generate content hash for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def init_db():
    """Connect to existing database."""
    conn = sqlite3.connect(str(DB_PATH))
    return conn

def extract_paper_simple(pdf_path: str):
    """Simple PDF extraction using extract_pdf_papers."""
    from extract_pdf_papers import extract_paper, paper_to_dict
    output_dir = str(Path(".workspace/research_papers/extracted"))
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paper = extract_paper(pdf_path, output_dir=output_dir)
    return paper_to_dict(paper)

def ingest_one(conn: sqlite3.Connection, pdf_path: str, category: str = None):
    """Ingest a single PDF using existing schema."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return None, {"status": "error", "error": f"File not found: {pdf_path}"}
    
    print(f"  Extracting: {pdf_path.name}...", end=" ", flush=True)
    
    try:
        paper_dict = extract_paper_simple(str(pdf_path))
    except Exception as e:
        print(f"EXTRACT FAILED: {e}")
        return None, {"status": "error", "error": str(e)}
    
    # Generate IDs - use full_text, fallback to preview
    full_text = paper_dict.get("full_text", "") or paper_dict.get("full_text_preview", "")
    content_hash = get_content_hash(full_text)
    paper_id = f"paper_{content_hash}"
    
    # Check if already exists
    cursor = conn.execute("SELECT id FROM research_papers WHERE content_hash = ?", (content_hash,))
    if cursor.fetchone():
        print("SKIPPED (duplicate)")
        return paper_id, {"status": "skipped", "reason": "duplicate"}
    
    # Get metadata
    metadata = paper_dict.get("metadata", {})
    title = metadata.get("title", pdf_path.stem)
    authors = ", ".join(metadata.get("authors", []))
    abstract = metadata.get("abstract", "")
    arxiv_id = metadata.get("arxiv_id", "")
    doi = metadata.get("doi", "")
    keywords = ", ".join(metadata.get("keywords", []))
    
    # Insert paper (matching existing schema)
    try:
        conn.execute("""
            INSERT INTO research_papers 
            (id, title, authors, abstract, arxiv_id, doi, keywords, source_path, 
             page_count, word_count, image_count, table_count, content_hash,
             extraction_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
        """, (
            paper_id, title, authors, abstract, arxiv_id, doi, keywords,
            str(pdf_path), paper_dict.get("page_count", 0), paper_dict.get("word_count", 0),
            paper_dict.get("image_count", 0), paper_dict.get("table_count", 0), content_hash
        ))
        
        if category:
            conn.execute("INSERT OR IGNORE INTO paper_categories (paper_id, category) VALUES (?, ?)",
                        (paper_id, category))
        
        # Simple chunking - split by ~1000 chars
        chunk_size = 1000
        for i in range(0, len(full_text), chunk_size):
            chunk = full_text[i:i+chunk_size]
            conn.execute("""
                INSERT INTO paper_chunks (paper_id, chunk_index, content, start_char, end_char, token_count, chunk_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (paper_id, str(i // chunk_size), chunk, i, min(i+chunk_size, len(full_text)), len(chunk)//4, "text"))
        
        conn.commit()
        print(f"OK ({title[:40]}...)")
        return paper_id, {"status": "success", "title": title}
        
    except sqlite3.IntegrityError as e:
        print(f"DB ERROR: {e}")
        conn.rollback()
        return None, {"status": "error", "error": str(e)}

def main():
    # Default to .research_papers in project root, or pass as arg
    import sys
    if len(sys.argv) > 1:
        source_dir = Path(sys.argv[1])
    else:
        source_dir = Path(__file__).parent.parent / ".research_papers"
    category = "ai-research"
    
    print("=" * 60)
    print("Quick Research Paper Ingest")
    print("=" * 60)
    
    # Get all PDFs
    pdfs = sorted([f for f in source_dir.iterdir() if f.suffix.lower() == ".pdf"])
    print(f"Found {len(pdfs)} PDFs in {source_dir}\n")
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = init_db()
    
    # Check current count
    cursor = conn.execute("SELECT COUNT(*) FROM research_papers")
    before = cursor.fetchone()[0]
    print(f"Papers in DB before: {before}\n")
    
    success = 0
    skipped = 0
    failed = 0
    
    for pdf in pdfs:
        paper_id, result = ingest_one(conn, str(pdf), category)
        if result["status"] == "success":
            success += 1
        elif result["status"] == "skipped":
            skipped += 1
        else:
            failed += 1
    
    # Final count
    cursor = conn.execute("SELECT COUNT(*) FROM research_papers")
    after = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print(f"Results: {success} ingested, {skipped} skipped, {failed} failed")
    print(f"Papers in DB after: {after} (added {after - before})")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    main()
