#!/usr/bin/env python3
"""Deep Contextual Mapping Between AIKH Databases.

Performs multi-strategy cross-linking between:
- research.db: Academic papers (25 papers, 3325 chunks)
- knowledge.db: Workspace artifacts (ADRs, specs, discussions)
- chatlogs.db: AI conversation history (49 logs, 2190 turns)

Mapping Strategies:
1. Semantic Similarity - Embedding-based similarity matching
2. Lexical Matching - Keyword and phrase overlap
3. Citation Detection - arXiv, DOI, paper title references
4. Concept Extraction - Topic modeling and concept mapping
5. Entity Linking - File paths, project names, technical terms

Usage:
    python scripts/deep_context_mapper.py [--rebuild] [--threshold 0.7]
"""

import argparse
import os
import re
import sqlite3
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import numpy as np

# Try to import sentence-transformers for embedding generation
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDER_AVAILABLE = True
except ImportError:
    EMBEDDER_AVAILABLE = False
    SentenceTransformer = None


# =============================================================================
# Configuration
# =============================================================================

AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
RESEARCH_DB = AIKH_HOME / "research.db"
CHATLOGS_DB = AIKH_HOME / "chatlogs.db"
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", "."))
KNOWLEDGE_DB = WORKSPACE_ROOT / ".workspace" / "knowledge.db"

# Semantic similarity threshold for creating links
DEFAULT_SIMILARITY_THRESHOLD = 0.65

# Key concepts for AI/ML domain
AI_CONCEPTS = {
    'llm': ['large language model', 'llm', 'gpt', 'transformer', 'language model'],
    'rag': ['retrieval augmented', 'rag', 'retrieval', 'vector search', 'embedding'],
    'agent': ['agent', 'autonomous', 'tool use', 'function calling', 'agentic'],
    'prompt': ['prompt', 'prompting', 'chain of thought', 'cot', 'few-shot'],
    'fine_tuning': ['fine-tune', 'fine-tuning', 'rlhf', 'sft', 'training'],
    'architecture': ['architecture', 'transformer', 'attention', 'encoder', 'decoder'],
    'evaluation': ['benchmark', 'evaluation', 'metrics', 'accuracy', 'perplexity'],
    'memory': ['memory', 'context window', 'long context', 'retrieval'],
    'reasoning': ['reasoning', 'chain of thought', 'step by step', 'logical'],
    'code': ['code generation', 'coding', 'programming', 'codex', 'copilot'],
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CrossLink:
    """Represents a contextual link between entities."""
    source_db: str
    source_id: str
    source_type: str
    target_db: str
    target_id: str
    target_type: str
    link_type: str
    confidence: float = 1.0
    context: Optional[str] = None
    evidence: list = field(default_factory=list)


@dataclass
class Entity:
    """Generic entity from any database."""
    db: str
    id: str
    type: str
    title: str
    content: str
    embedding: Optional[np.ndarray] = None
    concepts: set = field(default_factory=set)
    keywords: set = field(default_factory=set)


# =============================================================================
# Database Connections
# =============================================================================

def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_embedding(blob: bytes) -> np.ndarray:
    """Load embedding from SQLite blob."""
    if blob is None:
        return None
    # Assuming float32 embeddings
    n_floats = len(blob) // 4
    return np.array(struct.unpack(f'{n_floats}f', blob))


# =============================================================================
# Entity Loading
# =============================================================================

def load_research_entities() -> list[Entity]:
    """Load papers from research.db."""
    entities = []
    if not RESEARCH_DB.exists():
        return entities
    
    with get_connection(RESEARCH_DB) as conn:
        # Load papers with their embeddings
        for row in conn.execute("""
            SELECT p.id, p.title, p.abstract, p.authors, p.keywords,
                   e.embedding
            FROM research_papers p
            LEFT JOIN paper_embeddings_gpu e ON p.id = e.paper_id 
                AND e.embedding_type = 'paper'
        """):
            content = f"{row['title']} {row['abstract'] or ''} {row['keywords'] or ''}"
            entity = Entity(
                db='research',
                id=row['id'],
                type='paper',
                title=row['title'],
                content=content,
                embedding=load_embedding(row['embedding']) if row['embedding'] else None
            )
            entities.append(entity)
    
    return entities


def load_knowledge_entities() -> list[Entity]:
    """Load documents from knowledge.db."""
    entities = []
    if not KNOWLEDGE_DB.exists():
        return entities
    
    with get_connection(KNOWLEDGE_DB) as conn:
        for row in conn.execute("""
            SELECT id, type, title, content FROM documents
        """):
            entity = Entity(
                db='knowledge',
                id=row['id'],
                type=row['type'],
                title=row['title'],
                content=row['content'][:5000],  # Limit content size
            )
            entities.append(entity)
    
    return entities


def load_chatlog_entities() -> list[Entity]:
    """Load chat logs from chatlogs.db."""
    entities = []
    if not CHATLOGS_DB.exists():
        return entities
    
    with get_connection(CHATLOGS_DB) as conn:
        for row in conn.execute("""
            SELECT id, title, filename FROM chat_logs
        """):
            # Get aggregated turn content
            turns = conn.execute("""
                SELECT content FROM chat_turns 
                WHERE chat_log_id = ? 
                ORDER BY turn_index LIMIT 20
            """, (row['id'],)).fetchall()
            
            content = ' '.join(t['content'][:500] for t in turns)
            
            entity = Entity(
                db='chatlogs',
                id=str(row['id']),
                type='chatlog',
                title=row['title'] or row['filename'],
                content=content[:5000],
            )
            entities.append(entity)
    
    return entities


# =============================================================================
# Concept & Keyword Extraction
# =============================================================================

def extract_concepts(text: str) -> set[str]:
    """Extract AI/ML concepts from text."""
    text_lower = text.lower()
    found_concepts = set()
    
    for concept, keywords in AI_CONCEPTS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_concepts.add(concept)
                break
    
    return found_concepts


def extract_keywords(text: str, top_n: int = 20) -> set[str]:
    """Extract significant keywords from text."""
    # Simple keyword extraction - remove stopwords and get frequent terms
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
        'because', 'until', 'while', 'this', 'that', 'these', 'those', 'it',
        'its', 'we', 'our', 'you', 'your', 'they', 'their', 'what', 'which',
        'who', 'whom', 'also', 'using', 'use', 'used', 'based', 'new', 'one',
    }
    
    # Tokenize and filter
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    words = [w for w in words if w not in stopwords]
    
    # Get top N by frequency
    counter = Counter(words)
    return set(word for word, _ in counter.most_common(top_n))


