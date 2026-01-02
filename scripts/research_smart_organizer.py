"""Research Paper Smart Organizer - GPU-Accelerated Classification & Linking.

This tool provides:
1. Automatic topic classification using embeddings + clustering
2. Smart linking between papers based on semantic similarity
3. Knowledge graph extraction for concepts and relationships
4. Hierarchical taxonomy management

Citation: SESSION_009 Research on Knowledge Graph Construction
          https://arxiv.org/html/2507.03226v2
          Key insight: Two-stage retrieval (graph traversal + dense re-ranking)

Requirements:
    pip install sentence-transformers torch scikit-learn numpy
    
GPU Acceleration:
    Automatically uses CUDA if available (optimized for RTX 5090)
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

# Conditional imports for ML components
try:
    import torch
    TORCH_AVAILABLE = True
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    TORCH_AVAILABLE = False
    DEVICE = "cpu"

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

try:
    from sklearn.cluster import AgglomerativeClustering, KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

TAXONOMY_SCHEMA = """
-- Hierarchical Topic Taxonomy
-- Supports multi-level categorization across any domain

CREATE TABLE IF NOT EXISTS taxonomy_topics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT REFERENCES taxonomy_topics(id),
    level INTEGER DEFAULT 0,
    description TEXT,
    keywords TEXT,  -- JSON array of associated keywords
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(name, parent_id)
);

CREATE INDEX IF NOT EXISTS idx_taxonomy_parent ON taxonomy_topics(parent_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_level ON taxonomy_topics(level);

-- Paper-Topic Associations (many-to-many with confidence)
CREATE TABLE IF NOT EXISTS paper_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    topic_id TEXT NOT NULL REFERENCES taxonomy_topics(id) ON DELETE CASCADE,
    confidence REAL DEFAULT 1.0,  -- 0.0-1.0 classification confidence
    source TEXT DEFAULT 'auto',   -- 'auto', 'manual', 'llm'
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_topics_paper ON paper_topics(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_topics_topic ON paper_topics(topic_id);

-- Paper Sources (where papers come from)
CREATE TABLE IF NOT EXISTS paper_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    url_pattern TEXT,
    source_type TEXT,  -- 'arxiv', 'acl', 'ieee', 'conference', 'journal'
    credibility_score REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Paper-Source Links
CREATE TABLE IF NOT EXISTS paper_source_links (
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES paper_sources(id) ON DELETE CASCADE,
    external_id TEXT,  -- arxiv_id, doi, etc.
    url TEXT,
    PRIMARY KEY (paper_id, source_id)
);

-- Smart Links (paper-to-paper relationships)
CREATE TABLE IF NOT EXISTS paper_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    target_paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    link_type TEXT NOT NULL,  -- 'similar', 'cites', 'extends', 'contradicts', 'same_topic'
    similarity_score REAL,    -- cosine similarity for 'similar' type
    confidence REAL DEFAULT 1.0,
    metadata TEXT,            -- JSON for additional info
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source_paper_id, target_paper_id, link_type)
);

CREATE INDEX IF NOT EXISTS idx_paper_links_source ON paper_links(source_paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_links_target ON paper_links(target_paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_links_type ON paper_links(link_type);

-- Extracted Concepts (entities from papers)
CREATE TABLE IF NOT EXISTS paper_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES research_papers(id) ON DELETE CASCADE,
    concept TEXT NOT NULL,
    concept_type TEXT,  -- 'technique', 'model', 'dataset', 'metric', 'tool'
    frequency INTEGER DEFAULT 1,
    importance REAL DEFAULT 0.5,  -- TF-IDF or similar
    context TEXT,  -- Sentence where concept appears
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, concept, concept_type)
);

CREATE INDEX IF NOT EXISTS idx_concepts_paper ON paper_concepts(paper_id);
CREATE INDEX IF NOT EXISTS idx_concepts_concept ON paper_concepts(concept);
CREATE INDEX IF NOT EXISTS idx_concepts_type ON paper_concepts(concept_type);

