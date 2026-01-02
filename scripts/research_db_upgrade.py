#!/usr/bin/env python3
"""
Production Research Database Upgrade Script

Fixes:
1. Full text truncation (was 5003 chars, now unlimited)
2. Missing papers (retry failed ingestions)
3. FTS population (ensure all papers searchable)
4. Missing metadata (re-extract where needed)
5. Data validation and quality checks
"""

import sys
import sqlite3
import hashlib
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DB_PATH = Path(".workspace/research_papers.db")
SOURCE_DIR = Path("/home/mycahya/coding/AI Papers")
OUTPUT_DIR = Path(".workspace/research_papers/extracted")


def get_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def extract_arxiv_id(text: str, filename: str) -> str:
    """Extract arXiv ID from text or filename."""
    # From filename like 2508.00083v2.pdf
    match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', filename)
    if match:
        return match.group(1)
    
    # From text
    match = re.search(r'arXiv:(\d{4}\.\d{4,5})', text)
    if match:
        return match.group(1)
    
    return ""


def extract_full_text(pdf_path: str) -> dict:
    """Extract FULL text from PDF using PyMuPDF directly."""
    import fitz  # PyMuPDF
    from extract_pdf_papers import extract_metadata_from_text
    
    doc = fitz.open(pdf_path)
    
    # Get all text from all pages
    full_text_parts = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()
        if text:
            full_text_parts.append(text)
    
    full_text = "\n\n".join(full_text_parts)
    page_count = doc.page_count
    doc.close()
    
    # Extract metadata from text
    metadata = extract_metadata_from_text(full_text)
    
    return {
        "full_text": full_text,
        "metadata": {
            "title": metadata.title,
            "authors": metadata.authors,
            "abstract": metadata.abstract,
            "arxiv_id": metadata.arxiv_id,
            "doi": metadata.doi,
            "keywords": metadata.keywords,
        },
        "page_count": page_count,
        "word_count": len(full_text.split()),
    }


