"""Cross-Database Linking Service.

Enables relationships between the three AIKH databases:
- research.db: Academic papers and embeddings
- knowledge.db: Workspace artifacts (ADRs, specs, discussions)
- chatlogs.db: AI conversation history

This service provides a unified view and cross-referencing capabilities.
"""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CrossLink:
    """Represents a link between entities in different databases."""
    source_db: str  # 'research', 'knowledge', 'chatlogs'
    source_id: str
    source_type: str  # 'paper', 'document', 'chat_turn'
    target_db: str
    target_id: str
    target_type: str
    link_type: str  # 'cites', 'discusses', 'implements', 'references'
    confidence: float = 1.0
    context: Optional[str] = None


class CrossLinkService:
    """Service for managing cross-database relationships."""

    def __init__(self):
        self.db_paths = {
            'research': self._get_research_db(),
            'knowledge': self._get_knowledge_db(),
            'chatlogs': self._get_chatlogs_db(),
        }
        self._init_link_table()

    def _get_research_db(self) -> Path:
        if Path("/aikh/research.db").exists():
            return Path("/aikh/research.db")
        if aikh_home := os.getenv("AIKH_HOME"):
            return Path(aikh_home) / "research.db"
        return Path.home() / ".aikh" / "research.db"

    def _get_knowledge_db(self) -> Path:
        workspace = Path(os.getenv("WORKSPACE_ROOT", "."))
        return workspace / ".workspace" / "knowledge.db"

    def _get_chatlogs_db(self) -> Path:
        if Path("/aikh/chatlogs.db").exists():
            return Path("/aikh/chatlogs.db")
        if aikh_home := os.getenv("AIKH_HOME"):
            return Path(aikh_home) / "chatlogs.db"
        return Path.home() / ".aikh" / "chatlogs.db"

    def _init_link_table(self):
        """Initialize cross-link table in knowledge.db (central hub)."""
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
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source_db, source_id, target_db, target_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_crosslinks_source 
            ON cross_links(source_db, source_id);
        CREATE INDEX IF NOT EXISTS idx_crosslinks_target 
            ON cross_links(target_db, target_id);
        CREATE INDEX IF NOT EXISTS idx_crosslinks_type ON cross_links(link_type);
        """
        db_path = self.db_paths['knowledge']
        if db_path.exists():
            with sqlite3.connect(db_path) as conn:
                conn.executescript(schema)

    def add_link(self, link: CrossLink) -> bool:
        """Add a cross-database link."""
        db_path = self.db_paths['knowledge']
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cross_links
                    (source_db, source_id, source_type, target_db, target_id, 
                     target_type, link_type, confidence, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (link.source_db, link.source_id, link.source_type,
                      link.target_db, link.target_id, link.target_type,
                      link.link_type, link.confidence, link.context))
                return True
        except Exception:
            return False

    def get_links_from(self, db: str, entity_id: str) -> list[CrossLink]:
        """Get all links originating from an entity."""
        db_path = self.db_paths['knowledge']
        links = []
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM cross_links
                    WHERE source_db = ? AND source_id = ?
                """, (db, entity_id))
                for row in cursor:
                    links.append(CrossLink(
                        source_db=row['source_db'],
                        source_id=row['source_id'],
                        source_type=row['source_type'],
                        target_db=row['target_db'],
                        target_id=row['target_id'],
                        target_type=row['target_type'],
                        link_type=row['link_type'],
                        confidence=row['confidence'],
                        context=row['context']
                    ))
        except Exception:
            pass
        return links

    def get_links_to(self, db: str, entity_id: str) -> list[CrossLink]:
        """Get all links pointing to an entity."""
        db_path = self.db_paths['knowledge']
        links = []
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM cross_links
                    WHERE target_db = ? AND target_id = ?
                """, (db, entity_id))
                for row in cursor:
                    links.append(CrossLink(
                        source_db=row['source_db'],
                        source_id=row['source_id'],
                        source_type=row['source_type'],
                        target_db=row['target_db'],
                        target_id=row['target_id'],
                        target_type=row['target_type'],
                        link_type=row['link_type'],
                        confidence=row['confidence'],
                        context=row['context']
                    ))
        except Exception:
            pass
        return links

    def find_paper_citations_in_artifacts(self) -> list[CrossLink]:
        """Scan artifacts for paper citations and create links.
        
        Looks for patterns like:
        - arXiv:XXXX.XXXXX
        - [Author et al., YEAR]
        - DOI references
        """
        links = []
        research_db = self.db_paths['research']
        knowledge_db = self.db_paths['knowledge']
        
        if not research_db.exists() or not knowledge_db.exists():
            return links

        # Get all papers with their identifiers
        papers = {}
        with sqlite3.connect(research_db) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute(
                "SELECT id, arxiv_id, doi, title FROM research_papers"
            ):
                if row['arxiv_id']:
                    papers[row['arxiv_id']] = row['id']
                if row['doi']:
                    papers[row['doi']] = row['id']

        # Scan documents for citations
        with sqlite3.connect(knowledge_db) as conn:
            conn.row_factory = sqlite3.Row
            for doc in conn.execute("SELECT id, content FROM documents"):
                content = doc['content']
                for identifier, paper_id in papers.items():
                    if identifier in content:
                        link = CrossLink(
                            source_db='knowledge',
                            source_id=doc['id'],
                            source_type='document',
                            target_db='research',
                            target_id=paper_id,
                            target_type='paper',
                            link_type='cites',
                            confidence=1.0,
                            context=f"Found {identifier} in document"
                        )
                        links.append(link)
                        self.add_link(link)

        return links

    def get_stats(self) -> dict:
        """Get cross-link statistics."""
        db_path = self.db_paths['knowledge']
        stats = {'total_links': 0, 'by_type': {}, 'by_source_db': {}}
        
        try:
            with sqlite3.connect(db_path) as conn:
                # Total
                cursor = conn.execute("SELECT COUNT(*) FROM cross_links")
                stats['total_links'] = cursor.fetchone()[0]
                
                # By type
                for row in conn.execute(
                    "SELECT link_type, COUNT(*) FROM cross_links GROUP BY link_type"
                ):
                    stats['by_type'][row[0]] = row[1]
                
                # By source DB
                for row in conn.execute(
                    "SELECT source_db, COUNT(*) FROM cross_links GROUP BY source_db"
                ):
                    stats['by_source_db'][row[0]] = row[1]
        except Exception:
            pass

        return stats
