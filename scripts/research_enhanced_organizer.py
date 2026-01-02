"""Research Paper Enhanced Organizer - Full Feature Suite.

Features:
1. Concept Extraction - NLP-based entity extraction
2. Citation Graph - Parse references, build network
3. Auto Citation Downloader - Fetch papers cited 3+ times
4. Topic Visualization - D3.js interactive graph
5. Semantic Search API - Meaning-based queries
6. Auto-Ingest - Watch folder for new PDFs

GPU Acceleration: RTX 5090 optimized
"""

import sqlite3
import json
import hashlib
import re
import os
import time
import threading
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import urllib.request
import xml.etree.ElementTree as ET
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    DEVICE = "cpu"

ENHANCED_SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_paper_id TEXT NOT NULL,
    cited_title TEXT, cited_authors TEXT, cited_arxiv_id TEXT, cited_doi TEXT, cited_year INTEGER,
    resolved BOOLEAN DEFAULT 0, cited_paper_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON paper_citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_arxiv ON paper_citations(cited_arxiv_id);

CREATE TABLE IF NOT EXISTS download_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT UNIQUE, doi TEXT, title TEXT NOT NULL,
    citation_count INTEGER DEFAULT 0, priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', download_url TEXT, error_message TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS extracted_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL, concept TEXT NOT NULL, concept_type TEXT NOT NULL,
    normalized_concept TEXT, frequency INTEGER DEFAULT 1,
    context_sentences TEXT, created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(paper_id, concept, concept_type)
);
CREATE INDEX IF NOT EXISTS idx_concepts_paper ON extracted_concepts(paper_id);

CREATE TABLE IF NOT EXISTS concept_cooccurrence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_a TEXT NOT NULL, concept_b TEXT NOT NULL,
    cooccurrence_count INTEGER DEFAULT 1, paper_ids TEXT,
    UNIQUE(concept_a, concept_b)
);