def extract_citations(text: str) -> dict[str, list[str]]:
    """Extract paper citations from text."""
    citations = {
        'arxiv': [],
        'doi': [],
        'titles': [],
    }
    
    # arXiv patterns
    arxiv_pattern = r'(?:arXiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)'
    citations['arxiv'] = re.findall(arxiv_pattern, text)
    
    # DOI patterns
    doi_pattern = r'10\.\d{4,}/[^\s]+'
    citations['doi'] = re.findall(doi_pattern, text)
    
    return citations


# =============================================================================
# Similarity Computation
# =============================================================================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if a is None or b is None:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def compute_lexical_similarity(entity_a: Entity, entity_b: Entity) -> float:
    """Compute lexical similarity based on keyword overlap."""
    if not entity_a.keywords or not entity_b.keywords:
        return 0.0
    return jaccard_similarity(entity_a.keywords, entity_b.keywords)


def compute_concept_similarity(entity_a: Entity, entity_b: Entity) -> float:
    """Compute concept similarity based on shared concepts."""
    if not entity_a.concepts or not entity_b.concepts:
        return 0.0
    return jaccard_similarity(entity_a.concepts, entity_b.concepts)


# =============================================================================
# Link Discovery
# =============================================================================

def find_citation_links(
    research_entities: list[Entity],
    other_entities: list[Entity]
) -> list[CrossLink]:
    """Find links based on paper citations."""
    links = []
    
    # Build lookup tables
    arxiv_to_paper = {}
    title_to_paper = {}
    keyword_to_papers = defaultdict(list)
    
    # Key paper keywords for matching
    paper_keywords = {
        'llama': ['llama', 'llama 2', 'llama2'],
        'gpt': ['gpt', 'gpt-4', 'gpt4', 'chatgpt'],
        'palm': ['palm', 'pathways'],
        'gemini': ['gemini'],
        'deepseek': ['deepseek', 'deepseek-r1'],
        'starcoder': ['starcoder', 'star coder'],
        'codex': ['codex', 'code generation'],
        'rag': ['retrieval augmented', 'retrieval-augmented'],
        'chain_of_thought': ['chain of thought', 'chain-of-thought', 'cot prompting'],
        'longformer': ['longformer', 'long document'],
        'truthfulqa': ['truthfulqa', 'truthful qa'],
        'mmlu': ['mmlu', 'massive multitask'],
        'agentbench': ['agentbench', 'agent bench'],
        'autogen': ['autogen', 'multi-agent'],
    }
    
    for entity in research_entities:
        # Extract arXiv ID from content or title
        arxiv_match = re.search(r'(\d{4}\.\d{4,5})', entity.content)
        if arxiv_match:
            arxiv_to_paper[arxiv_match.group(1)] = entity
        
        # Title matching (normalized)
        title_norm = entity.title.lower().strip()
        if len(title_norm) > 15:
            title_to_paper[title_norm] = entity
            # Also add key parts of title
            for word in title_norm.split():
                if len(word) > 5:
                    keyword_to_papers[word].append(entity)
        
        # Match against known paper keywords
        content_lower = entity.content.lower()
        for key, keywords in paper_keywords.items():
            for kw in keywords:
                if kw in content_lower or kw in title_norm:
                    keyword_to_papers[key].append(entity)
                    break
    
    # Search for citations in other entities
    for entity in other_entities:
        content_lower = entity.content.lower()
        citations = extract_citations(entity.content)
        
        # Match arXiv IDs
        for arxiv_id in citations['arxiv']:
            if arxiv_id in arxiv_to_paper:
                paper = arxiv_to_paper[arxiv_id]
                links.append(CrossLink(
                    source_db=entity.db,
                    source_id=entity.id,
                    source_type=entity.type,
                    target_db='research',
                    target_id=paper.id,
                    target_type='paper',
                    link_type='cites',
                    confidence=1.0,
                    context=f"arXiv:{arxiv_id}",
                    evidence=[f"Found arXiv:{arxiv_id} reference"]
                ))
        
        # Match paper titles
        for title, paper in title_to_paper.items():
            if title in content_lower:
                links.append(CrossLink(
                    source_db=entity.db,
                    source_id=entity.id,
                    source_type=entity.type,
                    target_db='research',
                    target_id=paper.id,
                    target_type='paper',
                    link_type='references',
                    confidence=0.9,
                    context=f"Title match: {paper.title[:50]}",
                    evidence=[f"Found title reference: {title[:50]}"]
                ))
        
        # Match paper keywords
        matched_papers = set()
        for key, keywords in paper_keywords.items():
            for kw in keywords:
                if kw in content_lower and key in keyword_to_papers:
                    for paper in keyword_to_papers[key]:
                        if paper.id not in matched_papers:
                            matched_papers.add(paper.id)
                            links.append(CrossLink(
                                source_db=entity.db,
                                source_id=entity.id,
                                source_type=entity.type,
                                target_db='research',
                                target_id=paper.id,
                                target_type='paper',
                                link_type='discusses',
                                confidence=0.75,
                                context=f"Keyword match: {kw}",
                                evidence=[f"Found keyword: {kw}"]
                            ))
                    break
    
    return links