-- Concept Graph (relationships between concepts)
CREATE TABLE IF NOT EXISTS concept_graph (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_concept TEXT NOT NULL,
    target_concept TEXT NOT NULL,
    relation_type TEXT NOT NULL,  -- 'uses', 'improves', 'part_of', 'compared_to'
    paper_id TEXT REFERENCES research_papers(id) ON DELETE CASCADE,
    weight REAL DEFAULT 1.0,
    UNIQUE(source_concept, target_concept, relation_type, paper_id)
);

CREATE INDEX IF NOT EXISTS idx_concept_graph_source ON concept_graph(source_concept);
CREATE INDEX IF NOT EXISTS idx_concept_graph_target ON concept_graph(target_concept);

-- Paper Embeddings (for fast similarity)
CREATE TABLE IF NOT EXISTS paper_embeddings_v2 (
    paper_id TEXT PRIMARY KEY REFERENCES research_papers(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    embedding BLOB NOT NULL,  -- numpy array as bytes
    embedding_dim INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

# Default taxonomy for AI/ML research
DEFAULT_TAXONOMY = {
    "ai-systems": {
        "description": "AI system architectures and frameworks",
        "children": {
            "agentic-ai": {
                "description": "Autonomous AI agents and multi-agent systems",
                "keywords": ["agent", "autonomous", "multi-agent", "tool-use", "ReAct"]
            },
            "llm-architectures": {
                "description": "Large language model design and training",
                "keywords": ["transformer", "attention", "pretraining", "fine-tuning"]
            },
            "rag-systems": {
                "description": "Retrieval-augmented generation",
                "keywords": ["RAG", "retrieval", "vector", "embedding", "knowledge base"]
            }
        }
    },
    "context-management": {
        "description": "Context window and memory management",
        "children": {
            "context-compression": {
                "description": "Techniques to compress context windows",
                "keywords": ["compression", "pruning", "distillation", "summarization"]
            },
            "memory-systems": {
                "description": "Memory hierarchies and long-term storage",
                "keywords": ["memory", "hierarchical", "long-term", "episodic", "semantic"]
            },
            "token-optimization": {
                "description": "Token budget and allocation strategies",
                "keywords": ["token", "budget", "allocation", "efficiency"]
            }
        }
    },
    "code-generation": {
        "description": "AI-assisted code generation and analysis",
        "children": {
            "code-synthesis": {
                "description": "Generating code from specifications",
                "keywords": ["synthesis", "generation", "completion", "copilot"]
            },
            "code-understanding": {
                "description": "Analyzing and understanding code",
                "keywords": ["analysis", "understanding", "parsing", "AST"]
            },
            "code-validation": {
                "description": "Verifying and testing generated code",
                "keywords": ["validation", "testing", "verification", "correctness"]
            }
        }
    },
    "evaluation": {
        "description": "LLM evaluation and quality metrics",
        "children": {
            "benchmarks": {
                "description": "Standard benchmarks and datasets",
                "keywords": ["benchmark", "dataset", "HumanEval", "MBPP", "SWE-bench"]
            },
            "quality-metrics": {
                "description": "Metrics for measuring output quality",
                "keywords": ["metric", "score", "quality", "evaluation"]
            },
            "llm-as-judge": {
                "description": "Using LLMs to evaluate other LLMs",
                "keywords": ["judge", "evaluator", "self-eval", "critique"]
            }
        }
    },
    "software-engineering": {
        "description": "Software engineering practices with AI",
        "children": {
            "developer-tools": {
                "description": "Tools and IDEs for developers",
                "keywords": ["IDE", "tool", "developer", "productivity", "workflow"]
            },
            "documentation": {
                "description": "Documentation generation and management",
                "keywords": ["documentation", "docs", "readme", "API"]
            },
            "testing": {
                "description": "Automated testing and QA",
                "keywords": ["test", "testing", "QA", "automation"]
            }
        }
    }
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Topic:
    id: str
    name: str
    parent_id: Optional[str] = None
    level: int = 0
    description: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class PaperLink:
    source_paper_id: str
    target_paper_id: str
    link_type: str
    similarity_score: Optional[float] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class Concept:
    paper_id: str
    concept: str
    concept_type: str
    frequency: int = 1
    importance: float = 0.5
    context: str = ""


# =============================================================================
# SMART ORGANIZER CLASS
# =============================================================================

class ResearchSmartOrganizer:
    """GPU-accelerated paper classification and smart linking system."""
    
    def __init__(
        self,
        db_path: str = ".workspace/research_papers.db",
        embedding_model: str = "all-mpnet-base-v2",
        device: Optional[str] = None
    ):
        self.db_path = Path(db_path)
        self.embedding_model_name = embedding_model
        self.device = device or DEVICE
        self.model = None
        self._init_db()
        
        print(f"🚀 ResearchSmartOrganizer initialized")
        print(f"   Device: {self.device}")
        print(f"   Database: {self.db_path}")
        
    def _init_db(self):
        """Initialize database with taxonomy schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(TAXONOMY_SCHEMA)
            conn.commit()
            
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_model(self):
        """Lazy-load the embedding model."""
        if self.model is None:
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
            print(f"📦 Loading embedding model: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name, device=self.device)
            print(f"   Model loaded on {self.device}")
        return self.model
    
    # =========================================================================
    # TAXONOMY MANAGEMENT
    # =========================================================================
    
    def init_default_taxonomy(self) -> int:
        """Initialize the default AI/ML taxonomy."""
        count = 0
        
        def add_topics(topics: dict, parent_id: Optional[str] = None, level: int = 0):
            nonlocal count
            for name, data in topics.items():
                topic_id = hashlib.md5(f"{parent_id or ''}/{name}".encode()).hexdigest()[:12]
                self.add_topic(
                    topic_id=topic_id,
                    name=name,
                    parent_id=parent_id,
                    level=level,
                    description=data.get("description", ""),
                    keywords=data.get("keywords", [])
                )
                count += 1
                if "children" in data:
                    add_topics(data["children"], topic_id, level + 1)
        
        add_topics(DEFAULT_TAXONOMY)
        print(f"✅ Initialized {count} topics in taxonomy")
        return count
    
    def add_topic(
        self,
        topic_id: str,
        name: str,
        parent_id: Optional[str] = None,
        level: int = 0,
        description: str = "",
        keywords: List[str] = None
    ) -> bool:
        """Add a topic to the taxonomy."""
        with self._get_conn() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO taxonomy_topics 
                    (id, name, parent_id, level, description, keywords)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (topic_id, name, parent_id, level, description, 
                      json.dumps(keywords or [])))
                conn.commit()
                return True
            except Exception as e:
                print(f"❌ Error adding topic: {e}")
                return False
    
    def get_taxonomy_tree(self) -> Dict[str, Any]:
        """Get the full taxonomy as a nested tree."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT id, name, parent_id, level, description, keywords
                FROM taxonomy_topics ORDER BY level, name
            """)
            topics = [dict(row) for row in cursor.fetchall()]
        
        # Build tree
        tree = {}
        topic_map = {t["id"]: t for t in topics}
        
        for topic in topics:
            topic["children"] = {}
            if topic["parent_id"] is None:
                tree[topic["name"]] = topic
            else:
                parent = topic_map.get(topic["parent_id"])
                if parent:
                    parent["children"][topic["name"]] = topic
        
        return tree
    
    def list_topics(self) -> List[Dict[str, Any]]:
        """List all topics with paper counts."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT t.*, COUNT(pt.paper_id) as paper_count
                FROM taxonomy_topics t
                LEFT JOIN paper_topics pt ON t.id = pt.topic_id
                GROUP BY t.id
                ORDER BY t.level, t.name
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # EMBEDDING GENERATION (GPU-ACCELERATED)
    # =========================================================================
    
    def generate_paper_embeddings(self, batch_size: int = 32) -> int:
        """Generate embeddings for all papers using GPU."""
        model = self._load_model()
        
        with self._get_conn() as conn:
            # Get papers without embeddings
            cursor = conn.execute("""
                SELECT p.id, p.title, p.abstract, p.full_text
                FROM research_papers p
                LEFT JOIN paper_embeddings_v2 e ON p.id = e.paper_id
                WHERE e.paper_id IS NULL
            """)
            papers = [dict(row) for row in cursor.fetchall()]
        
        if not papers:
            print("✅ All papers already have embeddings")
            return 0
        
        print(f"📊 Generating embeddings for {len(papers)} papers...")
        
        # Prepare texts (title + abstract + preview)
        texts = []
        paper_ids = []
        for p in papers:
            text_parts = [p["title"] or ""]
            if p["abstract"]:
                text_parts.append(p["abstract"])
            if p["full_text"]:
                # Use first 2000 chars of full text
                text_parts.append(p["full_text"][:2000])
            texts.append(" ".join(text_parts))
            paper_ids.append(p["id"])
        
        # Generate embeddings in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")
            embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.extend(embeddings)
        
        # Store embeddings
        with self._get_conn() as conn:
            for paper_id, embedding in zip(paper_ids, all_embeddings):
                conn.execute("""
                    INSERT OR REPLACE INTO paper_embeddings_v2 
                    (paper_id, model_name, embedding, embedding_dim)
                    VALUES (?, ?, ?, ?)
                """, (paper_id, self.embedding_model_name, 
                      embedding.tobytes(), len(embedding)))
            conn.commit()
        
        print(f"✅ Generated {len(all_embeddings)} embeddings")
        return len(all_embeddings)
    
    def get_paper_embedding(self, paper_id: str) -> Optional[np.ndarray]:
        """Get embedding for a specific paper."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT embedding, embedding_dim FROM paper_embeddings_v2
                WHERE paper_id = ?
            """, (paper_id,))
            row = cursor.fetchone()
            if row:
                return np.frombuffer(row["embedding"], dtype=np.float32)
        return None
    
    def get_all_embeddings(self) -> Tuple[List[str], np.ndarray]:
        """Get all paper embeddings as a matrix."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT paper_id, embedding, embedding_dim FROM paper_embeddings_v2
            """)
            rows = cursor.fetchall()
        
        if not rows:
            return [], np.array([])
        
        paper_ids = [row["paper_id"] for row in rows]
        embeddings = np.array([
            np.frombuffer(row["embedding"], dtype=np.float32) 
            for row in rows
        ])
        return paper_ids, embeddings
    
    # =========================================================================
    # AUTOMATIC CLASSIFICATION
    # =========================================================================
    
    def classify_papers_by_clustering(
        self,
        n_clusters: Optional[int] = None,
        min_cluster_size: int = 3
    ) -> Dict[int, List[str]]:
        """Classify papers into clusters using embeddings."""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn not installed. Run: pip install scikit-learn")
        
        paper_ids, embeddings = self.get_all_embeddings()
        if len(paper_ids) == 0:
            print("❌ No embeddings found. Run generate_paper_embeddings() first.")
            return {}
        
        print(f"📊 Clustering {len(paper_ids)} papers...")
        
        # Auto-determine cluster count if not specified
        if n_clusters is None:
            # Heuristic: sqrt(n) clusters, minimum 3
            n_clusters = max(3, int(np.sqrt(len(paper_ids))))
        
        # Use Agglomerative Clustering for hierarchical structure
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(embeddings)
        
        # Group papers by cluster
        clusters = defaultdict(list)
        for paper_id, label in zip(paper_ids, labels):
            clusters[int(label)].append(paper_id)
        
        print(f"✅ Created {len(clusters)} clusters")
        for label, papers in sorted(clusters.items()):
            print(f"   Cluster {label}: {len(papers)} papers")
        
        return dict(clusters)
    
    def classify_papers_by_keywords(self) -> int:
        """Classify papers into topics based on keyword matching."""
        with self._get_conn() as conn:
            # Get all topics with keywords
            cursor = conn.execute("""
                SELECT id, name, keywords FROM taxonomy_topics
                WHERE keywords IS NOT NULL AND keywords != '[]'
            """)
            topics = [dict(row) for row in cursor.fetchall()]
            
            # Get all papers
            cursor = conn.execute("""
                SELECT id, title, abstract, full_text FROM research_papers
            """)
            papers = [dict(row) for row in cursor.fetchall()]
        
        classified = 0
        for paper in papers:
            text = " ".join([
                paper["title"] or "",
                paper["abstract"] or "",
                (paper["full_text"] or "")[:5000]
            ]).lower()
            
            for topic in topics:
                keywords = json.loads(topic["keywords"])
                matches = sum(1 for kw in keywords if kw.lower() in text)
                
                if matches > 0:
                    confidence = min(1.0, matches / len(keywords))
                    self._add_paper_topic(paper["id"], topic["id"], confidence, "keyword")
                    classified += 1
        
        print(f"✅ Created {classified} paper-topic associations via keywords")
        return classified
    
    def classify_papers_by_similarity(
        self,
        similarity_threshold: float = 0.5
    ) -> int:
        """Classify papers by similarity to topic representative texts."""
        model = self._load_model()
        
        with self._get_conn() as conn:
            # Get topics with descriptions
            cursor = conn.execute("""
                SELECT id, name, description, keywords FROM taxonomy_topics
            """)
            topics = [dict(row) for row in cursor.fetchall()]
            
            # Get paper embeddings
            paper_ids, paper_embeddings = self.get_all_embeddings()
        
        if len(paper_ids) == 0:
            print("❌ No embeddings found. Run generate_paper_embeddings() first.")
            return 0
        
        # Create topic embeddings from description + keywords
        topic_texts = []
        topic_ids = []
        for topic in topics:
            text = topic["description"] or topic["name"]
            keywords = json.loads(topic["keywords"]) if topic["keywords"] else []
            if keywords:
                text += " " + " ".join(keywords)
            topic_texts.append(text)
            topic_ids.append(topic["id"])
        
        print(f"📊 Computing similarity to {len(topics)} topics...")
        topic_embeddings = model.encode(topic_texts, convert_to_numpy=True)
        
        # Compute similarities
        similarities = cosine_similarity(paper_embeddings, topic_embeddings)
        
        classified = 0
        for i, paper_id in enumerate(paper_ids):
            for j, topic_id in enumerate(topic_ids):
                if similarities[i, j] >= similarity_threshold:
                    self._add_paper_topic(paper_id, topic_id, float(similarities[i, j]), "similarity")
                    classified += 1
        
        print(f"✅ Created {classified} paper-topic associations via similarity")
        return classified
    
    def _add_paper_topic(
        self,
        paper_id: str,
        topic_id: str,
        confidence: float,
        source: str
    ):
        """Add a paper-topic association."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO paper_topics 
                (paper_id, topic_id, confidence, source)
                VALUES (?, ?, ?, ?)
            """, (paper_id, topic_id, confidence, source))
            conn.commit()
    
    # =========================================================================
    # SMART LINKING
    # =========================================================================
    
    def compute_paper_similarities(
        self,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> int:
        """Compute and store paper-to-paper similarities."""
        paper_ids, embeddings = self.get_all_embeddings()
        
        if len(paper_ids) < 2:
            print("❌ Need at least 2 papers with embeddings")
            return 0
        
        print(f"📊 Computing similarities between {len(paper_ids)} papers...")
        
        # Compute pairwise cosine similarities
        similarities = cosine_similarity(embeddings)
        
        links_created = 0
        with self._get_conn() as conn:
            for i, source_id in enumerate(paper_ids):
                # Get top-k similar papers (excluding self)
                sim_scores = similarities[i].copy()
                sim_scores[i] = -1  # Exclude self
                
                top_indices = np.argsort(sim_scores)[-top_k:][::-1]
                
                for j in top_indices:
                    if sim_scores[j] >= min_similarity:
                        target_id = paper_ids[j]
                        conn.execute("""
                            INSERT OR REPLACE INTO paper_links
                            (source_paper_id, target_paper_id, link_type, similarity_score, confidence)
                            VALUES (?, ?, 'similar', ?, ?)
                        """, (source_id, target_id, float(sim_scores[j]), float(sim_scores[j])))
                        links_created += 1
            
            conn.commit()
        
        print(f"✅ Created {links_created} similarity links")
        return links_created
    
    def find_similar_papers(
        self,
        paper_id: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find papers similar to a given paper."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT 
                    p.id, p.title, p.abstract, 
                    l.similarity_score
                FROM paper_links l
                JOIN research_papers p ON l.target_paper_id = p.id
                WHERE l.source_paper_id = ? AND l.link_type = 'similar'
                ORDER BY l.similarity_score DESC
                LIMIT ?
            """, (paper_id, top_k))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_paper_graph(self) -> Dict[str, Any]:
        """Get the full paper similarity graph."""
        with self._get_conn() as conn:
            # Nodes
            cursor = conn.execute("""
                SELECT id, title FROM research_papers
            """)
            nodes = [{"id": row["id"], "title": row["title"]} for row in cursor.fetchall()]
            
            # Edges
            cursor = conn.execute("""
                SELECT source_paper_id, target_paper_id, similarity_score, link_type
                FROM paper_links
            """)
            edges = [dict(row) for row in cursor.fetchall()]
        
        return {"nodes": nodes, "edges": edges}
    
    # =========================================================================
    # TOPIC DISCOVERY (AUTOMATIC)
    # =========================================================================
    
    def discover_topics_from_clusters(
        self,
        n_clusters: int = 10
    ) -> List[Dict[str, Any]]:
        """Discover topics automatically from paper clusters."""
        clusters = self.classify_papers_by_clustering(n_clusters=n_clusters)
        
        discovered_topics = []
        with self._get_conn() as conn:
            for cluster_id, paper_ids in clusters.items():
                # Get titles and abstracts for cluster
                placeholders = ",".join("?" * len(paper_ids))
                cursor = conn.execute(f"""
                    SELECT title, abstract FROM research_papers
                    WHERE id IN ({placeholders})
                """, paper_ids)
                papers = cursor.fetchall()
                
                # Extract common words (simple approach)
                all_text = " ".join([
                    (p["title"] or "") + " " + (p["abstract"] or "")
                    for p in papers
                ]).lower()
                
                # Count words (exclude stopwords)
                stopwords = {"the", "a", "an", "in", "on", "at", "for", "to", "of", 
                            "and", "or", "is", "are", "was", "were", "with", "this",
                            "that", "we", "our", "from", "by", "as", "be", "can"}
                words = [w for w in all_text.split() if w.isalpha() and w not in stopwords and len(w) > 3]
                word_counts = defaultdict(int)
                for w in words:
                    word_counts[w] += 1
                
                # Top keywords
                top_keywords = sorted(word_counts.items(), key=lambda x: -x[1])[:10]
                
                discovered_topics.append({
                    "cluster_id": cluster_id,
                    "paper_count": len(paper_ids),
                    "paper_ids": paper_ids,
                    "top_keywords": [w for w, c in top_keywords],
                    "suggested_name": "_".join([w for w, c in top_keywords[:3]])
                })
        
        return discovered_topics
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def get_organization_stats(self) -> Dict[str, Any]:
        """Get statistics about paper organization."""
        with self._get_conn() as conn:
            stats = {}
            
            # Paper counts
            stats["total_papers"] = conn.execute(
                "SELECT COUNT(*) FROM research_papers"
            ).fetchone()[0]
            
            stats["papers_with_embeddings"] = conn.execute(
                "SELECT COUNT(*) FROM paper_embeddings_v2"
            ).fetchone()[0]
            
            stats["papers_with_topics"] = conn.execute(
                "SELECT COUNT(DISTINCT paper_id) FROM paper_topics"
            ).fetchone()[0]
            
            # Topic counts
            stats["total_topics"] = conn.execute(
                "SELECT COUNT(*) FROM taxonomy_topics"
            ).fetchone()[0]
            
            # Link counts
            stats["total_links"] = conn.execute(
                "SELECT COUNT(*) FROM paper_links"
            ).fetchone()[0]
            
            # Links by type
            cursor = conn.execute("""
                SELECT link_type, COUNT(*) as count 
                FROM paper_links GROUP BY link_type
            """)
            stats["links_by_type"] = {row["link_type"]: row["count"] for row in cursor.fetchall()}
            
        return stats
    
    def print_organization_report(self):
        """Print a formatted organization report."""
        stats = self.get_organization_stats()
        
        print("\n" + "="*60)
        print("📚 RESEARCH PAPER ORGANIZATION REPORT")
        print("="*60)
        
        print(f"\n📄 Papers")
        print(f"   Total: {stats['total_papers']}")
        print(f"   With embeddings: {stats['papers_with_embeddings']}")
        print(f"   With topics: {stats['papers_with_topics']}")
        
        print(f"\n🏷️  Topics")
        print(f"   Total: {stats['total_topics']}")
        
        print(f"\n🔗 Links")
        print(f"   Total: {stats['total_links']}")
        for link_type, count in stats.get("links_by_type", {}).items():
            print(f"   - {link_type}: {count}")
        
        print("\n" + "="*60)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Research Paper Smart Organizer")
    parser.add_argument("command", choices=[
        "init", "embed", "classify", "link", "discover", "report", "full"
    ])
    parser.add_argument("--db", default=".workspace/research_papers.db")
    parser.add_argument("--model", default="all-mpnet-base-v2")
    parser.add_argument("--clusters", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=0.3)
    parser.add_argument("--top-k", type=int, default=5)
    
    args = parser.parse_args()
    
    organizer = ResearchSmartOrganizer(
        db_path=args.db,
        embedding_model=args.model
    )
    
    if args.command == "init":
        organizer.init_default_taxonomy()
        
    elif args.command == "embed":
        organizer.generate_paper_embeddings()
        
    elif args.command == "classify":
        organizer.classify_papers_by_keywords()
        organizer.classify_papers_by_similarity()
        
    elif args.command == "link":
        organizer.compute_paper_similarities(
            top_k=args.top_k,
            min_similarity=args.threshold
        )
        
    elif args.command == "discover":
        topics = organizer.discover_topics_from_clusters(
            n_clusters=args.clusters or 10
        )
        print("\n📊 Discovered Topics:")
        for t in topics:
            print(f"\n  Cluster {t['cluster_id']} ({t['paper_count']} papers)")
            print(f"  Keywords: {', '.join(t['top_keywords'][:5])}")
            print(f"  Suggested: {t['suggested_name']}")
        
    elif args.command == "report":
        organizer.print_organization_report()
        
    elif args.command == "full":
        print("\n🚀 Running full organization pipeline...\n")
        organizer.init_default_taxonomy()
        organizer.generate_paper_embeddings()
        organizer.classify_papers_by_keywords()
        organizer.classify_papers_by_similarity()
        organizer.compute_paper_similarities(top_k=args.top_k, min_similarity=args.threshold)
        organizer.print_organization_report()


if __name__ == "__main__":
    main()
