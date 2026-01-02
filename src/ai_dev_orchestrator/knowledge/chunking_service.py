"""Text Chunking Service for RAG Systems.

Provides intelligent text chunking with overlap for optimal embedding generation
and retrieval performance.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
import tiktoken


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    
    content: str
    start_char: int
    end_char: int
    token_count: int
    chunk_index: int = 0


class ChunkingService:
    """Service for chunking text into optimal sizes for embeddings."""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 encoding_name: str = "cl100k_base"):
        """Initialize chunking service.
        
        Args:
            chunk_size: Target size of each chunk in tokens.
            chunk_overlap: Number of tokens to overlap between chunks.
            encoding_name: Tokenizer encoding to use.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            # Fallback to simple word-based counting
            self.encoding = None
    
    def chunk_text(self, 
                   text: str, 
                   chunk_size: Optional[int] = None,
                   chunk_overlap: Optional[int] = None) -> List[TextChunk]:
        """Chunk text into overlapping segments.
        
        Args:
            text: Text to chunk.
            chunk_size: Override default chunk size.
            chunk_overlap: Override default overlap.
            
        Returns:
            List of text chunks.
        """
        if not text or not text.strip():
            return []
        
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Try sentence-aware chunking first
        chunks = self._chunk_by_sentences(text, chunk_size, chunk_overlap)
        
        # If sentence chunking fails or produces too few chunks, fall back to simple chunking
        if not chunks or len(chunks) == 1 and len(text) > chunk_size * 2:
            chunks = self._chunk_simple(text, chunk_size, chunk_overlap)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for chunking.
        
        Args:
            text: Raw text.
            
        Returns:
            Cleaned text.
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (common in PDFs)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
        
        # Clean up line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def _chunk_by_sentences(self, 
                           text: str, 
                           chunk_size: int, 
                           chunk_overlap: int) -> List[TextChunk]:
        """Chunk text by sentences to preserve semantic boundaries.
        
        Args:
            text: Text to chunk.
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Overlap size in tokens.
            
        Returns:
            List of text chunks.
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            
            # Check if adding this sentence would exceed chunk size
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence
            test_tokens = self._count_tokens(test_chunk)
            
            if test_tokens <= chunk_size or not current_chunk:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = text.find(sentence)
                i += 1
            else:
                # Current chunk is full, create chunk and start new one
                if current_chunk:
                    chunk_end = current_start + len(current_chunk)
                    chunks.append(TextChunk(
                        content=current_chunk,
                        start_char=current_start,
                        end_char=chunk_end,
                        token_count=self._count_tokens(current_chunk),
                        chunk_index=chunk_index
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, chunk_overlap)
                current_chunk = overlap_text
                current_start = text.find(sentence) if sentence in text else chunk_end
                
                # Don't increment i, try adding the same sentence to new chunk
        
        # Add final chunk if it has content
        if current_chunk:
            chunk_end = current_start + len(current_chunk)
            chunks.append(TextChunk(
                content=current_chunk,
                start_char=current_start,
                end_char=chunk_end,
                token_count=self._count_tokens(current_chunk),
                chunk_index=chunk_index
            ))
        
        return chunks
    
    def _chunk_simple(self, 
                     text: str, 
                     chunk_size: int, 
                     chunk_overlap: int) -> List[TextChunk]:
        """Simple character-based chunking as fallback.
        
        Args:
            text: Text to chunk.
            chunk_size: Target chunk size in tokens.
            chunk_overlap: Overlap size in tokens.
            
        Returns:
            List of text chunks.
        """
        # Estimate characters per token (rough approximation)
        chars_per_token = 4
        chunk_chars = chunk_size * chars_per_token
        overlap_chars = chunk_overlap * chars_per_token
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_chars, len(text))
            
            # Try to break at word boundary
            if end < len(text):
                # Look for word boundary within last 100 characters
                boundary_search = text[max(end - 100, start):end]
                last_space = boundary_search.rfind(' ')
                if last_space > 0:
                    end = max(end - 100, start) + last_space
            
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append(TextChunk(
                    content=chunk_text.strip(),
                    start_char=start,
                    end_char=end,
                    token_count=self._count_tokens(chunk_text),
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + chunk_chars - overlap_chars, end)
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Text to split.
            
        Returns:
            List of sentences.
        """
        # Simple sentence splitting - can be improved with NLTK/spaCy
        sentence_endings = r'[.!?]+(?:\s+|$)'
        sentences = re.split(sentence_endings, text)
        
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get overlap text from the end of a chunk.
        
        Args:
            text: Source text.
            overlap_tokens: Number of tokens for overlap.
            
        Returns:
            Overlap text.
        """
        if not text or overlap_tokens <= 0:
            return ""
        
        # Split into words and take last N words as approximation
        words = text.split()
        overlap_words = min(overlap_tokens, len(words))
        
        return " ".join(words[-overlap_words:]) if overlap_words > 0 else ""
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text.
        
        Args:
            text: Text to count.
            
        Returns:
            Token count.
        """
        if not text:
            return 0
        
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception:
                pass
        
        # Fallback: approximate token count
        # Rough approximation: 1 token ≈ 0.75 words
        word_count = len(text.split())
        return int(word_count / 0.75)
    
    def get_chunk_stats(self, chunks: List[TextChunk]) -> dict:
        """Get statistics about a list of chunks.
        
        Args:
            chunks: List of chunks to analyze.
            
        Returns:
            Statistics dictionary.
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_tokens": 0,
                "avg_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0
            }
        
        token_counts = [chunk.token_count for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts)
        }