def find_concept_links(
    entities: list[Entity],
    threshold: float = 0.5
) -> list[CrossLink]:
    """Find links based on shared concepts."""
    links = []
    
    # Enrich entities with concepts
    for entity in entities:
        entity.concepts = extract_concepts(entity.content)
        entity.keywords = extract_keywords(entity.content)
    
    # Compare across different databases
    for i, entity_a in enumerate(entities):
        for entity_b in entities[i+1:]:
            # Skip same-database comparisons for now
            if entity_a.db == entity_b.db:
                continue
            
            # Compute combined similarity
            concept_sim = compute_concept_similarity(entity_a, entity_b)
            keyword_sim = compute_lexical_similarity(entity_a, entity_b)
            
            # Weighted combination
            combined_sim = 0.6 * concept_sim + 0.4 * keyword_sim
            
            if combined_sim >= threshold:
                shared_concepts = entity_a.concepts & entity_b.concepts
                links.append(CrossLink(
                    source_db=entity_a.db,
                    source_id=entity_a.id,
                    source_type=entity_a.type,
                    target_db=entity_b.db,
                    target_id=entity_b.id,
                    target_type=entity_b.type,
                    link_type='relates_to',
                    confidence=combined_sim,
                    context=f"Shared concepts: {', '.join(shared_concepts)}",
                    evidence=[f"Concept similarity: {concept_sim:.2f}", 
                              f"Keyword similarity: {keyword_sim:.2f}"]
                ))
    
    return links


