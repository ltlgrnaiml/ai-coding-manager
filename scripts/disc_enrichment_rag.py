#!/usr/bin/env python3
"""DISC Enrichment RAG - Context Mining for Discussion Documents.

Searches all AIKH databases (research.db, chatlogs.db, artifacts.db) and workspace
documents to find relevant context for each DISC document, building evidence chains
and provenance metadata.

Optimized for Apple Silicon M4 Max using MPS acceleration.

Usage:
    python scripts/disc_enrichment_rag.py [--disc DISC-0002] [--threshold 0.6] [--dry-run]
    python scripts/disc_enrichment_rag.py --all  # Process all DISCs

Architecture:
    1. Load DISC documents from .discussions/
    2. Extract key concepts, topics, and search queries from each DISC
    3. Search all databases using semantic similarity (embeddings) + lexical matching
    4. Build evidence chains linking concepts to source materials
    5. Generate provenance metadata as YAML frontmatter additions
    6. Optionally update DISCs with enriched context sections

Databases Searched:
    - ~/.aikh/research.db: Academic papers (25+ papers, 3000+ chunks)
    - ~/.aikh/chatlogs.db: AI conversation history (49+ logs, 2000+ turns)
    - ~/.aikh/artifacts.db: Workspace artifacts (ADRs, specs, docs)
    - Workspace files: .archive/, .sessions/, .chat_logs/, concept_graph.json
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import yaml

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    print("⚠️  sentence-transformers not available. Install with: pip install sentence-transformers")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
RESEARCH_DB = AIKH_HOME / "research.db"
CHATLOGS_DB = AIKH_HOME / "chatlogs.db"
ARTIFACTS_DB = AIKH_HOME / "artifacts.db"

WORKSPACE_ROOT = Path(__file__).parent.parent
DISCUSSIONS_DIR = WORKSPACE_ROOT / ".discussions"
ARCHIVE_DIR = WORKSPACE_ROOT / ".archive"
SESSIONS_DIR = WORKSPACE_ROOT / ".sessions"
CHAT_LOGS_DIR = WORKSPACE_ROOT / ".chat_logs"

# Similarity thresholds
DEFAULT_SEMANTIC_THRESHOLD = 0.55  # Lower = more results, higher = stricter
DEFAULT_TOP_K = 15  # Max results per source

# Key concepts to look for in DISC documents
AICM_CONCEPTS = {
    'uam': ['unified artifact model', 'uam', 'artifact chain', 'traceability', 'schema'],
    'aikh': ['ai knowledge hub', 'aikh', 'knowledge base', 'context', 'retrieval'],
    'p2re': ['prompt response', 'p2re', 'observability', 'trace', 'evaluation', 'lessons'],
    'tap_in': ['tap-in', 'tap in', 'session handoff', 'context serialization', 'warm-up'],
    'rainstorm': ['rainstorm', 'workflow', 'umbrella disc', 'nested', 'auto-discovery'],
    'splan': ['splan', 'super plan', 'orchestration', 'git branch', 'integration gate'],
    'quality': ['quality score', 'rubric', 'llm judge', 'calibration', 'feedback'],
    'artifact_gen': ['artifact generation', 'pipeline', 'prompt template', 'validation gate'],
    'chat': ['chat integration', 'streaming', 'tool calling', 'mcp', 'context injection'],
    'rag': ['retrieval augmented', 'rag', 'embedding', 'vector search', 'semantic'],
    'agent': ['agent', 'agentic', 'autonomous', 'tool use', 'function calling'],
    'llm': ['large language model', 'llm', 'gpt', 'claude', 'transformer'],
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EvidenceItem:
    """A piece of evidence linking to source material."""
    source_db: str  # 'research', 'chatlogs', 'artifacts', 'workspace'
    source_id: str
    source_type: str  # 'paper', 'chat_message', 'document', 'file'
    title: str
    snippet: str  # Relevant excerpt
    similarity_score: float
    match_type: str  # 'semantic', 'lexical', 'citation'
    concepts_matched: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProvenanceRecord:
    """Provenance metadata for a DISC document."""
    disc_id: str
    disc_title: str
    enrichment_date: str
    evidence_count: int
    sources_searched: List[str]
    key_concepts: List[str]
    evidence_chain: List[EvidenceItem]
    semantic_neighbors: List[Dict[str, Any]]  # Related DISCs/docs
    confidence_score: float


@dataclass 
class DISCDocument:
    """Parsed DISC document."""
    file_path: Path
    disc_id: str
    title: str
    content: str
    frontmatter: Dict[str, Any]
    sections: Dict[str, str]
    key_concepts: List[str]
    embedding: Optional[np.ndarray] = None


# =============================================================================
# Device Detection (Apple Silicon Optimized)
# =============================================================================

def get_device() -> str:
    """Detect the best device for ML inference."""
    if not TORCH_AVAILABLE:
        return "cpu"
    
    # Check for MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("🍎 Using Apple Silicon MPS acceleration")
        return "mps"
    
    # Check for CUDA
    if torch.cuda.is_available():
        print(f"🎮 Using CUDA: {torch.cuda.get_device_name(0)}")
        return "cuda"
    
    print("💻 Using CPU")
    return "cpu"


# =============================================================================
# Database Utilities
# =============================================================================

def get_connection(db_path: Path) -> Optional[sqlite3.Connection]:
    """Get database connection if database exists."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_embedding_blob(blob: bytes) -> np.ndarray:
    """Load embedding from SQLite blob."""
    if blob is None:
        return None
    n_floats = len(blob) // 4
    return np.array(struct.unpack(f'{n_floats}f', blob))


