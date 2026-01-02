"""Artifact Processor - Quick summarization and archival for markdown files.

Provides:
- Batch processing of markdown files from Downloads or any directory
- Automatic metadata extraction (title, type, tags, relationships)
- AI-powered summarization with key insights extraction
- RAG-optimized chunking and indexing
- Database archival with full-text and vector search support
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_dev_orchestrator.knowledge.database import get_connection
from ai_dev_orchestrator.knowledge.embedding_service import EmbeddingService
from ai_dev_orchestrator.knowledge.chat_record_parser import (
    ChatRecordParser, ChatSession, ConversationInsights, DiscConversationLogEntry
)
from ai_dev_orchestrator.llm.service import generate_structured, is_available
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Extracted metadata from a markdown file."""
    title: str
    doc_type: str
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    key_insights: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high, critical
    estimated_tokens: int = 0


@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    file_path: Path
    doc_id: str
    success: bool
    metadata: Optional[FileMetadata] = None
    error: Optional[str] = None
    chunks_created: int = 0
    embeddings_created: int = 0
    chat_session: Optional[ChatSession] = None
    conversation_insights: Optional[ConversationInsights] = None
    disc_log_entry: Optional[DiscConversationLogEntry] = None
    copyable_snippets: Optional[Dict[str, str]] = None


class MetadataExtractor:
    """Extract metadata and insights from markdown content using AI."""
    
    class DocumentAnalysis(BaseModel):
        title: str
        doc_type: str  # adr, spec, discussion, plan, session, migration, refactor, etc.
        tags: List[str]
        summary: str
        key_insights: List[str]
        relationships: List[str]  # Related documents or concepts
        priority: str  # low, medium, high, critical
    
    def extract_metadata(self, content: str, file_path: Path) -> FileMetadata:
        """Extract metadata from markdown content using AI analysis."""
        if not is_available():
            return self._fallback_extraction(content, file_path)
        
        try:
            # Truncate content for analysis (first 2000 chars for efficiency)
            analysis_content = content[:2000] + "..." if len(content) > 2000 else content
            
            prompt = f"""Analyze this markdown document and extract metadata:

DOCUMENT CONTENT:
{analysis_content}

FILE PATH: {file_path}

Extract the following information:
- title: Clear, descriptive title (if not in content, infer from filename/content)
- doc_type: Document type (adr, spec, discussion, plan, session, migration, refactor, guide, etc.)
- tags: Relevant tags for categorization (3-8 tags)
- summary: 2-3 sentence summary of the document's purpose and content
- key_insights: 3-5 key insights, decisions, or important points
- relationships: Related documents, systems, or concepts mentioned
- priority: Importance level (low, medium, high, critical)

Focus on extracting actionable information for RAG retrieval."""

            response = generate_structured(
                prompt=prompt,
                schema=self.DocumentAnalysis,
                system_prompt="You are a technical document analyzer specializing in software development artifacts."
            )
            
            if response.success and response.data:
                data = response.data
                return FileMetadata(
                    title=data.get("title", file_path.stem),
                    doc_type=data.get("doc_type", "document"),
                    tags=data.get("tags", []),
                    summary=data.get("summary", ""),
                    key_insights=data.get("key_insights", []),
                    relationships=data.get("relationships", []),
                    priority=data.get("priority", "medium"),
                    estimated_tokens=len(content) // 4
                )
            
        except Exception as e:
            logger.warning(f"AI metadata extraction failed for {file_path}: {e}")
        
        return self._fallback_extraction(content, file_path)
    
    def _fallback_extraction(self, content: str, file_path: Path) -> FileMetadata:
        """Fallback metadata extraction using regex patterns."""
        lines = content.split('\n')
        
        # Extract title (first # heading or filename)
        title = file_path.stem
        for line in lines[:10]:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Infer doc_type from filename/content
        doc_type = "document"
        filename_lower = file_path.name.lower()
        if "adr" in filename_lower or "decision" in filename_lower:
            doc_type = "adr"
        elif "spec" in filename_lower or "specification" in filename_lower:
            doc_type = "spec"
        elif "discussion" in filename_lower or "disc" in filename_lower:
            doc_type = "discussion"
        elif "plan" in filename_lower:
            doc_type = "plan"
        elif "session" in filename_lower:
            doc_type = "session"
        elif "migration" in filename_lower or "migrate" in filename_lower:
            doc_type = "migration"
        elif "refactor" in filename_lower:
            doc_type = "refactor"
        
        # Extract basic tags from content
        tags = []
        content_lower = content.lower()
        tag_patterns = [
            r'\b(react|vue|angular|frontend|ui|ux)\b',
            r'\b(backend|api|database|server)\b',
            r'\b(migration|refactor|architecture|design)\b',
            r'\b(documentation|guide|tutorial)\b'
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, content_lower)
            tags.extend(matches)
        
        tags = list(set(tags))[:8]  # Limit to 8 unique tags
        
        return FileMetadata(
            title=title,
            doc_type=doc_type,
            tags=tags,
            summary=f"Document extracted from {file_path.name}",
            key_insights=[],
            relationships=[],
            priority="medium",
            estimated_tokens=len(content) // 4
        )


