#!/usr/bin/env python3
"""
Production Research Database - First Principles Implementation

This script implements robust, defensive PDF extraction and database management
with systematic fallback handling for all failure modes.

Design Principles:
1. Never fail silently - always log and track failures
2. Multiple fallback strategies for metadata extraction
3. Validate all data before insert
4. Ensure 100% ingestion rate where technically possible
"""

import sys
import sqlite3
import hashlib
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Any
from dataclasses import dataclass

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

DB_PATH = Path(".workspace/research_papers.db")
SOURCE_DIR = Path("/home/mycahya/coding/AI Papers")


@dataclass
class ExtractedMetadata:
    """Validated metadata container."""
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    doi: str
    keywords: List[str]
    venue: str
    year: Optional[int]


@dataclass
class ExtractionResult:
    """Complete extraction result with validation status."""
    success: bool
    full_text: str
    metadata: ExtractedMetadata
    page_count: int
    word_count: int
    errors: List[str]
    warnings: List[str]


class RobustPDFExtractor:
    """First-principles PDF extractor with multiple fallback strategies."""
    
    # Patterns for metadata extraction
    ARXIV_PATTERNS = [
        r'arXiv:(\d{4}\.\d{4,5})',
        r'arxiv\.org/abs/(\d{4}\.\d{4,5})',
        r'(\d{4}\.\d{4,5})v\d+',
    ]
    
    DOI_PATTERNS = [
        r'doi\.org/(10\.\d{4,}/[^\s]+)',
        r'DOI:\s*(10\.\d{4,}/[^\s]+)',
        r'doi:\s*(10\.\d{4,}/[^\s]+)',
    ]
    
    ABSTRACT_MARKERS = [
        r'Abstract[:\s\-—]*\n?(.{100,2000}?)(?=\n\s*(?:1\.?\s*Introduction|Keywords|I\.\s*INTRODUCTION))',
        r'ABSTRACT[:\s\-—]*\n?(.{100,2000}?)(?=\n\s*(?:1\.?\s*Introduction|Keywords|I\.\s*INTRODUCTION))',
        r'Abstract[:\s\-—]*(.{100,2000}?)(?=\n\n)',
    ]
    
    VENUE_PATTERNS = [
        r'(ICLR|ICML|NeurIPS|CVPR|ACL|EMNLP|NAACL|AAAI|IJCAI)\s*(\d{4})',
        r'Proceedings of (?:the )?(\d{4}) (Conference|Annual Meeting)',
        r'Published (?:as a conference paper )?at (\w+)\s*(\d{4})',
    ]
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def extract(self) -> ExtractionResult:
        """Extract all content with comprehensive fallback handling."""
        import fitz  # PyMuPDF
        
        try:
            doc = fitz.open(str(self.pdf_path))
        except Exception as e:
            return ExtractionResult(
                success=False,
                full_text="",
                metadata=self._empty_metadata(),
                page_count=0,
                word_count=0,
                errors=[f"Failed to open PDF: {e}"],
                warnings=[]
            )
        
        # Extract full text from all pages
        full_text_parts = []
        for page_num in range(doc.page_count):
            try:
                page = doc[page_num]
                text = page.get_text()
                if text:
                    full_text_parts.append(text)
            except Exception as e:
                self.warnings.append(f"Page {page_num} extraction failed: {e}")
        
        full_text = "\n\n".join(full_text_parts)
        page_count = doc.page_count
        doc.close()
        
        if not full_text or len(full_text) < 100:
            self.errors.append("Insufficient text extracted from PDF")
            return ExtractionResult(
                success=False,
                full_text=full_text,
                metadata=self._empty_metadata(),
                page_count=page_count,
                word_count=len(full_text.split()),
                errors=self.errors,
                warnings=self.warnings
            )
        
        # Extract metadata with fallbacks
        metadata = self._extract_metadata(full_text)
        
        return ExtractionResult(
            success=True,
            full_text=full_text,
            metadata=metadata,
            page_count=page_count,
            word_count=len(full_text.split()),
            errors=self.errors,
            warnings=self.warnings
        )
    
    def _extract_metadata(self, text: str) -> ExtractedMetadata:
        """Extract metadata using multiple strategies with fallbacks."""
        
        # Title extraction (multiple strategies)
        title = self._extract_title(text)
        
        # Authors extraction
        authors = self._extract_authors(text)
        
        # Abstract extraction (multiple patterns)
        abstract = self._extract_abstract(text)
        
        # arXiv ID (from text and filename)
        arxiv_id = self._extract_arxiv_id(text)
        
        # DOI
        doi = self._extract_doi(text)
        
        # Keywords
        keywords = self._extract_keywords(text)
        
        # Venue and year
        venue, year = self._extract_venue(text)
        
        return ExtractedMetadata(
            title=title,
            authors=authors,
            abstract=abstract,
            arxiv_id=arxiv_id,
            doi=doi,
            keywords=keywords,
            venue=venue,
            year=year
        )
    
    def _extract_title(self, text: str) -> str:
        """Extract title with multiple fallback strategies."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Strategy 1: First substantial line that's not a header
        for i, line in enumerate(lines[:10]):
            # Skip arXiv headers
            if line.startswith('arXiv:') or 'preprint' in line.lower():
                continue
            # Skip page numbers
            if re.match(r'^\d+$', line):
                continue
            # Skip venue headers
            if any(v in line for v in ['Proceedings', 'Conference', 'Published as']):
                continue
            # Take first substantial line
            if len(line) > 20 and len(line) < 300:
                return line
        
        # Strategy 2: Filename as fallback
        return self.pdf_path.stem.replace('_', ' ').replace('-', ' ')
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract authors from common patterns."""
        # Look for author block near start
        first_2k = text[:2000]
        
        # Pattern: Names with affiliations (common in papers)
        author_block_match = re.search(
            r'(?:^|\n)([A-Z][a-z]+ [A-Z][a-z]+(?:,\s*[A-Z][a-z]+ [A-Z][a-z]+)*)',
            first_2k
        )
        if author_block_match:
            authors_str = author_block_match.group(1)
            return [a.strip() for a in authors_str.split(',') if a.strip()]
        
        return []
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract using multiple patterns with fallbacks."""
        # Strategy 1: Look for explicit "Abstract" section
        for pattern in self.ABSTRACT_MARKERS:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up
                abstract = re.sub(r'\s+', ' ', abstract)
                if len(abstract) > 100:
                    return abstract[:2000]
        
        # Strategy 2: First paragraph after title (heuristic)
        lines = text.split('\n\n')
        for i, para in enumerate(lines[1:6]):  # Check first few paragraphs
            para = para.strip()
            # Skip short or header-like paragraphs
            if len(para) < 200:
                continue
            # Skip if it looks like a section header
            if para.startswith(('1.', '1 ', 'I.', 'Introduction')):
                continue
            # This is likely the abstract
            return re.sub(r'\s+', ' ', para)[:2000]
        
        self.warnings.append("Could not extract abstract")
        return ""
    
    def _extract_arxiv_id(self, text: str) -> str:
        """Extract arXiv ID from text and filename."""
        # Try filename first
        filename_match = re.search(r'(\d{4}\.\d{4,5})', self.pdf_path.name)
        if filename_match:
            return filename_match.group(1)
        
        # Try text patterns
        for pattern in self.ARXIV_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_doi(self, text: str) -> str:
        """Extract DOI from text."""
        for pattern in self.DOI_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords if present."""
        match = re.search(r'Keywords?[:\s]+([^\n]+)', text, re.IGNORECASE)
        if match:
            keywords_str = match.group(1)
            # Split on common delimiters
            keywords = re.split(r'[,;•·]', keywords_str)
            return [k.strip() for k in keywords if k.strip() and len(k.strip()) < 50]
        return []
    
    def _extract_venue(self, text: str) -> Tuple[str, Optional[int]]:
        """Extract publication venue and year."""
        for pattern in self.VENUE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                venue = groups[0] if groups else ""
                year = None
                for g in groups:
                    if g and re.match(r'\d{4}', str(g)):
                        year = int(g)
                        break
                return venue, year
        return "", None
    
    def _empty_metadata(self) -> ExtractedMetadata:
        """Return empty metadata structure."""
        return ExtractedMetadata(
            title=self.pdf_path.stem,
            authors=[],
            abstract="",
            arxiv_id="",
            doi="",
            keywords=[],
            venue="",
            year=None
        )