def embedding_to_blob(embedding: np.ndarray) -> bytes:
    """Convert numpy embedding to SQLite blob."""
    return struct.pack(f'{len(embedding)}f', *embedding.tolist())


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


# =============================================================================
# DISC Document Parser
# =============================================================================

def parse_disc_document(file_path: Path) -> Optional[DISCDocument]:
    """Parse a DISC markdown document."""
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding='utf-8')
    
    # Extract DISC ID from filename
    disc_id_match = re.match(r'(DISC-\d{4})', file_path.name)
    disc_id = disc_id_match.group(1) if disc_id_match else file_path.stem
    
    # Extract title from first heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else disc_id
    
    # Parse frontmatter (blockquote style used in DISCs)
    frontmatter = {}
    fm_pattern = r'>\s*\*\*([^*]+)\*\*:\s*`?([^`\n]+)`?'
    for match in re.finditer(fm_pattern, content):
        key = match.group(1).strip().lower().replace(' ', '_')
        frontmatter[key] = match.group(2).strip()
    
    # Extract sections
    sections = {}
    section_pattern = r'^##\s+(.+)$'
    current_section = "intro"
    current_content = []
    
    for line in content.split('\n'):
        section_match = re.match(section_pattern, line)
        if section_match:
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = section_match.group(1).strip().lower().replace(' ', '_')
            current_content = []
        else:
            current_content.append(line)
    
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # Extract key concepts from content
    key_concepts = extract_concepts(content)
    
    return DISCDocument(
        file_path=file_path,
        disc_id=disc_id,
        title=title,
        content=content,
        frontmatter=frontmatter,
        sections=sections,
        key_concepts=key_concepts
    )


def extract_concepts(text: str) -> List[str]:
    """Extract key concepts from text using pattern matching."""
    text_lower = text.lower()
    found_concepts = []
    
    for concept_key, patterns in AICM_CONCEPTS.items():
        for pattern in patterns:
            if pattern in text_lower:
                found_concepts.append(concept_key)
                break
    
    return list(set(found_concepts))


def generate_search_queries(disc: DISCDocument) -> List[str]:
    """Generate search queries from DISC document."""
    queries = []
    
    # Use title
    queries.append(disc.title)
    
    # Use delegation scope if present
    if 'delegation_scope' in disc.frontmatter:
        queries.append(disc.frontmatter['delegation_scope'])
    
    # Use summary section if present
    if 'summary' in disc.sections:
        # Take first paragraph of summary
        summary = disc.sections['summary'].strip()
        first_para = summary.split('\n\n')[0][:500]
        queries.append(first_para)
    
    # Add concept-based queries
    for concept in disc.key_concepts:
        if concept in AICM_CONCEPTS:
            queries.append(' '.join(AICM_CONCEPTS[concept][:3]))
    
    return queries


# =============================================================================
# Embedding Model
# =============================================================================

