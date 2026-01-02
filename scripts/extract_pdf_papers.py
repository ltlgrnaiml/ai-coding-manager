"""PDF Paper Extraction Tool for AI Research Analysis.

This tool extracts text, images, and tables from academic PDF papers,
generating structured output suitable for AI consumption and RAG systems.

Citation: [Engineering-Tools-2025] "PDF Paper Extraction Tool"
          https://github.com/ltlgrnaiml/engineering-tools
          Key insight: Structured extraction with metadata parsing for academic papers
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import pdfplumber


@dataclass
class ExtractedImage:
    """Represents an extracted image from a PDF."""

    page_number: int
    image_index: int
    width: int
    height: int
    image_path: str
    caption: str | None = None


@dataclass
class ExtractedTable:
    """Represents an extracted table from a PDF."""

    page_number: int
    table_index: int
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None


@dataclass
class PaperMetadata:
    """Metadata extracted from a paper."""

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    publication_date: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    venue: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class ExtractedPaper:
    """Complete extraction from a PDF paper."""

    source_path: str
    extraction_date: str
    content_hash: str
    metadata: PaperMetadata
    full_text: str
    sections: dict[str, str]
    images: list[ExtractedImage]
    tables: list[ExtractedTable]
    page_count: int
    word_count: int


def extract_metadata_from_text(text: str) -> PaperMetadata:
    """Extract paper metadata from text content.

    Args:
        text: Full text content of the paper.

    Returns:
        PaperMetadata object with extracted fields.
    """
    metadata = PaperMetadata()

    # Try to extract arXiv ID
    arxiv_pattern = r"arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)"
    arxiv_match = re.search(arxiv_pattern, text)
    if arxiv_match:
        metadata.arxiv_id = arxiv_match.group(1)

    # Try to extract DOI
    doi_pattern = r"(?:doi[:\s]*|https?://doi\.org/)?(10\.\d{4,}/[^\s]+)"
    doi_match = re.search(doi_pattern, text, re.IGNORECASE)
    if doi_match:
        metadata.doi = doi_match.group(1).rstrip(".,;)")

    # Try to extract abstract
    abstract_patterns = [
        r"Abstract[:\s]*\n+(.*?)(?:\n\n|\n[A-Z][a-z]+\s*\n|Introduction)",
        r"ABSTRACT[:\s]*\n+(.*?)(?:\n\n|\n[A-Z][a-z]+\s*\n|INTRODUCTION)",
    ]
    for pattern in abstract_patterns:
        abstract_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            metadata.abstract = abstract_match.group(1).strip()[:2000]
            break

    # Try to extract keywords
    keywords_pattern = r"Keywords?[:\s]*(.*?)(?:\n\n|\n[A-Z])"
    keywords_match = re.search(keywords_pattern, text, re.IGNORECASE)
    if keywords_match:
        keywords_text = keywords_match.group(1)
        metadata.keywords = [
            k.strip() for k in re.split(r"[,;·•]", keywords_text) if k.strip()
        ][:10]

    return metadata


def extract_sections(text: str) -> dict[str, str]:
    """Extract major sections from paper text.

    Args:
        text: Full text content of the paper.

    Returns:
        Dictionary mapping section names to content.
    """
    sections = {}

    # Common section headers in academic papers
    section_patterns = [
        r"\n(\d+\.?\s*(?:Introduction|INTRODUCTION))\s*\n",
        r"\n(\d+\.?\s*(?:Related Work|RELATED WORK|Background|BACKGROUND))\s*\n",
        r"\n(\d+\.?\s*(?:Method(?:ology)?|METHOD(?:OLOGY)?|Approach|APPROACH))\s*\n",
        r"\n(\d+\.?\s*(?:Experiment(?:s)?|EXPERIMENT(?:S)?|Evaluation|EVALUATION))\s*\n",
        r"\n(\d+\.?\s*(?:Results?|RESULTS?))\s*\n",
        r"\n(\d+\.?\s*(?:Discussion|DISCUSSION))\s*\n",
        r"\n(\d+\.?\s*(?:Conclusion(?:s)?|CONCLUSION(?:S)?))\s*\n",
        r"\n(\d+\.?\s*(?:References?|REFERENCES?|Bibliography|BIBLIOGRAPHY))\s*\n",
    ]

    # Find all section starts
    section_starts = []
    for pattern in section_patterns:
        for match in re.finditer(pattern, text):
            section_starts.append((match.start(), match.group(1).strip()))

    # Sort by position
    section_starts.sort(key=lambda x: x[0])

    # Extract content between sections
    for i, (start, name) in enumerate(section_starts):
        if i + 1 < len(section_starts):
            end = section_starts[i + 1][0]
        else:
            end = len(text)

        content = text[start:end].strip()
        # Remove the header from content
        content = re.sub(r"^\d+\.?\s*\w+\s*\n", "", content)
        sections[name] = content[:5000]  # Limit section size

    return sections


def extract_paper(pdf_path: str, output_dir: str) -> ExtractedPaper:
    """Extract all content from a PDF paper.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory to save extracted images.

    Returns:
        ExtractedPaper object with all extracted content.
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectory for this paper's assets
    paper_hash = hashlib.md5(pdf_path.name.encode()).hexdigest()[:8]
    paper_dir = output_dir / f"{pdf_path.stem}_{paper_hash}"
    paper_dir.mkdir(exist_ok=True)

    # Extract text and images with PyMuPDF
    doc = fitz.open(str(pdf_path))
    full_text_parts = []
    images: list[ExtractedImage] = []

    for page_num, page in enumerate(doc):
        # Extract text
        full_text_parts.append(page.get_text())

        # Extract images
        image_list = page.get_images()
        for img_idx, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Save image
                image_filename = f"page{page_num + 1}_img{img_idx + 1}.{image_ext}"
                image_path = paper_dir / image_filename
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                images.append(
                    ExtractedImage(
                        page_number=page_num + 1,
                        image_index=img_idx + 1,
                        width=base_image.get("width", 0),
                        height=base_image.get("height", 0),
                        image_path=str(image_path),
                    )
                )
            except Exception:
                pass  # Skip problematic images

    full_text = "\n".join(full_text_parts)
    page_count = len(doc)
    doc.close()

    # Extract tables with pdfplumber
    tables: list[ExtractedTable] = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table_idx, table in enumerate(page_tables):
                    if table and len(table) > 1:
                        headers = [str(cell) if cell else "" for cell in table[0]]
                        rows = [
                            [str(cell) if cell else "" for cell in row]
                            for row in table[1:]
                        ]
                        tables.append(
                            ExtractedTable(
                                page_number=page_num + 1,
                                table_index=table_idx + 1,
                                headers=headers,
                                rows=rows,
                            )
                        )
    except Exception:
        pass  # Skip if table extraction fails

    # Extract metadata and sections
    metadata = extract_metadata_from_text(full_text)
    sections = extract_sections(full_text)

    # Try to get title from first page
    first_page_text = full_text_parts[0] if full_text_parts else ""
    lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]
    if lines:
        # First non-empty line is often the title
        potential_title = lines[0]
        if len(potential_title) < 200:
            metadata.title = potential_title

    # Calculate content hash
    content_hash = hashlib.sha256(full_text.encode()).hexdigest()[:16]

    return ExtractedPaper(
        source_path=str(pdf_path),
        extraction_date=datetime.now().isoformat(),
        content_hash=content_hash,
        metadata=metadata,
        full_text=full_text,
        sections=sections,
        images=images,
        tables=tables,
        page_count=page_count,
        word_count=len(full_text.split()),
    )