def generate_embeddings(entities: list[Entity], model_name: str = 'all-mpnet-base-v2') -> int:
    """Generate embeddings for entities that don't have them."""
    if not EMBEDDER_AVAILABLE:
        print("    ⚠️  sentence-transformers not available, skipping embedding generation")
        return 0
    
    # Filter entities without embeddings
    to_embed = [e for e in entities if e.embedding is None]
    if not to_embed:
        return 0
    
    print(f"    Generating embeddings for {len(to_embed)} entities...")
    
    try:
        model = SentenceTransformer(model_name)
        
        # Prepare texts - use title + truncated content
        texts = []
        for entity in to_embed:
            text = f"{entity.title}. {entity.content[:1500]}"
            texts.append(text)
        
        # Generate embeddings in batch
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
        
        # Assign embeddings to entities
        for entity, emb in zip(to_embed, embeddings):
            entity.embedding = emb
        
        return len(to_embed)
    except Exception as e:
        print(f"    ⚠️  Embedding generation failed: {e}")
        return 0


def find_semantic_links(
    entities: list[Entity],
    threshold: float = 0.65
) -> list[CrossLink]:
    """Find links based on embedding similarity."""
    links = []
    
    # Generate embeddings for entities that don't have them
    generated = generate_embeddings(entities)
    if generated > 0:
        print(f"    Generated {generated} new embeddings")
    
    # Filter entities with embeddings
    embedded = [e for e in entities if e.embedding is not None]
    print(f"    Comparing {len(embedded)} entities with embeddings...")
    
    if len(embedded) < 2:
        return links
    
    # For efficiency, compare across databases only
    by_db = defaultdict(list)
    for e in embedded:
        by_db[e.db].append(e)
    
    comparisons = 0
    for db_a in by_db:
        for db_b in by_db:
            if db_a >= db_b:  # Skip same-db and already compared pairs
                continue
            
            for entity_a in by_db[db_a]:
                for entity_b in by_db[db_b]:
                    comparisons += 1
                    similarity = cosine_similarity(entity_a.embedding, entity_b.embedding)
                    
                    if similarity >= threshold:
                        links.append(CrossLink(
                            source_db=entity_a.db,
                            source_id=entity_a.id,
                            source_type=entity_a.type,
                            target_db=entity_b.db,
                            target_id=entity_b.id,
                            target_type=entity_b.type,
                            link_type='semantically_similar',
                            confidence=float(similarity),
                            context=f"Embedding similarity: {similarity:.3f}",
                            evidence=[f"Cosine similarity: {similarity:.3f}"]
                        ))
    
    print(f"    Performed {comparisons} comparisons")
    return links


# =============================================================================
# Database Operations
# =============================================================================

def init_crosslinks_table():
    """Initialize the cross-links table."""
    if not KNOWLEDGE_DB.exists():
        print(f"Error: Knowledge DB not found at {KNOWLEDGE_DB}")
        return False
    
    schema = """
    CREATE TABLE IF NOT EXISTS cross_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_db TEXT NOT NULL,
        source_id TEXT NOT NULL,
        source_type TEXT NOT NULL,
        target_db TEXT NOT NULL,
        target_id TEXT NOT NULL,
        target_type TEXT NOT NULL,
        link_type TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        context TEXT,
        evidence TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(source_db, source_id, target_db, target_id, link_type)
    );
    CREATE INDEX IF NOT EXISTS idx_crosslinks_source ON cross_links(source_db, source_id);
    CREATE INDEX IF NOT EXISTS idx_crosslinks_target ON cross_links(target_db, target_id);
    CREATE INDEX IF NOT EXISTS idx_crosslinks_type ON cross_links(link_type);
    CREATE INDEX IF NOT EXISTS idx_crosslinks_confidence ON cross_links(confidence);
    """
    
    with get_connection(KNOWLEDGE_DB) as conn:
        conn.executescript(schema)
    
    return True


def save_links(links: list[CrossLink], clear_existing: bool = False):
    """Save cross-links to database."""
    if not links:
        return 0
    
    with get_connection(KNOWLEDGE_DB) as conn:
        if clear_existing:
            conn.execute("DELETE FROM cross_links")
        
        saved = 0
        for link in links:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO cross_links
                    (source_db, source_id, source_type, target_db, target_id,
                     target_type, link_type, confidence, context, evidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    link.source_db, link.source_id, link.source_type,
                    link.target_db, link.target_id, link.target_type,
                    link.link_type, link.confidence, link.context,
                    '|'.join(link.evidence) if link.evidence else None
                ))
                saved += 1
            except Exception as e:
                print(f"  Error saving link: {e}")
        
        conn.commit()
    
    return saved