class EmbeddingModel:
    """Embedding model with Apple Silicon optimization."""
    
    MODEL_NAME = 'all-mpnet-base-v2'  # 768 dims, good quality
    
    def __init__(self, device: str = None):
        self.device = device or get_device()
        self._model = None
    
    def _load_model(self):
        if self._model is None and EMBEDDER_AVAILABLE:
            print(f"📦 Loading embedding model on {self.device}...")
            self._model = SentenceTransformer(self.MODEL_NAME, device=self.device)
            print("✅ Model loaded")
    
    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for single text."""
        self._load_model()
        if self._model is None:
            return None
        return self._model.encode(text, normalize_embeddings=True)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        if self._model is None:
            return [None] * len(texts)
        return self._model.encode(texts, normalize_embeddings=True, batch_size=batch_size)


# =============================================================================
# Database Searchers
# =============================================================================

class ResearchDBSearcher:
    """Search research.db for relevant papers using multi-signal matching.
    
    Matching Signals (all contribute to final score):
    1. Semantic similarity (embedding cosine distance) - captures conceptual relevance
    2. Keyword overlap (explicit keywords field) - domain terminology alignment
    3. Author matching (for related work chains) - academic provenance
    4. Venue/conference matching - field relevance indicator
    5. Lexical content matching - direct term overlap in title/abstract
    """
    
    def __init__(self, embedding_model: EmbeddingModel):
        self.model = embedding_model
        self.conn = get_connection(RESEARCH_DB)
    
    def _compute_keyword_score(self, paper_keywords: str, query_keywords: List[str]) -> float:
        """Compute keyword overlap score between paper and query."""
        if not paper_keywords:
            return 0.0
        paper_kw_lower = paper_keywords.lower()
        matches = sum(1 for kw in query_keywords if kw.lower() in paper_kw_lower)
        return matches / max(len(query_keywords), 1)
    
    def _compute_author_score(self, authors: str, known_authors: List[str]) -> float:
        """Compute author relevance (for tracking academic lineage)."""
        if not authors or not known_authors:
            return 0.0
        authors_lower = authors.lower()
        matches = sum(1 for a in known_authors if a.lower() in authors_lower)
        return min(matches / max(len(known_authors), 1), 1.0)
    
    def _compute_venue_score(self, venue: str, target_venues: List[str]) -> float:
        """Compute venue/conference relevance."""
        if not venue:
            return 0.0
        venue_lower = venue.lower()
        # Top AI/ML venues get bonus
        premium_venues = ['neurips', 'icml', 'iclr', 'acl', 'emnlp', 'cvpr', 'aaai', 'arxiv']
        for pv in premium_venues:
            if pv in venue_lower:
                return 0.3  # Bonus for recognized venue
        return 0.1 if venue else 0.0
    
    def _compute_lexical_score(self, text: str, query_terms: List[str]) -> float:
        """Compute direct term overlap in content."""
        if not text:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term.lower() in text_lower)
        return matches / max(len(query_terms), 1)
    
    def search(self, query: str, query_embedding: np.ndarray, 
               threshold: float, top_k: int) -> List[EvidenceItem]:
        """Search research papers using multi-signal scoring.
        
        Final score is a weighted combination of:
        - 50% semantic similarity (embedding match)
        - 20% keyword overlap (explicit metadata)
        - 15% lexical match (title + abstract text)
        - 10% venue relevance (conference prestige)
        - 5% author chain (academic provenance)
        """
        if self.conn is None:
            return []
        
        results = []
        query_terms = [t for t in query.lower().split() if len(t) > 2]
        
        # Load all papers with full metadata
        try:
            papers = self.conn.execute("""
                SELECT p.id, p.title, p.abstract, p.authors, p.venue, 
                       p.keywords, p.arxiv_id, p.doi, p.publication_date,
                       p.word_count, p.page_count
                FROM research_papers p
            """).fetchall()
        except sqlite3.OperationalError:
            return []
        
        # Load paper-level embeddings from summary table
        paper_embeddings = {}
        try:
            for row in self.conn.execute("""
                SELECT paper_id, vector FROM paper_summary_embeddings
                WHERE vector IS NOT NULL
            """):
                emb = load_embedding_blob(row['vector'])
                if emb is not None:
                    paper_embeddings[row['paper_id']] = emb
        except sqlite3.OperationalError:
            pass
        
        # Also try chunk embeddings as fallback
        if not paper_embeddings:
            try:
                for row in self.conn.execute("""
                    SELECT c.paper_id, e.vector 
                    FROM paper_embeddings e
                    JOIN paper_chunks c ON e.chunk_id = c.id
                    WHERE e.vector IS NOT NULL
                    GROUP BY c.paper_id
                """):
                    emb = load_embedding_blob(row['vector'])
                    if emb is not None:
                        paper_embeddings[row['paper_id']] = emb
            except sqlite3.OperationalError:
                pass
        
        for paper in papers:
            paper_id = paper['id']
            
            # 1. Semantic similarity (50% weight)
            semantic_score = 0.0
            if query_embedding is not None and paper_id in paper_embeddings:
                db_emb = paper_embeddings[paper_id]
                if len(db_emb) == len(query_embedding):
                    semantic_score = cosine_similarity(query_embedding, db_emb)
            
            # 2. Keyword overlap (20% weight)
            keyword_score = self._compute_keyword_score(paper['keywords'], query_terms)
            
            # 3. Lexical match in title + abstract (15% weight)
            combined_text = f"{paper['title']} {paper['abstract'] or ''}"
            lexical_score = self._compute_lexical_score(combined_text, query_terms)
            
            # 4. Venue relevance (10% weight)
            venue_score = self._compute_venue_score(paper['venue'], [])
            
            # 5. Author chain (5% weight) - placeholder for future author tracking
            author_score = 0.0
            
            # Weighted combination
            final_score = (
                0.50 * semantic_score +
                0.20 * keyword_score +
                0.15 * lexical_score +
                0.10 * venue_score +
                0.05 * author_score
            )
            
            # Determine primary match type
            if semantic_score > 0.5:
                match_type = 'semantic'
            elif keyword_score > 0.3:
                match_type = 'keyword'
            elif lexical_score > 0.3:
                match_type = 'lexical'
            else:
                match_type = 'mixed'
            
            if final_score >= threshold * 0.5:  # Lower threshold for multi-signal
                results.append(EvidenceItem(
                    source_db='research',
                    source_id=paper_id,
                    source_type='paper',
                    title=paper['title'],
                    snippet=paper['abstract'][:300] if paper['abstract'] else '',
                    similarity_score=final_score,
                    match_type=match_type,
                    metadata={
                        'arxiv_id': paper['arxiv_id'],
                        'doi': paper['doi'],
                        'authors': paper['authors'],
                        'venue': paper['venue'],
                        'keywords': paper['keywords'],
                        'publication_date': paper['publication_date'],
                        'scores': {
                            'semantic': round(semantic_score, 3),
                            'keyword': round(keyword_score, 3),
                            'lexical': round(lexical_score, 3),
                            'venue': round(venue_score, 3)
                        }
                    }
                ))
        
        # Sort by final score and dedupe
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        seen = set()
        unique_results = []
        for r in results:
            if r.source_id not in seen:
                seen.add(r.source_id)
                unique_results.append(r)
        
        return unique_results[:top_k]


class ChatlogsDBSearcher:
    """Search chatlogs.db for relevant conversations."""
    
    def __init__(self, embedding_model: EmbeddingModel):
        self.model = embedding_model
        self.conn = get_connection(CHATLOGS_DB)
    
    def search(self, query: str, query_embedding: np.ndarray,
               threshold: float, top_k: int) -> List[EvidenceItem]:
        """Search chat turns by semantic similarity and keywords."""
        if self.conn is None:
            return []
        
        results = []
        
        # Try semantic search using embeddings
        if query_embedding is not None:
            try:
                for row in self.conn.execute("""
                    SELECT e.id, e.turn_id, e.chat_log_id, e.embedding,
                           t.content, t.role, l.title, l.filename
                    FROM chat_embeddings e
                    LEFT JOIN chat_turns t ON e.turn_id = t.id
                    JOIN chat_logs l ON e.chat_log_id = l.id
                    WHERE e.embedding IS NOT NULL
                """):
                    if row['embedding']:
                        db_embedding = load_embedding_blob(row['embedding'])
                        if db_embedding is not None and len(db_embedding) == len(query_embedding):
                            sim = cosine_similarity(query_embedding, db_embedding)
                            if sim >= threshold:
                                content = row['content'] or f"Chat log: {row['title'] or row['filename']}"
                                results.append(EvidenceItem(
                                    source_db='chatlogs',
                                    source_id=str(row['turn_id'] or row['chat_log_id']),
                                    source_type='chat_turn' if row['turn_id'] else 'chat_log',
                                    title=row['title'] or row['filename'] or 'Chat',
                                    snippet=content[:300],
                                    similarity_score=sim,
                                    match_type='semantic',
                                    metadata={'role': row['role']}
                                ))
            except sqlite3.OperationalError:
                pass
        
        # Fallback to keyword search
        if not results:
            try:
                keywords = query.lower().split()[:5]
                for kw in keywords:
                    if len(kw) < 3:
                        continue
                    for row in self.conn.execute("""
                        SELECT t.id, t.content, t.role, l.title, l.filename
                        FROM chat_turns t
                        JOIN chat_logs l ON t.chat_log_id = l.id
                        WHERE t.content LIKE ?
                        LIMIT 10
                    """, (f'%{kw}%',)):
                        content_lower = row['content'].lower()
                        match_count = sum(1 for k in keywords if k in content_lower)
                        score = match_count / len(keywords) if keywords else 0
                        
                        if score >= 0.3:
                            results.append(EvidenceItem(
                                source_db='chatlogs',
                                source_id=str(row['id']),
                                source_type='chat_turn',
                                title=row['title'] or row['filename'] or 'Chat',
                                snippet=row['content'][:300],
                                similarity_score=score,
                                match_type='lexical',
                                metadata={'role': row['role']}
                            ))
            except sqlite3.OperationalError:
                pass
        
        # Dedupe and sort
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.similarity_score, reverse=True):
            if r.source_id not in seen:
                seen.add(r.source_id)
                unique_results.append(r)
        
        return unique_results[:top_k]


class ArtifactsDBSearcher:
    """Search artifacts.db for relevant documents."""
    
    def __init__(self, embedding_model: EmbeddingModel):
        self.model = embedding_model
        self.conn = get_connection(ARTIFACTS_DB)
    
    def search(self, query: str, query_embedding: np.ndarray,
               threshold: float, top_k: int) -> List[EvidenceItem]:
        """Search artifacts by semantic similarity."""
        if self.conn is None:
            return []
        
        results = []
        
        # Try semantic search on chunk embeddings
        if query_embedding is not None:
            try:
                for row in self.conn.execute("""
                    SELECT c.id as chunk_id, c.content as chunk_content,
                           d.id, d.title, d.type, d.file_path,
                           e.vector
                    FROM embeddings e
                    JOIN chunks c ON e.chunk_id = c.id
                    JOIN documents d ON c.doc_id = d.id
                    WHERE d.archived_at IS NULL
                    AND e.vector IS NOT NULL
                """):
                    if row['vector']:
                        db_embedding = load_embedding_blob(row['vector'])
                        if db_embedding is not None and len(db_embedding) == len(query_embedding):
                            sim = cosine_similarity(query_embedding, db_embedding)
                            if sim >= threshold:
                                results.append(EvidenceItem(
                                    source_db='artifacts',
                                    source_id=row['id'],
                                    source_type=row['type'],
                                    title=row['title'],
                                    snippet=row['chunk_content'][:300] if row['chunk_content'] else '',
                                    similarity_score=sim,
                                    match_type='semantic',
                                    metadata={'file_path': row['file_path']}
                                ))
            except sqlite3.OperationalError:
                pass
        
        # Also search archived artifacts
        if query_embedding is not None:
            try:
                for row in self.conn.execute("""
                    SELECT c.id as chunk_id, c.content as chunk_content,
                           a.id, a.title, a.original_type, a.archive_path,
                           e.vector
                    FROM archived_embeddings e
                    JOIN archived_chunks c ON e.chunk_id = c.id
                    JOIN archived_artifacts a ON c.artifact_id = a.id
                    WHERE e.vector IS NOT NULL
                """):
                    if row['vector']:
                        db_embedding = load_embedding_blob(row['vector'])
                        if db_embedding is not None and len(db_embedding) == len(query_embedding):
                            sim = cosine_similarity(query_embedding, db_embedding)
                            if sim >= threshold:
                                results.append(EvidenceItem(
                                    source_db='artifacts',
                                    source_id=row['id'],
                                    source_type=f"archived_{row['original_type']}",
                                    title=f"[Archived] {row['title']}",
                                    snippet=row['chunk_content'][:300] if row['chunk_content'] else '',
                                    similarity_score=sim,
                                    match_type='semantic',
                                    metadata={'file_path': row['archive_path']}
                                ))
            except sqlite3.OperationalError:
                pass
        
        # Fallback to FTS
        if not results:
            try:
                for row in self.conn.execute("""
                    SELECT d.id, d.title, d.type, d.content, d.file_path
                    FROM documents d
                    WHERE d.archived_at IS NULL
                    AND (d.title LIKE ? OR d.content LIKE ?)
                    LIMIT 10
                """, (f'%{query[:50]}%', f'%{query[:50]}%')):
                    results.append(EvidenceItem(
                        source_db='artifacts',
                        source_id=row['id'],
                        source_type=row['type'],
                        title=row['title'],
                        snippet=row['content'][:300] if row['content'] else '',
                        similarity_score=0.4,
                        match_type='lexical',
                        metadata={'file_path': row['file_path']}
                    ))
            except sqlite3.OperationalError:
                pass
        
        # Dedupe by document ID
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.similarity_score, reverse=True):
            if r.source_id not in seen:
                seen.add(r.source_id)
                unique_results.append(r)
        
        return unique_results[:top_k]


class WorkspaceSearcher:
    """Search workspace files (concept_graph.json, paper_graph.json, etc.)."""
    
    def __init__(self, workspace_root: Path):
        self.root = workspace_root
    
    def search(self, query: str, concepts: List[str], top_k: int) -> List[EvidenceItem]:
        """Search workspace files for relevant context."""
        results = []
        
        # Search concept_graph.json
        concept_graph_path = self.root / "concept_graph.json"
        if concept_graph_path.exists():
            try:
                graph = json.loads(concept_graph_path.read_text())
                nodes = graph.get('nodes', [])
                
                for node in nodes:
                    node_id = node.get('id', '').lower()
                    for concept in concepts:
                        if concept in node_id or node_id in concept:
                            results.append(EvidenceItem(
                                source_db='workspace',
                                source_id=f"concept:{node_id}",
                                source_type='concept_node',
                                title=f"Concept: {node_id}",
                                snippet=f"Type: {node.get('type')}, Frequency: {node.get('freq')}",
                                similarity_score=0.7,
                                match_type='concept',
                                concepts_matched=[concept],
                                metadata=node
                            ))
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Search paper_graph.json
        paper_graph_path = self.root / "paper_graph.json"
        if paper_graph_path.exists():
            try:
                graph = json.loads(paper_graph_path.read_text())
                nodes = graph.get('nodes', [])
                
                query_lower = query.lower()
                for node in nodes:
                    title = node.get('title', '').lower()
                    if any(kw in title for kw in query_lower.split()[:3]):
                        results.append(EvidenceItem(
                            source_db='workspace',
                            source_id=f"paper:{node.get('id')}",
                            source_type='paper_reference',
                            title=node.get('title', 'Unknown Paper'),
                            snippet=f"arXiv: {node.get('arxiv', 'N/A')}",
                            similarity_score=0.6,
                            match_type='citation',
                            metadata=node
                        ))
            except (json.JSONDecodeError, KeyError):
                pass
        
        return results[:top_k]


# =============================================================================
# Main Enrichment Engine
# =============================================================================

class DISCEnrichmentEngine:
    """Main engine for enriching DISC documents with contextual provenance."""
    
    def __init__(self, threshold: float = DEFAULT_SEMANTIC_THRESHOLD, 
                 top_k: int = DEFAULT_TOP_K):
        self.threshold = threshold
        self.top_k = top_k
        self.device = get_device()
        self.embedding_model = EmbeddingModel(self.device)
        
        # Initialize searchers
        self.research_searcher = ResearchDBSearcher(self.embedding_model)
        self.chatlogs_searcher = ChatlogsDBSearcher(self.embedding_model)
        self.artifacts_searcher = ArtifactsDBSearcher(self.embedding_model)
        self.workspace_searcher = WorkspaceSearcher(WORKSPACE_ROOT)
    
    def enrich_disc(self, disc: DISCDocument) -> ProvenanceRecord:
        """Enrich a single DISC document with evidence from all sources."""
        print(f"\n{'='*60}")
        print(f"📄 Enriching: {disc.disc_id} - {disc.title}")
        print(f"{'='*60}")
        
        # Generate search queries
        queries = generate_search_queries(disc)
        print(f"🔍 Generated {len(queries)} search queries")
        print(f"🏷️  Key concepts: {', '.join(disc.key_concepts)}")
        
        all_evidence: List[EvidenceItem] = []
        sources_searched = []
        
        # Embed the main content for semantic search
        main_text = f"{disc.title} {disc.frontmatter.get('delegation_scope', '')} {disc.sections.get('summary', '')[:500]}"
        main_embedding = self.embedding_model.embed(main_text)
        
        # Search each database
        for query in queries[:3]:  # Limit queries to avoid too many results
            query_embedding = self.embedding_model.embed(query)
            
            # Research papers
            if self.research_searcher.conn:
                sources_searched.append('research.db')
                results = self.research_searcher.search(
                    query, query_embedding, self.threshold, self.top_k
                )
                all_evidence.extend(results)
                print(f"  📚 Research: {len(results)} matches")
            
            # Chat logs
            if self.chatlogs_searcher.conn:
                sources_searched.append('chatlogs.db')
                results = self.chatlogs_searcher.search(
                    query, query_embedding, self.threshold, self.top_k
                )
                all_evidence.extend(results)
                print(f"  💬 Chatlogs: {len(results)} matches")
            
            # Artifacts
            if self.artifacts_searcher.conn:
                sources_searched.append('artifacts.db')
                results = self.artifacts_searcher.search(
                    query, query_embedding, self.threshold, self.top_k
                )
                all_evidence.extend(results)
                print(f"  📁 Artifacts: {len(results)} matches")
        
        # Workspace files
        sources_searched.append('workspace')
        ws_results = self.workspace_searcher.search(
            disc.title, disc.key_concepts, self.top_k
        )
        all_evidence.extend(ws_results)
        print(f"  📂 Workspace: {len(ws_results)} matches")
        
        # Deduplicate evidence
        seen = set()
        unique_evidence = []
        for e in sorted(all_evidence, key=lambda x: x.similarity_score, reverse=True):
            key = f"{e.source_db}:{e.source_id}"
            if key not in seen:
                seen.add(key)
                unique_evidence.append(e)
        
        # Tag evidence with matched concepts
        for evidence in unique_evidence:
            evidence_text = f"{evidence.title} {evidence.snippet}".lower()
            for concept in disc.key_concepts:
                if concept in AICM_CONCEPTS:
                    for pattern in AICM_CONCEPTS[concept]:
                        if pattern in evidence_text:
                            evidence.concepts_matched.append(concept)
                            break
        
        # Calculate confidence score
        avg_similarity = np.mean([e.similarity_score for e in unique_evidence]) if unique_evidence else 0
        concept_coverage = len(set(c for e in unique_evidence for c in e.concepts_matched)) / max(len(disc.key_concepts), 1)
        confidence = (avg_similarity + concept_coverage) / 2
        
        return ProvenanceRecord(
            disc_id=disc.disc_id,
            disc_title=disc.title,
            enrichment_date=datetime.now().isoformat(),
            evidence_count=len(unique_evidence),
            sources_searched=list(set(sources_searched)),
            key_concepts=disc.key_concepts,
            evidence_chain=unique_evidence[:self.top_k],
            semantic_neighbors=[],  # Could add related DISCs here
            confidence_score=confidence
        )
    
    def generate_provenance_yaml(self, record: ProvenanceRecord) -> str:
        """Generate YAML provenance metadata block."""
        # Convert numpy types to native Python for clean YAML
        confidence = float(record.confidence_score) if hasattr(record.confidence_score, 'item') else record.confidence_score
        
        provenance = {
            'provenance': {
                'enrichment_date': record.enrichment_date,
                'confidence_score': round(float(confidence), 3),
                'sources_searched': record.sources_searched,
                'evidence_count': record.evidence_count,
                'key_concepts': record.key_concepts,
                'evidence_chain': [
                    {
                        'source': f"{e.source_db}:{e.source_type}",
                        'id': e.source_id,
                        'title': e.title[:80],
                        'score': round(float(e.similarity_score), 3),
                        'match_type': e.match_type,
                        'concepts': e.concepts_matched[:3]
                    }
                    for e in record.evidence_chain[:10]  # Top 10
                ]
            }
        }
        return yaml.dump(provenance, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    def generate_context_section(self, record: ProvenanceRecord) -> str:
        """Generate a Context/Provenance section for the DISC."""
        lines = [
            "## Historical Context & Provenance",
            "",
            f"> **Enrichment Date**: {record.enrichment_date[:10]}",
            f"> **Evidence Sources**: {', '.join(record.sources_searched)}",
            f"> **Confidence Score**: {record.confidence_score:.1%}",
            "",
            "### Related Research Papers",
            ""
        ]
        
        # Group evidence by source
        by_source = defaultdict(list)
        for e in record.evidence_chain:
            by_source[e.source_db].append(e)
        
        # Research papers
        if 'research' in by_source:
            for e in by_source['research'][:5]:
                arxiv = e.metadata.get('arxiv_id', '')
                arxiv_link = f"[arXiv:{arxiv}](https://arxiv.org/abs/{arxiv})" if arxiv else ''
                lines.append(f"- **{e.title[:60]}** ({e.match_type}, {e.similarity_score:.0%}) {arxiv_link}")
        else:
            lines.append("- *No direct research paper matches found*")
        
        lines.extend(["", "### Related Conversations", ""])
        
        # Chat logs
        if 'chatlogs' in by_source:
            for e in by_source['chatlogs'][:5]:
                lines.append(f"- **{e.title}**: \"{e.snippet[:80]}...\" ({e.match_type})")
        else:
            lines.append("- *No direct chat log matches found*")
        
        lines.extend(["", "### Concept Linkages", ""])
        
        # Concepts from workspace
        if 'workspace' in by_source:
            for e in by_source['workspace'][:5]:
                lines.append(f"- {e.title}: {e.snippet}")
        
        lines.extend(["", "---", ""])
        
        return '\n'.join(lines)


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Enrich DISC documents with contextual provenance from AIKH databases"
    )
    parser.add_argument('--disc', type=str, help="Specific DISC to process (e.g., DISC-0002)")
    parser.add_argument('--all', action='store_true', help="Process all DISC documents")
    parser.add_argument('--threshold', type=float, default=DEFAULT_SEMANTIC_THRESHOLD,
                        help=f"Similarity threshold (default: {DEFAULT_SEMANTIC_THRESHOLD})")
    parser.add_argument('--top-k', type=int, default=DEFAULT_TOP_K,
                        help=f"Max results per source (default: {DEFAULT_TOP_K})")
    parser.add_argument('--dry-run', action='store_true', 
                        help="Show results without modifying files")
    parser.add_argument('--output-dir', type=Path, default=None,
                        help="Output directory for provenance files (default: .discussions/provenance/)")
    
    args = parser.parse_args()
    
    if not args.disc and not args.all:
        parser.error("Specify --disc DISC-XXXX or --all")
    
    # Setup output directory
    output_dir = args.output_dir or (DISCUSSIONS_DIR / "provenance")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find DISC files
    disc_files = []
    if args.disc:
        pattern = f"{args.disc}*.md"
        disc_files = list(DISCUSSIONS_DIR.glob(pattern))
        if not disc_files:
            print(f"❌ No DISC file found matching: {args.disc}")
            return 1
    else:
        disc_files = sorted(DISCUSSIONS_DIR.glob("DISC-*.md"))
        if not disc_files:
            print("❌ No DISC files found in .discussions/")
            return 1
    
    print(f"\n🔬 DISC Enrichment RAG")
    print(f"📍 AIKH Home: {AIKH_HOME}")
    print(f"📁 Discussions: {DISCUSSIONS_DIR}")
    print(f"🎯 Threshold: {args.threshold}")
    print(f"📊 Top-K: {args.top_k}")
    print(f"📄 Files to process: {len(disc_files)}")
    
    # Check database availability
    print("\n📊 Database Status:")
    print(f"  Research DB: {'✅' if RESEARCH_DB.exists() else '❌'} {RESEARCH_DB}")
    print(f"  Chatlogs DB: {'✅' if CHATLOGS_DB.exists() else '❌'} {CHATLOGS_DB}")
    print(f"  Artifacts DB: {'✅' if ARTIFACTS_DB.exists() else '❌'} {ARTIFACTS_DB}")
    
    # Initialize engine
    engine = DISCEnrichmentEngine(threshold=args.threshold, top_k=args.top_k)
    
    # Process each DISC
    all_records = []
    for disc_file in disc_files:
        disc = parse_disc_document(disc_file)
        if disc is None:
            print(f"⚠️  Could not parse: {disc_file}")
            continue
        
        record = engine.enrich_disc(disc)
        all_records.append(record)
        
        # Generate outputs
        yaml_content = engine.generate_provenance_yaml(record)
        context_section = engine.generate_context_section(record)
        
        # Output file paths
        yaml_file = output_dir / f"{disc.disc_id}_provenance.yaml"
        context_file = output_dir / f"{disc.disc_id}_context.md"
        
        if args.dry_run:
            print(f"\n📋 Provenance YAML for {disc.disc_id}:")
            print(yaml_content[:500])
            print("...")
        else:
            # Save provenance YAML
            yaml_file.write_text(yaml_content, encoding='utf-8')
            print(f"💾 Saved: {yaml_file}")
            
            # Save context section
            context_file.write_text(context_section, encoding='utf-8')
            print(f"💾 Saved: {context_file}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 ENRICHMENT SUMMARY")
    print(f"{'='*60}")
    print(f"DISCs processed: {len(all_records)}")
    print(f"Total evidence items: {sum(r.evidence_count for r in all_records)}")
    print(f"Average confidence: {np.mean([r.confidence_score for r in all_records]):.1%}")
    print(f"Output directory: {output_dir}")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN - No files were modified")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