def paper_to_dict(paper: ExtractedPaper) -> dict[str, Any]:
    """Convert ExtractedPaper to dictionary for JSON serialization.

    Args:
        paper: ExtractedPaper object.

    Returns:
        Dictionary representation.
    """
    return {
        "source_path": paper.source_path,
        "extraction_date": paper.extraction_date,
        "content_hash": paper.content_hash,
        "metadata": {
            "title": paper.metadata.title,
            "authors": paper.metadata.authors,
            "abstract": paper.metadata.abstract,
            "publication_date": paper.metadata.publication_date,
            "doi": paper.metadata.doi,
            "arxiv_id": paper.metadata.arxiv_id,
            "venue": paper.metadata.venue,
            "keywords": paper.metadata.keywords,
        },
        "sections": paper.sections,
        "images": [
            {
                "page_number": img.page_number,
                "image_index": img.image_index,
                "width": img.width,
                "height": img.height,
                "image_path": img.image_path,
                "caption": img.caption,
            }
            for img in paper.images
        ],
        "tables": [
            {
                "page_number": tbl.page_number,
                "table_index": tbl.table_index,
                "headers": tbl.headers,
                "rows": tbl.rows,
                "caption": tbl.caption,
            }
            for tbl in paper.tables
        ],
        "page_count": paper.page_count,
        "word_count": paper.word_count,
        "full_text_preview": paper.full_text[:5000] + "..."
        if len(paper.full_text) > 5000
        else paper.full_text,
    }