class ResearchDBManager:
    """Database manager with validation and quality checks."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()
    
    def get_content_hash(self, text: str) -> str:
        """Generate content hash for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def paper_exists(self, content_hash: str) -> bool:
        """Check if paper already exists."""
        cursor = self.conn.execute(
            "SELECT id FROM research_papers WHERE content_hash = ?",
            (content_hash,)
        )
        return cursor.fetchone() is not None
    
    def get_paper_by_path(self, source_path: str) -> Optional[str]:
        """Get paper ID by source path."""
        cursor = self.conn.execute(
            "SELECT id FROM research_papers WHERE source_path = ?",
            (source_path,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    
    def update_paper_metadata(self, paper_id: str, metadata: ExtractedMetadata, full_text: str):
        """Update paper with extracted metadata."""
        self.conn.execute("""
            UPDATE research_papers SET
                title = COALESCE(NULLIF(?, ''), title),
                authors = COALESCE(NULLIF(?, ''), authors),
                abstract = COALESCE(NULLIF(?, ''), abstract),
                arxiv_id = COALESCE(NULLIF(?, ''), arxiv_id),
                doi = COALESCE(NULLIF(?, ''), doi),
                keywords = COALESCE(NULLIF(?, ''), keywords),
                venue = COALESCE(NULLIF(?, ''), venue),
                full_text = ?,
                word_count = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            metadata.title,
            ", ".join(metadata.authors),
            metadata.abstract,
            metadata.arxiv_id,
            metadata.doi,
            ", ".join(metadata.keywords),
            metadata.venue,
            full_text,
            len(full_text.split()),
            paper_id
        ))
        self.conn.commit()
    
    def insert_paper(self, result: ExtractionResult, source_path: Path, category: str = "ai-research") -> Tuple[str, str]:
        """Insert new paper with full validation."""
        content_hash = self.get_content_hash(result.full_text)
        
        if self.paper_exists(content_hash):
            return "", "duplicate"
        
        paper_id = f"paper_{content_hash}"
        metadata = result.metadata
        
        try:
            self.conn.execute("""
                INSERT INTO research_papers 
                (id, title, authors, abstract, arxiv_id, doi, keywords, venue,
                 source_path, page_count, word_count, content_hash, full_text,
                 extraction_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
            """, (
                paper_id,
                metadata.title,
                ", ".join(metadata.authors),
                metadata.abstract,
                metadata.arxiv_id or None,  # Allow NULL for non-arXiv papers
                metadata.doi,
                ", ".join(metadata.keywords),
                metadata.venue,
                str(source_path),
                result.page_count,
                result.word_count,
                content_hash,
                result.full_text
            ))
            
            # Add category
            self.conn.execute(
                "INSERT OR IGNORE INTO paper_categories (paper_id, category) VALUES (?, ?)",
                (paper_id, category)
            )
            
            # Create chunks
            self._create_chunks(paper_id, result.full_text)
            
            self.conn.commit()
            return paper_id, "success"
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return "", f"integrity_error: {e}"
        except Exception as e:
            self.conn.rollback()
            return "", f"error: {e}"
    
    def _create_chunks(self, paper_id: str, text: str, chunk_size: int = 1000, overlap: int = 200):
        """Create text chunks for the paper."""
        # Delete existing chunks
        self.conn.execute("DELETE FROM paper_chunks WHERE paper_id = ?", (paper_id,))
        
        chunk_idx = 0
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if len(chunk) > 100:
                self.conn.execute("""
                    INSERT INTO paper_chunks 
                    (paper_id, chunk_index, content, start_char, end_char, token_count, chunk_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, chunk_idx, chunk, i, i + len(chunk), len(chunk) // 4, "text"))
                chunk_idx += 1
        
        return chunk_idx
    
    def get_papers_missing_metadata(self) -> List[Dict]:
        """Get papers that need metadata updates."""
        cursor = self.conn.execute("""
            SELECT id, source_path, title, abstract, arxiv_id, LENGTH(full_text) as text_len
            FROM research_papers
            WHERE abstract IS NULL OR abstract = ''
               OR LENGTH(full_text) < 10000
               OR title LIKE 'arXiv:%'
               OR title LIKE 'Published %'
               OR title = '1'
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        stats = {}
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM research_papers")
        stats["total_papers"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM research_papers WHERE full_text IS NOT NULL AND LENGTH(full_text) > 10000"
        )
        stats["with_full_text"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM research_papers WHERE abstract IS NOT NULL AND LENGTH(abstract) > 50"
        )
        stats["with_abstract"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM research_papers WHERE arxiv_id IS NOT NULL AND arxiv_id != ''"
        )
        stats["with_arxiv"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT AVG(LENGTH(full_text)), AVG(word_count) FROM research_papers")
        row = cursor.fetchone()
        stats["avg_text_len"] = int(row[0] or 0)
        stats["avg_words"] = int(row[1] or 0)
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM paper_chunks")
        stats["total_chunks"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM research_fts")
        stats["fts_entries"] = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM paper_embeddings")
        stats["embeddings"] = cursor.fetchone()[0]
        
        return stats


def run_full_extraction(source_dir: Path = SOURCE_DIR):
    """Run full extraction on all PDFs with quality reporting."""
    logger.info("=" * 70)
    logger.info("PRODUCTION RESEARCH DB - FULL EXTRACTION")
    logger.info("=" * 70)
    
    db = ResearchDBManager()
    
    # Get all PDFs
    pdfs = sorted([f for f in source_dir.iterdir() if f.suffix.lower() == ".pdf"])
    logger.info(f"Found {len(pdfs)} PDFs in {source_dir}")
    
    # Get initial stats
    before_stats = db.get_stats()
    logger.info(f"Papers before: {before_stats['total_papers']}")
    
    results = {
        "success": [],
        "duplicate": [],
        "failed": [],
        "updated": []
    }
    
    for pdf in pdfs:
        # Check if already exists
        existing_id = db.get_paper_by_path(str(pdf))
        
        # Extract
        extractor = RobustPDFExtractor(str(pdf))
        result = extractor.extract()
        
        if not result.success:
            logger.error(f"✗ {pdf.name}: {result.errors}")
            results["failed"].append({"path": str(pdf), "errors": result.errors})
            continue
        
        if existing_id:
            # Update existing paper
            db.update_paper_metadata(existing_id, result.metadata, result.full_text)
            logger.info(f"↻ {pdf.name}: updated metadata")
            results["updated"].append(str(pdf))
        else:
            # Insert new paper
            paper_id, status = db.insert_paper(result, pdf)
            
            if status == "success":
                logger.info(f"✓ {pdf.name}: {result.metadata.title[:40]}...")
                results["success"].append(str(pdf))
            elif status == "duplicate":
                logger.info(f"~ {pdf.name}: duplicate")
                results["duplicate"].append(str(pdf))
            else:
                logger.error(f"✗ {pdf.name}: {status}")
                results["failed"].append({"path": str(pdf), "errors": [status]})
    
    # Final stats
    after_stats = db.get_stats()
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("EXTRACTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"New papers:     {len(results['success'])}")
    logger.info(f"Updated:        {len(results['updated'])}")
    logger.info(f"Duplicates:     {len(results['duplicate'])}")
    logger.info(f"Failed:         {len(results['failed'])}")
    logger.info("")
    logger.info(f"Total papers:   {after_stats['total_papers']}")
    logger.info(f"With full text: {after_stats['with_full_text']} ({100*after_stats['with_full_text']/after_stats['total_papers']:.0f}%)")
    logger.info(f"With abstract:  {after_stats['with_abstract']} ({100*after_stats['with_abstract']/after_stats['total_papers']:.0f}%)")
    logger.info(f"With arXiv ID:  {after_stats['with_arxiv']} ({100*after_stats['with_arxiv']/after_stats['total_papers']:.0f}%)")
    logger.info(f"Total chunks:   {after_stats['total_chunks']}")
    logger.info(f"FTS entries:    {after_stats['fts_entries']}")
    
    db.close()
    return results, after_stats


def fix_missing_metadata():
    """Fix papers with missing or poor metadata."""
    logger.info("=" * 70)
    logger.info("FIXING MISSING METADATA")
    logger.info("=" * 70)
    
    db = ResearchDBManager()
    papers = db.get_papers_missing_metadata()
    
    logger.info(f"Found {len(papers)} papers needing metadata fixes")
    
    fixed = 0
    for paper in papers:
        source_path = Path(paper["source_path"])
        
        # Try to find the file
        if not source_path.exists():
            source_path = SOURCE_DIR / source_path.name
        
        if not source_path.exists():
            logger.warning(f"  ? {paper['id']}: source file not found")
            continue
        
        # Re-extract
        extractor = RobustPDFExtractor(str(source_path))
        result = extractor.extract()
        
        if result.success:
            db.update_paper_metadata(paper["id"], result.metadata, result.full_text)
            logger.info(f"  ✓ {source_path.name}: {result.metadata.title[:40]}...")
            fixed += 1
        else:
            logger.error(f"  ✗ {source_path.name}: {result.errors}")
    
    logger.info(f"\nFixed: {fixed}/{len(papers)}")
    db.close()


def validate_database():
    """Validate database integrity and completeness."""
    logger.info("=" * 70)
    logger.info("DATABASE VALIDATION")
    logger.info("=" * 70)
    
    db = ResearchDBManager()
    stats = db.get_stats()
    
    issues = []
    
    # Check for papers without full text
    cursor = db.conn.execute(
        "SELECT COUNT(*) FROM research_papers WHERE full_text IS NULL OR LENGTH(full_text) < 1000"
    )
    no_text = cursor.fetchone()[0]
    if no_text > 0:
        issues.append(f"{no_text} papers without adequate full text")
    
    # Check for papers without chunks
    cursor = db.conn.execute("""
        SELECT COUNT(*) FROM research_papers p
        WHERE NOT EXISTS (SELECT 1 FROM paper_chunks c WHERE c.paper_id = p.id)
    """)
    no_chunks = cursor.fetchone()[0]
    if no_chunks > 0:
        issues.append(f"{no_chunks} papers without chunks")
    
    # Check for papers without FTS
    cursor = db.conn.execute("""
        SELECT COUNT(*) FROM research_papers p
        WHERE NOT EXISTS (SELECT 1 FROM research_fts f WHERE f.paper_id = p.id)
    """)
    no_fts = cursor.fetchone()[0]
    if no_fts > 0:
        issues.append(f"{no_fts} papers not in FTS index")
    
    # Report
    logger.info(f"Total papers: {stats['total_papers']}")
    logger.info(f"With full text: {stats['with_full_text']}")
    logger.info(f"With abstract: {stats['with_abstract']}")
    logger.info(f"Total chunks: {stats['total_chunks']}")
    logger.info(f"FTS entries: {stats['fts_entries']}")
    
    if issues:
        logger.warning("\nIssues found:")
        for issue in issues:
            logger.warning(f"  • {issue}")
    else:
        logger.info("\n✓ All validation checks passed!")
    
    db.close()
    return len(issues) == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Research Database Manager")
    parser.add_argument("command", choices=["extract", "fix", "validate", "all"],
                       help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "extract":
        run_full_extraction()
    elif args.command == "fix":
        fix_missing_metadata()
    elif args.command == "validate":
        validate_database()
    elif args.command == "all":
        run_full_extraction()
        fix_missing_metadata()
        validate_database()