def ensure_schema(conn: sqlite3.Connection):
    """Ensure all required columns and tables exist."""
    # Add full_text column if missing
    cursor = conn.execute("PRAGMA table_info(research_papers)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if "full_text" not in columns:
        print("Adding full_text column...")
        conn.execute("ALTER TABLE research_papers ADD COLUMN full_text TEXT")
        conn.commit()
    
    # Ensure FTS table exists and is populated
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='research_fts'")
    if not cursor.fetchone():
        print("Creating FTS table...")
        conn.execute("""
            CREATE VIRTUAL TABLE research_fts USING fts5(
                title, authors, abstract, full_text,
                content='research_papers',
                content_rowid='rowid'
            )
        """)
        conn.commit()


def populate_fts(conn: sqlite3.Connection):
    """Populate FTS index with all papers."""
    print("Rebuilding FTS index...")
    
    # Check if FTS table exists and what type it is
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE name='research_fts'")
    fts_sql = cursor.fetchone()
    
    if fts_sql and 'content=' in str(fts_sql[0]):
        # Content-synced FTS - just rebuild
        try:
            conn.execute("INSERT INTO research_fts(research_fts) VALUES('rebuild')")
            conn.commit()
            cursor = conn.execute("SELECT COUNT(*) FROM research_fts")
            count = cursor.fetchone()[0]
            print(f"FTS index rebuilt (content-synced): {count} entries")
            return
        except Exception as e:
            print(f"FTS rebuild failed: {e}, creating new FTS table...")
    
    # Drop and recreate FTS table
    try:
        conn.execute("DROP TABLE IF EXISTS research_fts")
    except:
        pass
    
    # Create new FTS table
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS research_fts USING fts5(
            paper_id, title, authors, abstract, full_text
        )
    """)
    
    # Get all papers and insert
    cursor = conn.execute("""
        SELECT id, title, authors, abstract, full_text 
        FROM research_papers
    """)
    papers = cursor.fetchall()
    
    for paper_id, title, authors, abstract, full_text in papers:
        conn.execute("""
            INSERT INTO research_fts(paper_id, title, authors, abstract, full_text)
            VALUES (?, ?, ?, ?, ?)
        """, (paper_id, title or "", authors or "", abstract or "", full_text or ""))
    
    conn.commit()
    print(f"FTS index created with {len(papers)} papers")


def fix_paper(conn: sqlite3.Connection, paper_id: str, pdf_path: Path):
    """Fix a single paper's data."""
    try:
        data = extract_full_text(str(pdf_path))
        full_text = data["full_text"]
        metadata = data["metadata"]
        
        # Extract arXiv ID if missing
        arxiv_id = metadata.get("arxiv_id") or extract_arxiv_id(full_text, pdf_path.name)
        
        # Update paper
        conn.execute("""
            UPDATE research_papers SET
                full_text = ?,
                arxiv_id = COALESCE(NULLIF(arxiv_id, ''), ?),
                abstract = COALESCE(NULLIF(abstract, ''), ?),
                word_count = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            full_text,
            arxiv_id,
            metadata.get("abstract", ""),
            data["word_count"],
            paper_id
        ))
        
        # Re-chunk with full text
        conn.execute("DELETE FROM paper_chunks WHERE paper_id = ?", (paper_id,))
        
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            if len(chunk) > 100:  # Skip tiny chunks
                chunks.append((paper_id, len(chunks), chunk, i, i + len(chunk), len(chunk) // 4, "text"))
        
        conn.executemany("""
            INSERT INTO paper_chunks (paper_id, chunk_index, content, start_char, end_char, token_count, chunk_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, chunks)
        
        return True, len(full_text), len(chunks)
        
    except Exception as e:
        return False, 0, str(e)


def ingest_missing(conn: sqlite3.Connection, pdf_path: Path, category: str = "ai-research"):
    """Ingest a missing paper."""
    try:
        data = extract_full_text(str(pdf_path))
        full_text = data["full_text"]
        metadata = data["metadata"]
        
        content_hash = get_content_hash(full_text)
        paper_id = f"paper_{content_hash}"
        
        # Check if exists
        cursor = conn.execute("SELECT id FROM research_papers WHERE content_hash = ?", (content_hash,))
        if cursor.fetchone():
            return None, "duplicate"
        
        arxiv_id = metadata.get("arxiv_id") or extract_arxiv_id(full_text, pdf_path.name)
        title = metadata.get("title", pdf_path.stem)
        authors = ", ".join(metadata.get("authors", []))
        abstract = metadata.get("abstract", "")
        keywords = ", ".join(metadata.get("keywords", []))
        
        conn.execute("""
            INSERT INTO research_papers 
            (id, title, authors, abstract, arxiv_id, keywords, source_path, 
             page_count, word_count, content_hash, full_text,
             extraction_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
        """, (
            paper_id, title, authors, abstract, arxiv_id, keywords,
            str(pdf_path), data["page_count"], data["word_count"], content_hash, full_text
        ))
        
        conn.execute("INSERT OR IGNORE INTO paper_categories (paper_id, category) VALUES (?, ?)",
                    (paper_id, category))
        
        # Chunk
        chunk_size = 1000
        overlap = 200
        for i in range(0, len(full_text), chunk_size - overlap):
            chunk = full_text[i:i + chunk_size]
            if len(chunk) > 100:
                conn.execute("""
                    INSERT INTO paper_chunks (paper_id, chunk_index, content, start_char, end_char, token_count, chunk_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, i // (chunk_size - overlap), chunk, i, i + len(chunk), len(chunk) // 4, "text"))
        
        conn.commit()
        return paper_id, "success"
        
    except Exception as e:
        return None, str(e)


def main():
    print("=" * 70)
    print("PRODUCTION RESEARCH DATABASE UPGRADE")
    print("=" * 70)
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    
    # Step 1: Ensure schema
    print("Step 1: Schema validation...")
    ensure_schema(conn)
    
    # Step 2: Get current state
    cursor = conn.execute("SELECT COUNT(*) FROM research_papers")
    before_count = cursor.fetchone()[0]
    print(f"Papers before: {before_count}")
    
    # Step 3: Find papers needing fixes
    print("\nStep 2: Identifying papers needing fixes...")
    cursor = conn.execute("""
        SELECT id, source_path, 
               COALESCE(LENGTH(full_text), 0) as text_len,
               COALESCE(abstract, '') as abstract,
               COALESCE(arxiv_id, '') as arxiv_id
        FROM research_papers
    """)
    papers = cursor.fetchall()
    
    needs_fix = []
    for paper_id, source_path, text_len, abstract, arxiv_id in papers:
        issues = []
        if text_len < 10000:  # Likely truncated
            issues.append("truncated")
        if not abstract:
            issues.append("no_abstract")
        if not arxiv_id:
            issues.append("no_arxiv")
        
        if issues:
            needs_fix.append((paper_id, source_path, issues))
    
    print(f"Papers needing fixes: {len(needs_fix)}")
    
    # Step 4: Fix papers
    if needs_fix:
        print("\nStep 3: Fixing papers...")
        fixed = 0
        for paper_id, source_path, issues in needs_fix:
            pdf_path = Path(source_path)
            if not pdf_path.exists():
                # Try alternate path
                pdf_path = SOURCE_DIR / pdf_path.name
            
            if pdf_path.exists():
                success, text_len, chunks = fix_paper(conn, paper_id, pdf_path)
                if success:
                    fixed += 1
                    print(f"  ✓ {pdf_path.name}: {text_len} chars, {chunks} chunks")
                else:
                    print(f"  ✗ {pdf_path.name}: {chunks}")
            else:
                print(f"  ? {source_path}: file not found")
        
        conn.commit()
        print(f"Fixed: {fixed}/{len(needs_fix)}")
    
    # Step 5: Ingest missing papers
    print("\nStep 4: Ingesting missing papers...")
    all_pdfs = set(f for f in SOURCE_DIR.iterdir() if f.suffix.lower() == ".pdf")
    cursor = conn.execute("SELECT source_path FROM research_papers")
    ingested_paths = {Path(row[0]).name for row in cursor.fetchall()}
    
    missing = [pdf for pdf in all_pdfs if pdf.name not in ingested_paths]
    print(f"Missing papers: {len(missing)}")
    
    ingested = 0
    for pdf in missing:
        paper_id, status = ingest_missing(conn, pdf)
        if status == "success":
            ingested += 1
            print(f"  ✓ {pdf.name}")
        elif status == "duplicate":
            print(f"  ~ {pdf.name} (duplicate)")
        else:
            print(f"  ✗ {pdf.name}: {status}")
    
    print(f"Ingested: {ingested}/{len(missing)}")
    
    # Step 6: Rebuild FTS
    print("\nStep 5: Rebuilding FTS index...")
    populate_fts(conn)
    
    # Step 7: Final stats
    print("\n" + "=" * 70)
    print("FINAL QUALITY REPORT")
    print("=" * 70)
    
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN full_text IS NOT NULL AND LENGTH(full_text) > 10000 THEN 1 ELSE 0 END) as has_full_text,
            SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as has_abstract,
            SUM(CASE WHEN arxiv_id IS NOT NULL AND arxiv_id != '' THEN 1 ELSE 0 END) as has_arxiv,
            AVG(word_count) as avg_words,
            AVG(LENGTH(full_text)) as avg_text_len
        FROM research_papers
    """)
    row = cursor.fetchone()
    
    print(f"Total papers: {row[0]}")
    print(f"With full text: {row[1]} ({100*row[1]/row[0]:.0f}%)")
    print(f"With abstract: {row[2]} ({100*row[2]/row[0]:.0f}%)")
    print(f"With arXiv ID: {row[3]} ({100*row[3]/row[0]:.0f}%)")
    print(f"Avg word count: {row[4]:.0f}")
    print(f"Avg text length: {row[5]:.0f} chars")
    
    cursor = conn.execute("SELECT COUNT(*) FROM paper_chunks")
    print(f"Total chunks: {cursor.fetchone()[0]}")
    
    cursor = conn.execute("SELECT COUNT(*) FROM research_fts")
    print(f"FTS entries: {cursor.fetchone()[0]}")
    
    # Test FTS
    print("\nFTS Search Test:")
    cursor = conn.execute("""
        SELECT title FROM research_fts WHERE research_fts MATCH 'context compression' LIMIT 3
    """)
    results = cursor.fetchall()
    for r in results:
        print(f"  - {r[0][:60]}...")
    
    conn.close()
    print("\n" + "=" * 70)
    print("UPGRADE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