def get_link_stats() -> dict:
    """Get statistics about cross-links."""
    stats = {
        'total': 0,
        'by_type': {},
        'by_source_db': {},
        'by_target_db': {},
        'high_confidence': 0,
    }
    
    with get_connection(KNOWLEDGE_DB) as conn:
        stats['total'] = conn.execute(
            "SELECT COUNT(*) FROM cross_links"
        ).fetchone()[0]
        
        for row in conn.execute(
            "SELECT link_type, COUNT(*) FROM cross_links GROUP BY link_type"
        ):
            stats['by_type'][row[0]] = row[1]
        
        for row in conn.execute(
            "SELECT source_db, COUNT(*) FROM cross_links GROUP BY source_db"
        ):
            stats['by_source_db'][row[0]] = row[1]
        
        for row in conn.execute(
            "SELECT target_db, COUNT(*) FROM cross_links GROUP BY target_db"
        ):
            stats['by_target_db'][row[0]] = row[1]
        
        stats['high_confidence'] = conn.execute(
            "SELECT COUNT(*) FROM cross_links WHERE confidence >= 0.8"
        ).fetchone()[0]
    
    return stats


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Deep contextual mapping between AIKH databases')
    parser.add_argument('--rebuild', action='store_true', help='Clear and rebuild all links')
    parser.add_argument('--threshold', type=float, default=DEFAULT_SIMILARITY_THRESHOLD,
                        help=f'Similarity threshold (default: {DEFAULT_SIMILARITY_THRESHOLD})')
    args = parser.parse_args()
    
    print("=" * 70)
    print("AIKH Deep Contextual Mapper")
    print("=" * 70)
    
    # Check databases
    print("\n📂 Database Status:")
    for name, path in [('Research', RESEARCH_DB), ('Knowledge', KNOWLEDGE_DB), ('Chatlogs', CHATLOGS_DB)]:
        exists = "✅" if path.exists() else "❌"
        print(f"  {exists} {name}: {path}")
    
    if not KNOWLEDGE_DB.exists():
        print("\n❌ Knowledge DB required for storing cross-links. Exiting.")
        return
    
    # Initialize table
    print("\n🔧 Initializing cross-links table...")
    init_crosslinks_table()
    
    # Load entities
    print("\n📥 Loading entities...")
    research_entities = load_research_entities()
    knowledge_entities = load_knowledge_entities()
    chatlog_entities = load_chatlog_entities()
    
    print(f"  Research papers: {len(research_entities)}")
    print(f"  Knowledge docs:  {len(knowledge_entities)}")
    print(f"  Chat logs:       {len(chatlog_entities)}")
    
    all_entities = research_entities + knowledge_entities + chatlog_entities
    
    if not all_entities:
        print("\n❌ No entities found. Exiting.")
        return
    
    # Find links using multiple strategies
    all_links = []
    
    # Strategy 1: Citation detection
    print("\n🔍 Strategy 1: Citation Detection...")
    citation_links = find_citation_links(
        research_entities, 
        knowledge_entities + chatlog_entities
    )
    print(f"  Found {len(citation_links)} citation links")
    all_links.extend(citation_links)
    
    # Strategy 2: Concept-based linking
    print("\n🧠 Strategy 2: Concept-Based Linking...")
    concept_links = find_concept_links(all_entities, threshold=0.4)
    print(f"  Found {len(concept_links)} concept links")
    all_links.extend(concept_links)
    
    # Strategy 3: Semantic similarity (if embeddings available)
    print("\n📊 Strategy 3: Semantic Similarity...")
    semantic_links = find_semantic_links(all_entities, threshold=args.threshold)
    print(f"  Found {len(semantic_links)} semantic links")
    all_links.extend(semantic_links)
    
    # Deduplicate links
    unique_links = {}
    for link in all_links:
        key = (link.source_db, link.source_id, link.target_db, link.target_id, link.link_type)
        if key not in unique_links or link.confidence > unique_links[key].confidence:
            unique_links[key] = link
    
    final_links = list(unique_links.values())
    print(f"\n📊 Total unique links: {len(final_links)}")
    
    # Save links
    print("\n💾 Saving links to database...")
    saved = save_links(final_links, clear_existing=args.rebuild)
    print(f"  Saved {saved} links")
    
    # Print statistics
    print("\n📈 Cross-Link Statistics:")
    stats = get_link_stats()
    print(f"  Total links: {stats['total']}")
    print(f"  High confidence (≥0.8): {stats['high_confidence']}")
    print("\n  By link type:")
    for link_type, count in sorted(stats['by_type'].items()):
        print(f"    {link_type}: {count}")
    print("\n  By source database:")
    for db, count in sorted(stats['by_source_db'].items()):
        print(f"    {db}: {count}")
    print("\n  By target database:")
    for db, count in sorted(stats['by_target_db'].items()):
        print(f"    {db}: {count}")
    
    print("\n" + "=" * 70)
    print("✅ Deep contextual mapping complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