def generate_paper_summary(paper: ExtractedPaper) -> str:
    """Generate a markdown summary of the extracted paper.

    Args:
        paper: ExtractedPaper object.

    Returns:
        Markdown formatted summary.
    """
    lines = []
    lines.append(f"# {paper.metadata.title or 'Untitled Paper'}")
    lines.append("")

    if paper.metadata.arxiv_id:
        lines.append(f"**arXiv**: {paper.metadata.arxiv_id}")
    if paper.metadata.doi:
        lines.append(f"**DOI**: {paper.metadata.doi}")

    lines.append(f"**Pages**: {paper.page_count}")
    lines.append(f"**Words**: {paper.word_count:,}")
    lines.append(f"**Images**: {len(paper.images)}")
    lines.append(f"**Tables**: {len(paper.tables)}")
    lines.append("")

    if paper.metadata.abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(paper.metadata.abstract)
        lines.append("")

    if paper.metadata.keywords:
        lines.append("## Keywords")
        lines.append("")
        lines.append(", ".join(paper.metadata.keywords))
        lines.append("")

    if paper.sections:
        lines.append("## Sections Found")
        lines.append("")
        for section_name in paper.sections.keys():
            lines.append(f"- {section_name}")
        lines.append("")

    return "\n".join(lines)


def process_paper_batch(
    pdf_paths: list[str], output_dir: str, category: str
) -> dict[str, Any]:
    """Process a batch of papers in a category.

    Args:
        pdf_paths: List of paths to PDF files.
        output_dir: Base output directory.
        category: Category name for organization.

    Returns:
        Dictionary with batch processing results.
    """
    category_dir = Path(output_dir) / category
    category_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "category": category,
        "processed": [],
        "failed": [],
        "summary": {},
    }

    for pdf_path in pdf_paths:
        try:
            print(f"Processing: {pdf_path}")
            paper = extract_paper(pdf_path, str(category_dir))

            # Save JSON extraction
            json_path = category_dir / f"{Path(pdf_path).stem}_extraction.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(paper_to_dict(paper), f, indent=2, ensure_ascii=False)

            # Save markdown summary
            md_path = category_dir / f"{Path(pdf_path).stem}_summary.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(generate_paper_summary(paper))

            # Save full text
            txt_path = category_dir / f"{Path(pdf_path).stem}_fulltext.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(paper.full_text)

            results["processed"].append(
                {
                    "source": pdf_path,
                    "title": paper.metadata.title,
                    "arxiv_id": paper.metadata.arxiv_id,
                    "doi": paper.metadata.doi,
                    "pages": paper.page_count,
                    "words": paper.word_count,
                    "images": len(paper.images),
                    "tables": len(paper.tables),
                    "json_path": str(json_path),
                    "md_path": str(md_path),
                }
            )
            print(f"  ✓ Extracted: {paper.metadata.title or 'Untitled'}")

        except Exception as e:
            results["failed"].append({"source": pdf_path, "error": str(e)})
            print(f"  ✗ Failed: {e}")

    results["summary"] = {
        "total": len(pdf_paths),
        "success": len(results["processed"]),
        "failed": len(results["failed"]),
    }

    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_papers.py <pdf_path> [output_dir]")
        print("       python extract_pdf_papers.py --batch <category> <pdf_path1> <pdf_path2> ...")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 4:
            print("Batch mode requires: --batch <category> <pdf_path1> [pdf_path2] ...")
            sys.exit(1)
        
        category = sys.argv[2]
        pdf_paths = sys.argv[3:]
        output_dir = "extracted_papers"
        
        print(f"Processing {len(pdf_paths)} papers in category '{category}'")
        results = process_paper_batch(pdf_paths, output_dir, category)
        
        print(f"\nResults: {results['summary']['success']} succeeded, {results['summary']['failed']} failed")
        
    else:
        # Single file mode
        pdf_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_papers"
        
        print(f"Extracting: {pdf_path}")
        paper = extract_paper(pdf_path, output_dir)
        
        # Save outputs
        output_path = Path(output_dir)
        stem = Path(pdf_path).stem
        
        # JSON
        json_path = output_path / f"{stem}_extraction.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(paper_to_dict(paper), f, indent=2, ensure_ascii=False)
        
        # Markdown summary
        md_path = output_path / f"{stem}_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(generate_paper_summary(paper))
        
        # Full text
        txt_path = output_path / f"{stem}_fulltext.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(paper.full_text)
        
        print(f"✓ Extracted to: {output_path}")
        print(f"  Title: {paper.metadata.title}")
        print(f"  Pages: {paper.page_count}")
        print(f"  Words: {paper.word_count:,}")
        print(f"  Images: {len(paper.images)}")
        print(f"  Tables: {len(paper.tables)}")
