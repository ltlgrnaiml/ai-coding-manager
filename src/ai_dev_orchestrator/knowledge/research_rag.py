"""Research Paper RAG Integration.

Integrates research paper database with the main RAG system for unified search
and retrieval across both general documents and academic papers.
"""

import sqlite3
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

from .research_database import get_research_connection, search_research_papers
from .search_service import SearchHit
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class ResearchSearchHit:
    """Research paper search result."""
    
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str]
    arxiv_id: Optional[str]
    doi: Optional[str]
    venue: Optional[str]
    chunk_content: str
    chunk_type: str
    score: float
    snippet: Optional[str] = None
    publication_date: Optional[str] = None
    categories: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []


class ResearchRAGService:
    """RAG service for research papers with semantic search capabilities."""
    
    def __init__(self, research_db_path: Optional[str] = None):
        """Initialize research RAG service.
        
        Args:
            research_db_path: Optional path to research database.
        """
        self.research_conn = get_research_connection(research_db_path)
        self.embedding_service = EmbeddingService()
    
    def search_papers_semantic(self, 
                              query: str, 
                              limit: int = 10,
                              category_filter: Optional[str] = None,
                              min_score: float = 0.7) -> List[ResearchSearchHit]:
        """Semantic search across research papers using embeddings.
        
        Args:
            query: Search query.
            limit: Maximum results to return.
            category_filter: Optional category filter.
            min_score: Minimum similarity score.
            
        Returns:
            List of research search hits.
        """
        logger.info(f"Semantic search for: '{query}' (limit={limit})")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed(query).vector
            query_blob = self.embedding_service.vector_to_blob(query_embedding)
            
            # Build SQL query for semantic search
            base_query = """
                SELECT 
                    p.id, p.title, p.authors, p.abstract, p.arxiv_id, p.doi, 
                    p.venue, p.publication_date,
                    pc.content as chunk_content, pc.chunk_type,
                    pe.vector as embedding_blob
                FROM research_papers p
                JOIN paper_chunks pc ON p.id = pc.paper_id
                JOIN paper_embeddings pe ON pc.id = pe.chunk_id
            """
            
            params = []
            
            if category_filter:
                base_query += """
                    JOIN paper_categories pcat ON p.id = pcat.paper_id
                    WHERE pcat.category = ?
                """
                params.append(category_filter)
            
            cursor = self.research_conn.execute(base_query, params)
            results = []
            
            for row in cursor.fetchall():
                # Calculate cosine similarity
                chunk_embedding = self.embedding_service.blob_to_vector(row['embedding_blob'])
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                
                if similarity >= min_score:
                    # Parse authors JSON
                    import json
                    authors = json.loads(row['authors'] or '[]')
                    
                    # Get categories for this paper
                    categories = self._get_paper_categories(row['id'])
                    
                    hit = ResearchSearchHit(
                        paper_id=row['id'],
                        title=row['title'],
                        authors=authors,
                        abstract=row['abstract'],
                        arxiv_id=row['arxiv_id'],
                        doi=row['doi'],
                        venue=row['venue'],
                        chunk_content=row['chunk_content'],
                        chunk_type=row['chunk_type'],
                        score=similarity,
                        publication_date=row['publication_date'],
                        categories=categories
                    )
                    results.append(hit)
            
            # Sort by score and limit
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def search_papers_fulltext(self, 
                              query: str, 
                              limit: int = 10,
                              category_filter: Optional[str] = None) -> List[ResearchSearchHit]:
        """Full-text search across research papers.
        
        Args:
            query: Search query.
            limit: Maximum results to return.
            category_filter: Optional category filter.
            
        Returns:
            List of research search hits.
        """
        logger.info(f"Full-text search for: '{query}' (limit={limit})")
        
        try:
            # Use the existing FTS search
            fts_results = search_research_papers(
                self.research_conn, query, limit, category_filter
            )
            
            hits = []
            for result in fts_results:
                import json
                authors = json.loads(result.get('authors', '[]'))
                categories = self._get_paper_categories(result['id'])
                
                hit = ResearchSearchHit(
                    paper_id=result['id'],
                    title=result['title'],
                    authors=authors,
                    abstract=result.get('abstract'),
                    arxiv_id=result.get('arxiv_id'),
                    doi=result.get('doi'),
                    venue=result.get('venue'),
                    chunk_content=result.get('snippet', ''),
                    chunk_type='fulltext',
                    score=1.0,  # FTS doesn't provide similarity scores
                    snippet=result.get('snippet'),
                    publication_date=result.get('publication_date'),
                    categories=categories
                )
                hits.append(hit)
            
            return hits
            
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            return []
    
    def search_papers_hybrid(self, 
                            query: str, 
                            limit: int = 10,
                            category_filter: Optional[str] = None,
                            semantic_weight: float = 0.7) -> List[ResearchSearchHit]:
        """Hybrid search combining semantic and full-text search.
        
        Args:
            query: Search query.
            limit: Maximum results to return.
            category_filter: Optional category filter.
            semantic_weight: Weight for semantic vs full-text (0.0-1.0).
            
        Returns:
            List of research search hits with combined scores.
        """
        logger.info(f"Hybrid search for: '{query}' (limit={limit})")
        
        # Get results from both methods
        semantic_results = self.search_papers_semantic(
            query, limit * 2, category_filter, min_score=0.5
        )
        fulltext_results = self.search_papers_fulltext(
            query, limit * 2, category_filter
        )
        
        # Combine and re-rank using RRF (Reciprocal Rank Fusion)
        combined_scores = {}
        
        # Add semantic scores
        for i, hit in enumerate(semantic_results):
            key = (hit.paper_id, hit.chunk_content[:100])  # Use content snippet as key
            rrf_score = 1.0 / (60 + i + 1)  # RRF formula
            combined_scores[key] = {
                'hit': hit,
                'semantic_rrf': rrf_score,
                'fulltext_rrf': 0.0,
                'semantic_score': hit.score
            }
        
        # Add full-text scores
        for i, hit in enumerate(fulltext_results):
            key = (hit.paper_id, hit.chunk_content[:100])
            rrf_score = 1.0 / (60 + i + 1)
            
            if key in combined_scores:
                combined_scores[key]['fulltext_rrf'] = rrf_score
            else:
                combined_scores[key] = {
                    'hit': hit,
                    'semantic_rrf': 0.0,
                    'fulltext_rrf': rrf_score,
                    'semantic_score': 0.0
                }
        
        # Calculate final scores and sort
        final_results = []
        for key, data in combined_scores.items():
            hit = data['hit']
            
            # Weighted combination of RRF scores
            final_score = (
                semantic_weight * data['semantic_rrf'] + 
                (1 - semantic_weight) * data['fulltext_rrf']
            )
            
            hit.score = final_score
            final_results.append(hit)
        
        # Sort by final score and return top results
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:limit]
    
    def get_paper_context(self, 
                         paper_id: str, 
                         query: Optional[str] = None,
                         max_chunks: int = 5) -> Dict[str, Any]:
        """Get contextual information from a research paper.
        
        Args:
            paper_id: Paper ID.
            query: Optional query to find most relevant chunks.
            max_chunks: Maximum chunks to return.
            
        Returns:
            Paper context with metadata and relevant chunks.
        """
        # Get paper metadata
        cursor = self.research_conn.execute("""
            SELECT * FROM research_papers WHERE id = ?
        """, (paper_id,))
        
        paper = cursor.fetchone()
        if not paper:
            return {}
        
        import json
        paper_dict = dict(paper)
        paper_dict['authors'] = json.loads(paper_dict['authors'] or '[]')
        paper_dict['keywords'] = json.loads(paper_dict['keywords'] or '[]')
        
        # Get categories
        paper_dict['categories'] = self._get_paper_categories(paper_id)
        
        # Get relevant chunks
        if query:
            # Find most relevant chunks using semantic search
            chunks = self._get_relevant_chunks(paper_id, query, max_chunks)
        else:
            # Get abstract and conclusion chunks if available
            chunks = self._get_key_chunks(paper_id, max_chunks)
        
        paper_dict['relevant_chunks'] = chunks
        
        return paper_dict
    
    def get_citation_context(self, paper_id: str) -> Dict[str, Any]:
        """Get citation context for a paper (citing and cited papers).
        
        Args:
            paper_id: Paper ID.
            
        Returns:
            Citation context with related papers.
        """
        context = {
            'citing_papers': [],
            'cited_papers': []
        }
        
        # Get papers that cite this paper
        cursor = self.research_conn.execute("""
            SELECT p.id, p.title, p.authors, pc.citation_text
            FROM paper_citations pc
            JOIN research_papers p ON pc.citing_paper_id = p.id
            WHERE pc.cited_paper_id = ?
            ORDER BY p.publication_date DESC
        """, (paper_id,))
        
        for row in cursor.fetchall():
            import json
            context['citing_papers'].append({
                'paper_id': row['id'],
                'title': row['title'],
                'authors': json.loads(row['authors'] or '[]'),
                'citation_text': row['citation_text']
            })
        
        # Get papers cited by this paper
        cursor = self.research_conn.execute("""
            SELECT p.id, p.title, p.authors, pc.citation_text
            FROM paper_citations pc
            JOIN research_papers p ON pc.cited_paper_id = p.id
            WHERE pc.citing_paper_id = ?
        """, (paper_id,))
        
        for row in cursor.fetchall():
            import json
            context['cited_papers'].append({
                'paper_id': row['id'],
                'title': row['title'],
                'authors': json.loads(row['authors'] or '[]'),
                'citation_text': row['citation_text']
            })
        
        return context
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector.
            vec2: Second vector.
            
        Returns:
            Cosine similarity score.
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception:
            return 0.0
    
    def _get_paper_categories(self, paper_id: str) -> List[str]:
        """Get categories for a paper.
        
        Args:
            paper_id: Paper ID.
            
        Returns:
            List of category names.
        """
        cursor = self.research_conn.execute("""
            SELECT category FROM paper_categories WHERE paper_id = ?
        """, (paper_id,))
        
        return [row['category'] for row in cursor.fetchall()]
    
    def _get_relevant_chunks(self, 
                           paper_id: str, 
                           query: str, 
                           max_chunks: int) -> List[Dict[str, Any]]:
        """Get most relevant chunks for a query from a specific paper.
        
        Args:
            paper_id: Paper ID.
            query: Search query.
            max_chunks: Maximum chunks to return.
            
        Returns:
            List of relevant chunks.
        """
        try:
            query_embedding = self.embedding_service.embed(query).vector
            
            cursor = self.research_conn.execute("""
                SELECT pc.content, pc.chunk_type, pe.vector
                FROM paper_chunks pc
                JOIN paper_embeddings pe ON pc.id = pe.chunk_id
                WHERE pc.paper_id = ?
            """, (paper_id,))
            
            chunks_with_scores = []
            for row in cursor.fetchall():
                chunk_embedding = self.embedding_service.blob_to_vector(row['vector'])
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                
                chunks_with_scores.append({
                    'content': row['content'],
                    'chunk_type': row['chunk_type'],
                    'similarity': similarity
                })
            
            # Sort by similarity and return top chunks
            chunks_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
            return chunks_with_scores[:max_chunks]
            
        except Exception as e:
            logger.error(f"Failed to get relevant chunks: {e}")
            return []
    
    def _get_key_chunks(self, paper_id: str, max_chunks: int) -> List[Dict[str, Any]]:
        """Get key chunks (abstract, conclusion, etc.) from a paper.
        
        Args:
            paper_id: Paper ID.
            max_chunks: Maximum chunks to return.
            
        Returns:
            List of key chunks.
        """
        # Prioritize certain chunk types
        priority_types = ['abstract', 'conclusion', 'introduction', 'results']
        
        chunks = []
        for chunk_type in priority_types:
            cursor = self.research_conn.execute("""
                SELECT content, chunk_type
                FROM paper_chunks
                WHERE paper_id = ? AND chunk_type = ?
                LIMIT ?
            """, (paper_id, chunk_type, max_chunks - len(chunks)))
            
            for row in cursor.fetchall():
                chunks.append({
                    'content': row['content'],
                    'chunk_type': row['chunk_type'],
                    'similarity': 1.0  # High priority for key sections
                })
            
            if len(chunks) >= max_chunks:
                break
        
        # Fill remaining slots with general text chunks if needed
        if len(chunks) < max_chunks:
            cursor = self.research_conn.execute("""
                SELECT content, chunk_type
                FROM paper_chunks
                WHERE paper_id = ? AND chunk_type = 'text'
                LIMIT ?
            """, (paper_id, max_chunks - len(chunks)))
            
            for row in cursor.fetchall():
                chunks.append({
                    'content': row['content'],
                    'chunk_type': row['chunk_type'],
                    'similarity': 0.8
                })
        
        return chunks[:max_chunks]
    
    def close(self) -> None:
        """Close database connection."""
        if self.research_conn:
            self.research_conn.close()
