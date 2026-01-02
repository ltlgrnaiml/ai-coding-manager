"""Research Paper Service for FastAPI Backend.

Provides API endpoints for research paper management and RAG integration.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
import logging

# Add src to path for research modules
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from ai_dev_orchestrator.knowledge.research_rag import ResearchRAGService, ResearchSearchHit
from ai_dev_orchestrator.knowledge.research_database import (
    get_research_connection,
    get_research_stats,
    get_papers_by_category,
    get_paper_by_id,
    get_paper_file,
    get_paper_images
)
from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion

logger = logging.getLogger(__name__)


class ResearchPaperService:
    """Service class for research paper operations."""
    
    def __init__(self):
        """Initialize research paper service."""
        self.rag_service = ResearchRAGService()
        self.ingestion_service = ResearchPaperIngestion()
    
    def search_papers(self, 
                     query: str, 
                     method: str = "hybrid",
                     limit: int = 10,
                     category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search research papers.
        
        Args:
            query: Search query.
            method: Search method (semantic, fulltext, hybrid).
            limit: Maximum results.
            category: Optional category filter.
            
        Returns:
            List of search results.
        """
        try:
            if method == "semantic":
                results = self.rag_service.search_papers_semantic(query, limit, category)
            elif method == "fulltext":
                results = self.rag_service.search_papers_fulltext(query, limit, category)
            else:  # hybrid
                results = self.rag_service.search_papers_hybrid(query, limit, category)
            
            # Convert to dict format for API response
            return [self._search_hit_to_dict(hit) for hit in results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    def get_paper_details(self, 
                         paper_id: str, 
                         query: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a paper.
        
        Args:
            paper_id: Paper ID.
            query: Optional query for relevant chunks.
            
        Returns:
            Paper details.
        """
        try:
            context = self.rag_service.get_paper_context(paper_id, query)
            
            if not context:
                raise HTTPException(status_code=404, detail="Paper not found")
            
            return context
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get paper details: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get paper: {str(e)}")
    
    def get_paper_context_for_rag(self, 
                                 paper_id: str, 
                                 query: str,
                                 max_chunks: int = 3) -> Dict[str, Any]:
        """Get paper context optimized for RAG usage.
        
        Args:
            paper_id: Paper ID.
            query: Query for finding relevant chunks.
            max_chunks: Maximum chunks to return.
            
        Returns:
            RAG-optimized context.
        """
        try:
            context = self.rag_service.get_paper_context(paper_id, query, max_chunks)
            
            if not context:
                return {}
            
            # Format for RAG consumption
            rag_context = {
                "paper_id": paper_id,
                "title": context.get("title", ""),
                "authors": context.get("authors", []),
                "abstract": context.get("abstract", ""),
                "relevant_content": [],
                "metadata": {
                    "arxiv_id": context.get("arxiv_id"),
                    "doi": context.get("doi"),
                    "venue": context.get("venue"),
                    "publication_date": context.get("publication_date"),
                    "categories": context.get("categories", [])
                }
            }
            
            # Add relevant chunks
            for chunk in context.get("relevant_chunks", []):
                rag_context["relevant_content"].append({
                    "content": chunk["content"],
                    "type": chunk["chunk_type"],
                    "relevance": chunk["similarity"]
                })
            
            return rag_context
            
        except Exception as e:
            logger.error(f"Failed to get RAG context: {e}")
            return {}
    
    def list_papers_by_category(self, 
                               category: str, 
                               limit: int = 20) -> List[Dict[str, Any]]:
        """List papers in a category.
        
        Args:
            category: Category name.
            limit: Maximum results.
            
        Returns:
            List of papers.
        """
        try:
            conn = get_research_connection()
            papers = get_papers_by_category(conn, category, limit)
            conn.close()
            
            # Convert to API format
            result = []
            for paper in papers:
                import json
                result.append({
                    "paper_id": paper["id"],
                    "title": paper["title"],
                    "authors": json.loads(paper["authors"] or "[]"),
                    "arxiv_id": paper.get("arxiv_id"),
                    "doi": paper.get("doi"),
                    "venue": paper.get("venue"),
                    "publication_date": paper.get("publication_date"),
                    "confidence": paper["confidence"],
                    "category_source": paper["category_source"]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list papers: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list papers: {str(e)}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get research database statistics.
        
        Returns:
            Database statistics.
        """
        try:
            conn = get_research_connection()
            stats = get_research_stats(conn)
            conn.close()
            
            # Add ingestion stats
            ing_stats = self.ingestion_service.get_ingestion_stats()
            stats.update({
                "processing": {
                    "papers_with_chunks": ing_stats.get("papers_with_chunks", 0),
                    "total_chunks": ing_stats.get("total_chunks", 0),
                    "total_embeddings": ing_stats.get("total_embeddings", 0),
                    "avg_word_count": ing_stats.get("avg_word_count", 0),
                    "avg_page_count": ing_stats.get("avg_page_count", 0)
                }
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
    
    def ingest_paper_from_path(self, 
                              pdf_path: str, 
                              category: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a paper from file path.
        
        Args:
            pdf_path: Path to PDF file.
            category: Optional category.
            
        Returns:
            Ingestion result.
        """
        try:
            paper_id, result = self.ingestion_service.ingest_pdf(pdf_path, category)
            
            return {
                "paper_id": paper_id,
                "status": result["status"],
                "title": result.get("title"),
                "pages": result.get("pages", 0),
                "words": result.get("words", 0),
                "images": result.get("images", 0),
                "tables": result.get("tables", 0),
                "category": category,
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest paper: {e}")
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all available categories.
        
        Returns:
            List of categories with counts.
        """
        try:
            stats = self.get_database_stats()
            return stats.get("categories", [])
            
        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
    
    def get_paper_pdf(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get PDF file for a paper.
        
        Args:
            paper_id: Paper ID.
            
        Returns:
            PDF file data or None if not found.
        """
        try:
            conn = get_research_connection()
            pdf_data = get_paper_file(conn, paper_id, "pdf")
            conn.close()
            return pdf_data
            
        except Exception as e:
            logger.error(f"Failed to get PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get PDF: {str(e)}")
    
    def get_paper_images_list(self, 
                             paper_id: str, 
                             plots_only: bool = False) -> List[Dict[str, Any]]:
        """Get images for a paper.
        
        Args:
            paper_id: Paper ID.
            plots_only: If True, only return plots/graphs.
            
        Returns:
            List of image data (without BLOB data for performance).
        """
        try:
            conn = get_research_connection()
            images = get_paper_images(conn, paper_id, plots_only)
            conn.close()
            
            # Remove BLOB data for list view (performance)
            for img in images:
                img.pop('image_data', None)
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to get images: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get images: {str(e)}")
    
    def get_paper_image_data(self, paper_id: str, image_id: int) -> Optional[Dict[str, Any]]:
        """Get specific image data including BLOB.
        
        Args:
            paper_id: Paper ID.
            image_id: Image ID.
            
        Returns:
            Image data with BLOB or None if not found.
        """
        try:
            conn = get_research_connection()
            cursor = conn.execute("""
                SELECT id, page_number, image_index, width, height, image_data, 
                       mime_type, file_size, caption, is_plot, plot_type, created_at
                FROM paper_images 
                WHERE paper_id = ? AND id = ?
            """, (paper_id, image_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
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
            }
            
        except Exception as e:
            logger.error(f"Failed to get image data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")
    
    def _search_hit_to_dict(self, hit: ResearchSearchHit) -> Dict[str, Any]:
        """Convert ResearchSearchHit to dictionary.
        
        Args:
            hit: Search hit object.
            
        Returns:
            Dictionary representation.
        """
        return {
            "paper_id": hit.paper_id,
            "title": hit.title,
            "authors": hit.authors,
            "abstract": hit.abstract,
            "arxiv_id": hit.arxiv_id,
            "doi": hit.doi,
            "venue": hit.venue,
            "chunk_content": hit.chunk_content,
            "chunk_type": hit.chunk_type,
            "score": hit.score,
            "snippet": hit.snippet,
            "publication_date": hit.publication_date,
            "categories": hit.categories
        }
    
    def close(self):
        """Close service connections."""
        if self.rag_service:
            self.rag_service.close()
        if self.ingestion_service:
            self.ingestion_service.close()


# Global service instance
research_service = ResearchPaperService()