class ChunkProcessor:
    """Process documents into RAG-optimized chunks."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize chunk processor.
        
        Args:
            chunk_size: Target chunk size in characters.
            overlap: Overlap between chunks in characters.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def create_chunks(self, content: str, doc_id: str) -> List[Dict[str, Any]]:
        """Create overlapping chunks from document content.
        
        Args:
            content: Document content.
            doc_id: Document identifier.
            
        Returns:
            List of chunk dictionaries ready for database insertion.
        """
        if len(content) <= self.chunk_size:
            return [{
                'doc_id': doc_id,
                'chunk_index': 0,
                'content': content,
                'start_char': 0,
                'end_char': len(content),
                'token_count': len(content) // 4
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings within last 100 chars
                search_start = max(end - 100, start)
                sentence_end = -1
                
                for i in range(end - 1, search_start - 1, -1):
                    if content[i] in '.!?':
                        sentence_end = i + 1
                        break
                
                if sentence_end > start:
                    end = sentence_end
            
            chunk_content = content[start:end].strip()
            if chunk_content:
                chunks.append({
                    'doc_id': doc_id,
                    'chunk_index': chunk_index,
                    'content': chunk_content,
                    'start_char': start,
                    'end_char': end,
                    'token_count': len(chunk_content) // 4
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.overlap, end)
            if start >= len(content):
                break
        
        return chunks


class ArtifactProcessor:
    """Main processor for markdown files to knowledge archive."""
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """Initialize artifact processor.
        
        Args:
            embedding_service: Optional embedding service. Creates new if not provided.
        """
        self.metadata_extractor = MetadataExtractor()
        self.chunk_processor = ChunkProcessor()
        self.embedding_service = embedding_service or EmbeddingService()
        self.chat_parser = ChatRecordParser()
        self._conn = None
    
    def _get_connection(self):
        """Get database connection."""
        if self._conn is None:
            self._conn = get_connection()
        return self._conn
    
    def _generate_doc_id(self, file_path: Path, content: str) -> str:
        """Generate unique document ID from file path and content hash."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        safe_name = re.sub(r'[^\w\-_]', '_', file_path.stem)
        return f"{safe_name}_{content_hash}"
    
    def _file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection."""
        return hashlib.md5(file_path.read_bytes()).hexdigest()
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        """Process a single markdown file.
        
        Args:
            file_path: Path to markdown file.
            
        Returns:
            ProcessingResult with processing details.
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return ProcessingResult(
                    file_path=file_path,
                    doc_id="",
                    success=False,
                    error="File does not exist or is not a file"
                )
            
            content = file_path.read_text(encoding='utf-8')
            doc_id = self._generate_doc_id(file_path, content)
            file_hash = self._file_hash(file_path)
            
            conn = self._get_connection()
            
            # Check if document already exists and is up-to-date
            existing = conn.execute(
                "SELECT file_hash FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            
            if existing and existing['file_hash'] == file_hash:
                logger.info(f"Document {doc_id} already up-to-date, skipping")
                return ProcessingResult(
                    file_path=file_path,
                    doc_id=doc_id,
                    success=True,
                    error="Already up-to-date"
                )
            
            # Extract metadata
            metadata = self.metadata_extractor.extract_metadata(content, file_path)
            
            # Check if this is a chat record and process it
            chat_session = None
            conversation_insights = None
            disc_log_entry = None
            copyable_snippets = None
            
            if self._is_chat_record(content, file_path):
                try:
                    chat_session = self.chat_parser.parse_chat_record(content, file_path)
                    conversation_insights = self.chat_parser.analyze_conversation(chat_session)
                    disc_log_entry = self.chat_parser.create_disc_log_entry(chat_session, conversation_insights)
                    copyable_snippets = self.chat_parser.extract_copyable_snippets(chat_session, conversation_insights)
                    
                    # Update metadata with chat-specific information
                    if not metadata.doc_type or metadata.doc_type == "document":
                        metadata.doc_type = "chat_record"
                    if not metadata.summary:
                        metadata.summary = conversation_insights.summary
                    if not metadata.tags:
                        metadata.tags = conversation_insights.topics_discussed[:5]
                    
                    logger.info(f"Processed chat record: {chat_session.total_messages} messages, {len(conversation_insights.topics_discussed)} topics")
                    
                except Exception as e:
                    logger.warning(f"Chat record processing failed for {file_path}: {e}")
            
            # Insert/update document
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (id, type, title, content, file_path, file_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (doc_id, metadata.doc_type, metadata.title, content, str(file_path), file_hash))
            
            # Delete existing chunks and embeddings
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            
            # Create chunks
            chunks = self.chunk_processor.create_chunks(content, doc_id)
            chunks_created = 0
            
            for chunk in chunks:
                conn.execute("""
                    INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char, token_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (chunk['doc_id'], chunk['chunk_index'], chunk['content'], 
                     chunk['start_char'], chunk['end_char'], chunk['token_count']))
                chunks_created += 1
            
            conn.commit()
            
            # Generate embeddings for chunks
            embeddings_created = self.embedding_service.embed_all_chunks(conn)
            
            logger.info(f"Processed {file_path}: {chunks_created} chunks, {embeddings_created} embeddings")
            
            return ProcessingResult(
                file_path=file_path,
                doc_id=doc_id,
                success=True,
                metadata=metadata,
                chunks_created=chunks_created,
                embeddings_created=embeddings_created,
                chat_session=chat_session,
                conversation_insights=conversation_insights,
                disc_log_entry=disc_log_entry,
                copyable_snippets=copyable_snippets
            )
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return ProcessingResult(
                file_path=file_path,
                doc_id="",
                success=False,
                error=str(e)
            )
    
    def _is_chat_record(self, content: str, file_path: Path) -> bool:
        """Determine if a file is a chat record."""
        # Check filename patterns
        filename_lower = file_path.name.lower()
        chat_indicators = ['chat', 'conversation', 'cascade', 'session', 'dialogue', 'transcript']
        
        if any(indicator in filename_lower for indicator in chat_indicators):
            return True
        
        # Check content patterns
        format_type = self.chat_parser.detect_format(content)
        return format_type in ['cascade_markdown', 'cascade_json', 'plain_text']
    
    def process_directory(self, directory: Path, pattern: str = "*.md") -> List[ProcessingResult]:
        """Process all markdown files in a directory.
        
        Args:
            directory: Directory to process.
            pattern: File pattern to match.
            
        Returns:
            List of ProcessingResult for each file.
        """
        results = []
        
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory}")
            return results
        
        files = list(directory.glob(pattern))
        logger.info(f"Found {len(files)} files matching {pattern} in {directory}")
        
        for file_path in files:
            result = self.process_file(file_path)
            results.append(result)
        
        return results
    
    def process_file_list(self, file_paths: List[str]) -> List[ProcessingResult]:
        """Process a list of file paths.
        
        Args:
            file_paths: List of file path strings.
            
        Returns:
            List of ProcessingResult for each file.
        """
        results = []
        
        for path_str in file_paths:
            # Handle Windows paths
            path_str = path_str.replace('\\', '/')
            file_path = Path(path_str)
            
            result = self.process_file(file_path)
            results.append(result)
        
        return results


def create_processor() -> ArtifactProcessor:
    """Create a new artifact processor instance."""
    return ArtifactProcessor()


def process_downloads_folder(downloads_path: Optional[str] = None) -> List[ProcessingResult]:
    """Convenience function to process Downloads folder.
    
    Args:
        downloads_path: Optional custom downloads path. Uses default if not provided.
        
    Returns:
        List of ProcessingResult for each processed file.
    """
    if downloads_path:
        downloads_dir = Path(downloads_path)
    else:
        # Try common Downloads locations
        home = Path.home()
        possible_downloads = [
            home / "Downloads",
            home / "downloads", 
            Path("/mnt/c/Users") / Path.home().name / "Downloads"  # WSL
        ]
        
        downloads_dir = None
        for path in possible_downloads:
            if path.exists():
                downloads_dir = path
                break
        
        if not downloads_dir:
            logger.error("Could not find Downloads folder")
            return []
    
    processor = create_processor()
    return processor.process_directory(downloads_dir)
