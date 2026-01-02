"""Research Paper Ingestion Pipeline.

Integrates PDF extraction with research database storage and RAG system.
Processes academic papers and makes them available for semantic search.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import logging

# Add scripts directory to path for PDF converter
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts"))

from extract_pdf_papers import extract_paper, paper_to_dict
from .research_database import (
    get_research_connection, 
    init_research_database,
    insert_research_paper,
    get_paper_by_id,
    add_paper_category,
    store_paper_file,
    store_paper_image_blob,
    classify_image_as_plot
)
from .embedding_service import EmbeddingService
from .chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class ResearchPaperIngestion:
    """Pipeline for ingesting research papers into the RAG system."""
    
    def __init__(self, 
                 research_db_path: Optional[Path] = None,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 skip_embeddings: bool = False):
        """Initialize ingestion pipeline.
        
        Args:
            research_db_path: Optional custom research database path.
            chunk_size: Size of text chunks for embeddings.
            chunk_overlap: Overlap between chunks.
            skip_embeddings: Skip embedding generation for faster ingestion.
        """
        self.research_db_path = research_db_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.skip_embeddings = skip_embeddings
        
        # Initialize services (lazy load embedding service if needed)
        self._embedding_service = None
        self.chunking_service = ChunkingService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Initialize research database
        self.research_conn = init_research_database(research_db_path)
    
    @property
    def embedding_service(self):
        """Lazy load embedding service only when needed."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    def ingest_pdf(self, 
                   pdf_path: str, 
                   category: Optional[str] = None,
                   output_dir: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Ingest a single PDF paper.
        
        Args:
            pdf_path: Path to PDF file.
            category: Optional category for the paper.
            output_dir: Optional output directory for extracted assets.
            
        Returns:
            Tuple of (paper_id, extraction_results).
        """
        logger.info(f"Ingesting PDF: {pdf_path}")
        
        # Set default output directory
        if output_dir is None:
            output_dir = str(Path(".workspace") / "research_papers" / "extracted")
        
        try:
            # Extract paper content
            paper = extract_paper(pdf_path, output_dir)
            paper_dict = paper_to_dict(paper)
            
            # Insert into research database
            paper_id = insert_research_paper(self.research_conn, paper_dict)
            logger.info(f"Inserted paper with ID: {paper_id}")
            
            # Add category if provided
            if category:
                add_paper_category(self.research_conn, paper_id, category)
                logger.info(f"Added category '{category}' to paper {paper_id}")
            
            # Store original PDF as BLOB
            try:
                store_paper_file(self.research_conn, paper_id, pdf_path, "pdf", True)
                logger.info(f"Stored PDF file for paper {paper_id}")
            except Exception as e:
                logger.warning(f"Failed to store PDF file: {e}")
            
            # Store images as BLOBs
            self._store_images_as_blobs(paper_id, paper_dict)
            
            # Process chunks and embeddings
            self._process_paper_chunks(paper_id, paper_dict)
            
            return paper_id, {
                "status": "success",
                "paper_id": paper_id,
                "title": paper.metadata.title,
                "pages": paper.page_count,
                "words": paper.word_count,
                "images": len(paper.images),
                "tables": len(paper.tables)
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF {pdf_path}: {e}")
            return "", {
                "status": "error",
                "error": str(e),
                "pdf_path": pdf_path
            }
    
    def ingest_batch(self, 
                     pdf_paths: List[str], 
                     category: Optional[str] = None,
                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a batch of PDF papers.
        
        Args:
            pdf_paths: List of PDF file paths.
            category: Optional category for all papers.
            output_dir: Optional output directory.
            
        Returns:
            Batch processing results.
        """
        logger.info(f"Starting batch ingestion of {len(pdf_paths)} papers")
        
        results = {
            "total": len(pdf_paths),
            "successful": [],
            "failed": [],
            "summary": {}
        }
        
        for pdf_path in pdf_paths:
            paper_id, result = self.ingest_pdf(pdf_path, category, output_dir)
            
            if result["status"] == "success":
                results["successful"].append({
                    "paper_id": paper_id,
                    "pdf_path": pdf_path,
                    **result
                })
            else:
                results["failed"].append({
                    "pdf_path": pdf_path,
                    **result
                })
        
        results["summary"] = {
            "success_count": len(results["successful"]),
            "failure_count": len(results["failed"]),
            "success_rate": len(results["successful"]) / len(pdf_paths) if pdf_paths else 0
        }
        
        logger.info(f"Batch ingestion complete: {results['summary']}")
        return results
    
    def _process_paper_chunks(self, paper_id: str, paper_dict: Dict[str, Any]) -> None:
        """Process paper content into chunks and generate embeddings.
        
        Args:
            paper_id: Paper ID in database.
            paper_dict: Paper data dictionary.
        """
        logger.info(f"Processing chunks for paper {paper_id}")
        
        # Get full text content
        full_text = paper_dict.get("full_text_preview", "")
        if not full_text:
            logger.warning(f"No full text available for paper {paper_id}")
            return
        
        # Create chunks
        chunks = self.chunking_service.chunk_text(full_text)
        logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
        
        # Insert chunks into research database
        for i, chunk in enumerate(chunks):
            chunk_id = self._insert_paper_chunk(
                paper_id, i, chunk.content, 
                chunk.start_char, chunk.end_char, chunk.token_count
            )
            
            # Generate and store embedding (unless skipped)
            if not self.skip_embeddings:
                try:
                    embedding_result = self.embedding_service.embed(chunk.content)
                    self._insert_paper_embedding(chunk_id, embedding_result.vector)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {chunk_id}: {e}")
        
        # Process abstract separately if available
        abstract = paper_dict.get("metadata", {}).get("abstract")
        if abstract:
            self._process_special_section(paper_id, "abstract", abstract)
        
        # Process sections
        sections = paper_dict.get("sections", {})
        for section_name, section_content in sections.items():
            if section_content and len(section_content.strip()) > 50:
                self._process_special_section(paper_id, section_name, section_content)
    
    def _process_special_section(self, paper_id: str, section_name: str, content: str) -> None:
        """Process a special section (abstract, conclusion, etc.) with dedicated chunks.
        
        Args:
            paper_id: Paper ID.
            section_name: Name of the section.
            content: Section content.
        """
        # Create smaller chunks for important sections
        section_chunks = self.chunking_service.chunk_text(
            content, 
            chunk_size=min(500, self.chunk_size),
            chunk_overlap=100
        )
        
        for i, chunk in enumerate(section_chunks):
            chunk_id = self._insert_paper_chunk(
                paper_id, f"{section_name}_{i}", chunk.content,
                chunk.start_char, chunk.end_char, chunk.token_count,
                chunk_type=section_name.lower()
            )
            
            if not self.skip_embeddings:
                try:
                    embedding_result = self.embedding_service.embed(chunk.content)
                    self._insert_paper_embedding(chunk_id, embedding_result.vector)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for {section_name} chunk: {e}")
    
    def _insert_paper_chunk(self, 
                           paper_id: str, 
                           chunk_index: Any, 
                           content: str,
                           start_char: int, 
                           end_char: int, 
                           token_count: int,
                           chunk_type: str = "text") -> int:
        """Insert a paper chunk into the database.
        
        Args:
            paper_id: Paper ID.
            chunk_index: Chunk index.
            content: Chunk content.
            start_char: Start character position.
            end_char: End character position.
            token_count: Token count.
            chunk_type: Type of chunk.
            
        Returns:
            Chunk ID.
        """
        cursor = self.research_conn.execute("""
            INSERT INTO paper_chunks (
                paper_id, chunk_index, content, start_char, end_char, 
                token_count, chunk_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (paper_id, str(chunk_index), content, start_char, end_char, 
              token_count, chunk_type))
        
        self.research_conn.commit()
        return cursor.lastrowid
    
    def _insert_paper_embedding(self, chunk_id: int, embedding: List[float]) -> None:
        """Insert embedding for a paper chunk.
        
        Args:
            chunk_id: Chunk ID.
            embedding: Embedding vector.
        """
        # Convert embedding to blob
        embedding_blob = self.embedding_service.vector_to_blob(embedding)
        
        self.research_conn.execute("""
            INSERT OR REPLACE INTO paper_embeddings (
                chunk_id, vector, model, dimensions
            ) VALUES (?, ?, ?, ?)
        """, (chunk_id, embedding_blob, 
              self.embedding_service._model_name or "unknown", len(embedding)))
        
        self.research_conn.commit()
    
    def _store_images_as_blobs(self, paper_id: str, paper_dict: Dict[str, Any]) -> None:
        """Store extracted images as BLOBs in the database.
        
        Args:
            paper_id: Paper ID in database.
            paper_dict: Paper data dictionary with image information.
        """
        logger.info(f"Storing images as BLOBs for paper {paper_id}")
        
        images = paper_dict.get("images", [])
        if not images:
            logger.info(f"No images found for paper {paper_id}")
            return
        
        stored_count = 0
        for img in images:
            try:
                image_path = img.get("image_path")
                if not image_path or not Path(image_path).exists():
                    logger.warning(f"Image file not found: {image_path}")
                    continue
                
                # Classify image as plot or regular image
                is_plot, plot_type = classify_image_as_plot(image_path)
                
                # Store image as BLOB
                store_paper_image_blob(
                    self.research_conn,
                    paper_id,
                    image_path,
                    img.get("page_number", 0),
                    img.get("image_index", 0),
                    img.get("width", 0),
                    img.get("height", 0),
                    img.get("caption"),
                    is_plot,
                    plot_type
                )
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to store image {img.get('image_path', 'unknown')}: {e}")
        
        logger.info(f"Stored {stored_count}/{len(images)} images as BLOBs for paper {paper_id}")
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion pipeline statistics.
        
        Returns:
            Statistics dictionary.
        """
        cursor = self.research_conn.execute("""
            SELECT 
                COUNT(*) as total_papers,
                COUNT(DISTINCT pc.paper_id) as papers_with_chunks,
                COUNT(pc.id) as total_chunks,
                COUNT(pe.id) as total_embeddings,
                AVG(p.word_count) as avg_word_count,
                AVG(p.page_count) as avg_page_count
            FROM research_papers p
            LEFT JOIN paper_chunks pc ON p.id = pc.paper_id
            LEFT JOIN paper_embeddings pe ON pc.id = pe.chunk_id
        """)
        
        stats = dict(cursor.fetchone())
        
        # Get category distribution
        cursor = self.research_conn.execute("""
            SELECT category, COUNT(*) as count
            FROM paper_categories
            GROUP BY category
            ORDER BY count DESC
        """)
        stats["categories"] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def close(self) -> None:
        """Close database connections."""
        if self.research_conn:
            self.research_conn.close()


def ingest_paper_cli(pdf_path: str, 
                    category: Optional[str] = None,
                    output_dir: Optional[str] = None) -> None:
    """CLI function to ingest a single paper.
    
    Args:
        pdf_path: Path to PDF file.
        category: Optional category.
        output_dir: Optional output directory.
    """
    ingestion = ResearchPaperIngestion()
    
    try:
        paper_id, result = ingestion.ingest_pdf(pdf_path, category, output_dir)
        
        if result["status"] == "success":
            print(f"✓ Successfully ingested paper: {paper_id}")
            print(f"  Title: {result.get('title', 'Unknown')}")
            print(f"  Pages: {result.get('pages', 0)}")
            print(f"  Words: {result.get('words', 0):,}")
            print(f"  Images: {result.get('images', 0)}")
            print(f"  Tables: {result.get('tables', 0)}")
            if category:
                print(f"  Category: {category}")
        else:
            print(f"✗ Failed to ingest paper: {result.get('error', 'Unknown error')}")
            
    finally:
        ingestion.close()


def ingest_batch_cli(pdf_paths: List[str], 
                    category: Optional[str] = None,
                    output_dir: Optional[str] = None) -> None:
    """CLI function to ingest a batch of papers.
    
    Args:
        pdf_paths: List of PDF file paths.
        category: Optional category for all papers.
        output_dir: Optional output directory.
    """
    ingestion = ResearchPaperIngestion()
    
    try:
        results = ingestion.ingest_batch(pdf_paths, category, output_dir)
        
        print(f"\nBatch Ingestion Results:")
        print(f"Total papers: {results['total']}")
        print(f"Successful: {results['summary']['success_count']}")
        print(f"Failed: {results['summary']['failure_count']}")
        print(f"Success rate: {results['summary']['success_rate']:.1%}")
        
        if results["failed"]:
            print(f"\nFailed papers:")
            for failure in results["failed"]:
                print(f"  ✗ {failure['pdf_path']}: {failure.get('error', 'Unknown error')}")
        
        print(f"\nIngestion statistics:")
        stats = ingestion.get_ingestion_stats()
        print(f"  Total papers in database: {stats['total_papers']}")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Total embeddings: {stats['total_embeddings']}")
        
    finally:
        ingestion.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Paper Ingestion Pipeline")
    parser.add_argument("pdf_paths", nargs="+", help="PDF file paths to ingest")
    parser.add_argument("--category", "-c", help="Category for the papers")
    parser.add_argument("--output-dir", "-o", help="Output directory for extracted assets")
    parser.add_argument("--batch", "-b", action="store_true", 
                       help="Process as batch (default for multiple files)")
    
    args = parser.parse_args()
    
    if len(args.pdf_paths) == 1 and not args.batch:
        ingest_paper_cli(args.pdf_paths[0], args.category, args.output_dir)
    else:
        ingest_batch_cli(args.pdf_paths, args.category, args.output_dir)