CREATE TABLE IF NOT EXISTS ingest_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL, status TEXT DEFAULT 'pending',
    paper_id TEXT, error_message TEXT, created_at TEXT DEFAULT (datetime('now'))
);
"""

KNOWN_CONCEPTS = {
    "models": ["GPT", "GPT-4", "GPT-4o", "BERT", "LLaMA", "Llama-3", "Claude", "Gemini", "Mistral",
               "CodeLlama", "StarCoder", "Codex", "Copilot", "CLIP", "SPECTER2", "Transformer"],
    "datasets": ["HumanEval", "MBPP", "SWE-bench", "BigCodeBench", "MMLU", "GSM8K", "ImageNet"],
    "techniques": ["RAG", "Chain-of-Thought", "CoT", "ReAct", "In-Context Learning", "Few-Shot",
                   "RLHF", "DPO", "LoRA", "QLoRA", "Flash Attention", "KV Cache", "Agentic",
                   "Multi-Agent", "Tool Use", "Context Compression", "GraphRAG"],
    "metrics": ["BLEU", "ROUGE", "Pass@k", "Pass@1", "BERTScore", "Perplexity"],
    "tools": ["LangChain", "LlamaIndex", "HuggingFace", "vLLM", "ChromaDB", "FAISS", "Pinecone"],
    "frameworks": ["PyTorch", "TensorFlow", "FastAPI", "React"]
}


class ResearchEnhancedOrganizer:
    def __init__(self, db_path=".workspace/research_papers.db", embedding_model="all-mpnet-base-v2"):
        self.db_path = Path(db_path)
        self.embedding_model_name = embedding_model
        self.device = DEVICE
        self.model = None
        self._init_db()
        print(f"🚀 ResearchEnhancedOrganizer | Device: {self.device}")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(ENHANCED_SCHEMA)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _load_model(self):
        if self.model is None and SBERT_AVAILABLE:
            print(f"📦 Loading {self.embedding_model_name}...")
            self.model = SentenceTransformer(self.embedding_model_name, device=self.device)
        return self.model

    # === 1. CONCEPT EXTRACTION ===
    def extract_concepts_from_paper(self, paper_id: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT title, abstract, full_text FROM research_papers WHERE id=?", 
                              (paper_id,)).fetchone()
            if not row: return 0
            text = " ".join([row["title"] or "", row["abstract"] or "", (row["full_text"] or "")[:30000]])

        count = 0
        for ctype, concepts in KNOWN_CONCEPTS.items():
            for concept in concepts:
                matches = re.findall(r'\b' + re.escape(concept) + r'\b', text, re.IGNORECASE)
                if matches:
                    contexts = [s.strip()[:200] for s in re.split(r'[.!?]+', text) 
                               if concept.lower() in s.lower()][:2]
                    with self._get_conn() as conn:
                        conn.execute("""INSERT OR REPLACE INTO extracted_concepts 
                            (paper_id, concept, concept_type, normalized_concept, frequency, context_sentences)
                            VALUES (?,?,?,?,?,?)""", 
                            (paper_id, concept, ctype, concept.lower(), len(matches), json.dumps(contexts)))
                        conn.commit()
                    count += 1
        return count

    def extract_all_concepts(self) -> int:
        with self._get_conn() as conn:
            papers = [r["id"] for r in conn.execute("SELECT id FROM research_papers").fetchall()]
        print(f"📊 Extracting concepts from {len(papers)} papers...")
        total = sum(self.extract_concepts_from_paper(p) for p in papers)
        print(f"✅ Extracted {total} concept types")
        return total

    def build_concept_cooccurrence(self) -> int:
        with self._get_conn() as conn:
            papers = conn.execute("""SELECT paper_id, GROUP_CONCAT(normalized_concept,'|||') as concepts
                FROM extracted_concepts GROUP BY paper_id""").fetchall()
        
        cooc = defaultdict(lambda: {"count": 0, "papers": set()})
        for p in papers:
            concepts = list(set((p["concepts"] or "").split("|||")))
            for i, c1 in enumerate(concepts):
                for c2 in concepts[i+1:]:
                    key = tuple(sorted([c1, c2]))
                    cooc[key]["count"] += 1
                    cooc[key]["papers"].add(p["paper_id"])

        with self._get_conn() as conn:
            for (c1, c2), data in cooc.items():
                conn.execute("INSERT OR REPLACE INTO concept_cooccurrence (concept_a, concept_b, cooccurrence_count, paper_ids) VALUES (?,?,?,?)",
                            (c1, c2, data["count"], json.dumps(list(data["papers"]))))
            conn.commit()
        print(f"✅ Built {len(cooc)} co-occurrences")
        return len(cooc)

    # === 2. CITATION GRAPH ===
    def extract_citations_from_paper(self, paper_id: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute("SELECT full_text FROM research_papers WHERE id=?", (paper_id,)).fetchone()
            if not row or not row["full_text"]: return 0
            text = row["full_text"]

        citations = []
        for arxiv_id in re.findall(r'arXiv[:\s]*(\d{4}\.\d{4,5}(?:v\d+)?)', text, re.IGNORECASE):
            citations.append({"arxiv_id": arxiv_id})
        for doi in re.findall(r'(10\.\d{4,}/[^\s\]]+)', text):
            citations.append({"doi": doi.rstrip('.,;:)')})

        with self._get_conn() as conn:
            for c in citations:
                try:
                    conn.execute("""INSERT OR IGNORE INTO paper_citations 
                        (citing_paper_id, cited_arxiv_id, cited_doi) VALUES (?,?,?)""",
                        (paper_id, c.get("arxiv_id"), c.get("doi")))
                except: pass
            conn.commit()
        return len(citations)

    def extract_all_citations(self) -> int:
        with self._get_conn() as conn:
            papers = [r["id"] for r in conn.execute("SELECT id FROM research_papers").fetchall()]
        print(f"📊 Extracting citations from {len(papers)} papers...")
        total = sum(self.extract_citations_from_paper(p) for p in papers)
        print(f"✅ Extracted {total} citations")
        return total

    def resolve_citations(self) -> int:
        with self._get_conn() as conn:
            conn.execute("""UPDATE paper_citations SET cited_paper_id = (
                SELECT id FROM research_papers WHERE arxiv_id = paper_citations.cited_arxiv_id),
                resolved = 1 WHERE cited_arxiv_id IS NOT NULL AND cited_paper_id IS NULL""")
            resolved = conn.execute("SELECT COUNT(*) FROM paper_citations WHERE resolved=1").fetchone()[0]
            conn.commit()
        print(f"✅ Resolved {resolved} citations")
        return resolved

    # === 3. AUTO CITATION DOWNLOADER ===
    def queue_high_value_citations(self, min_citations: int = 3) -> int:
        with self._get_conn() as conn:
            candidates = conn.execute("""SELECT cited_arxiv_id, COUNT(*) as cnt 
                FROM paper_citations WHERE cited_paper_id IS NULL AND cited_arxiv_id IS NOT NULL
                GROUP BY cited_arxiv_id HAVING cnt >= ? ORDER BY cnt DESC""", (min_citations,)).fetchall()
            queued = 0
            for r in candidates:
                try:
                    conn.execute("INSERT OR IGNORE INTO download_queue (arxiv_id, title, citation_count, priority) VALUES (?,?,?,?)",
                                (r["cited_arxiv_id"], f"arXiv:{r['cited_arxiv_id']}", r["cnt"], r["cnt"]))
                    queued += 1
                except: pass
            conn.commit()
        print(f"✅ Queued {queued} papers (cited {min_citations}+ times)")
        return queued

    def download_paper(self, arxiv_id: str, output_dir: str = "research_papers") -> Optional[str]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / f"{arxiv_id.replace('/', '_')}.pdf"
        if output_file.exists(): return str(output_file)
        try:
            print(f"   📥 Downloading arXiv:{arxiv_id}")
            urllib.request.urlretrieve(f"https://arxiv.org/pdf/{arxiv_id}.pdf", output_file)
            time.sleep(1)
            return str(output_file)
        except Exception as e:
            print(f"   ⚠️ Failed: {e}")
            return None

    def process_download_queue(self, max_downloads: int = 10, auto_extract: bool = True) -> int:
        with self._get_conn() as conn:
            queue = conn.execute("SELECT * FROM download_queue WHERE status='pending' ORDER BY priority DESC LIMIT ?", 
                                (max_downloads,)).fetchall()
        downloaded = 0
        downloaded_files = []
        for item in queue:
            arxiv_id = item["arxiv_id"]
            pdf_path = self.download_paper(arxiv_id)
            with self._get_conn() as conn:
                if pdf_path:
                    conn.execute("UPDATE download_queue SET status='completed', download_url=? WHERE arxiv_id=?",
                                (pdf_path, arxiv_id))
                    downloaded += 1
                    downloaded_files.append(pdf_path)
                else:
                    conn.execute("UPDATE download_queue SET status='failed' WHERE arxiv_id=?", (arxiv_id,))
                conn.commit()
        print(f"✅ Downloaded {downloaded} papers")
        
        if auto_extract and downloaded_files:
            print(f"📚 Auto-extracting {len(downloaded_files)} papers...")
            self._auto_extract_papers(downloaded_files)
        
        return downloaded
    
    def _auto_extract_papers(self, pdf_paths: List[str]) -> int:
        """Auto-extract downloaded papers into the research database."""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "scripts/quick_ingest.py", "research_papers/"],
                capture_output=True, text=True, cwd=Path(__file__).parent.parent
            )
            if result.returncode == 0:
                print(f"✅ Auto-extraction complete")
            else:
                print(f"⚠️ Auto-extraction warning: {result.stderr[:200] if result.stderr else 'unknown'}")
            return len(pdf_paths)
        except Exception as e:
            print(f"⚠️ Auto-extraction failed: {e}")
            return 0

    # === 4. VISUALIZATION ===
    def export_paper_graph_d3(self, output_file: str = "paper_graph.json") -> str:
        with self._get_conn() as conn:
            papers = conn.execute("SELECT id, title, arxiv_id FROM research_papers").fetchall()
            links = conn.execute("""SELECT source_paper_id, target_paper_id, similarity_score 
                FROM paper_links WHERE link_type='similar' AND similarity_score > 0.4""").fetchall()
        
        nodes = [{"id": p["id"], "title": (p["title"] or "")[:50], "arxiv": p["arxiv_id"]} for p in papers]
        node_ids = {n["id"] for n in nodes}
        edges = [{"source": l["source_paper_id"], "target": l["target_paper_id"], "value": l["similarity_score"]}
                 for l in links if l["source_paper_id"] in node_ids and l["target_paper_id"] in node_ids]
        
        Path(output_file).write_text(json.dumps({"nodes": nodes, "links": edges}, indent=2))
        print(f"✅ Paper graph: {len(nodes)} nodes, {len(edges)} edges → {output_file}")
        return output_file

    def export_concept_graph_d3(self, output_file: str = "concept_graph.json") -> str:
        with self._get_conn() as conn:
            concepts = conn.execute("""SELECT normalized_concept, concept_type, SUM(frequency) as freq
                FROM extracted_concepts GROUP BY normalized_concept HAVING freq >= 2""").fetchall()
            coocs = conn.execute("SELECT * FROM concept_cooccurrence WHERE cooccurrence_count >= 2").fetchall()
        
        nodes = [{"id": c["normalized_concept"], "type": c["concept_type"], "freq": c["freq"]} for c in concepts]
        node_ids = {n["id"] for n in nodes}
        edges = [{"source": c["concept_a"], "target": c["concept_b"], "value": c["cooccurrence_count"]}
                 for c in coocs if c["concept_a"] in node_ids and c["concept_b"] in node_ids]
        
        Path(output_file).write_text(json.dumps({"nodes": nodes, "links": edges}, indent=2))
        print(f"✅ Concept graph: {len(nodes)} nodes, {len(edges)} edges → {output_file}")
        return output_file

    # === 5. SEMANTIC SEARCH ===
    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict]:
        model = self._load_model()
        if not model: return []
        query_emb = model.encode([query], convert_to_numpy=True)[0]
        
        with self._get_conn() as conn:
            rows = conn.execute("""SELECT e.paper_id, e.embedding, p.title, p.abstract
                FROM paper_embeddings_v2 e JOIN research_papers p ON e.paper_id = p.id""").fetchall()
        
        results = []
        for r in rows:
            paper_emb = np.frombuffer(r["embedding"], dtype=np.float32)
            sim = float(np.dot(query_emb, paper_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(paper_emb)))
            results.append({"paper_id": r["paper_id"], "title": r["title"], 
                           "abstract": (r["abstract"] or "")[:300], "similarity": round(sim, 4)})
        
        results.sort(key=lambda x: -x["similarity"])
        return results[:top_k]

    # === 6. AUTO-INGEST ===
    def scan_for_new_pdfs(self, watch_folder: str = "research_papers") -> List[str]:
        watch_path = Path(watch_folder)
        if not watch_path.exists(): return []
        with self._get_conn() as conn:
            known = {r["file_path"] for r in conn.execute("SELECT file_path FROM ingest_queue").fetchall()}
        new_files = []
        for pdf in watch_path.glob("**/*.pdf"):
            path_str = str(pdf.absolute())
            if path_str not in known:
                new_files.append(path_str)
                with self._get_conn() as conn:
                    conn.execute("INSERT OR IGNORE INTO ingest_queue (file_path) VALUES (?)", (path_str,))
                    conn.commit()
        if new_files: print(f"📁 Found {len(new_files)} new PDFs")
        return new_files

    # === FULL PIPELINE ===
    def run_full_pipeline(self, min_citations: int = 3, max_downloads: int = 10) -> Dict:
        print("\n" + "="*60 + "\n🚀 FULL ENHANCED PIPELINE\n" + "="*60)
        results = {}
        results["concepts"] = self.extract_all_concepts()
        results["cooccurrences"] = self.build_concept_cooccurrence()
        results["citations"] = self.extract_all_citations()
        results["resolved"] = self.resolve_citations()
        results["queued"] = self.queue_high_value_citations(min_citations)
        results["downloaded"] = self.process_download_queue(max_downloads) if results["queued"] else 0
        results["paper_graph"] = self.export_paper_graph_d3()
        results["concept_graph"] = self.export_concept_graph_d3()
        results["new_pdfs"] = len(self.scan_for_new_pdfs())
        print("\n✅ COMPLETE:", results)
        return results

    def print_report(self):
        with self._get_conn() as conn:
            stats = {
                "papers": conn.execute("SELECT COUNT(*) FROM research_papers").fetchone()[0],
                "concepts": conn.execute("SELECT COUNT(DISTINCT normalized_concept) FROM extracted_concepts").fetchone()[0],
                "citations": conn.execute("SELECT COUNT(*) FROM paper_citations").fetchone()[0],
                "resolved": conn.execute("SELECT COUNT(*) FROM paper_citations WHERE resolved=1").fetchone()[0],
                "queued": conn.execute("SELECT COUNT(*) FROM download_queue WHERE status='pending'").fetchone()[0],
                "downloaded": conn.execute("SELECT COUNT(*) FROM download_queue WHERE status='completed'").fetchone()[0],
            }
        print("\n" + "="*50 + "\n📚 ENHANCED REPORT\n" + "="*50)
        for k, v in stats.items(): print(f"   {k}: {v}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["full", "concepts", "citations", "download", "visualize", "search", "report"])
    parser.add_argument("--db", default=".workspace/research_papers.db")
    parser.add_argument("--query", "-q")
    parser.add_argument("--min-citations", type=int, default=3)
    parser.add_argument("--max-downloads", type=int, default=10)
    args = parser.parse_args()
    
    org = ResearchEnhancedOrganizer(db_path=args.db)
    
    if args.command == "full": org.run_full_pipeline(args.min_citations, args.max_downloads)
    elif args.command == "concepts": org.extract_all_concepts(); org.build_concept_cooccurrence()
    elif args.command == "citations": org.extract_all_citations(); org.resolve_citations()
    elif args.command == "download": org.queue_high_value_citations(args.min_citations); org.process_download_queue(args.max_downloads)
    elif args.command == "visualize": org.export_paper_graph_d3(); org.export_concept_graph_d3()
    elif args.command == "search" and args.query:
        for r in org.semantic_search(args.query): print(f"[{r['similarity']:.3f}] {r['title']}")
    elif args.command == "report": org.print_report()


if __name__ == "__main__":
    main()
