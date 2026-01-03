#!/usr/bin/env python3
"""Test AIKH (AI Knowledge Hub) database access and embedding functionality.

Tests:
1. Database connectivity for all three AIKH databases
2. Table structure verification
3. GPU/MPS availability for embeddings
4. Embedding generation test
5. Basic CRUD operations

Usage:
    python scripts/test_aikh_databases.py
"""

import os
import sys
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# AIKH paths
AIKH_HOME = Path(os.environ.get("AIKH_HOME", Path.home() / ".aikh"))
ARTIFACTS_DB = AIKH_HOME / "artifacts.db"
CHATLOGS_DB = AIKH_HOME / "chatlogs.db"
RESEARCH_DB = AIKH_HOME / "research.db"


def test_database_connection(db_path: Path, name: str) -> dict:
    """Test database connection and return info."""
    result = {
        "name": name,
        "path": str(db_path),
        "exists": db_path.exists(),
        "connected": False,
        "tables": [],
        "error": None
    }
    
    if not db_path.exists():
        result["error"] = "Database file not found"
        return result
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        result["connected"] = True
        
        # Get tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        result["tables"] = [row[0] for row in cursor.fetchall()]
        
        # Get size
        result["size_kb"] = db_path.stat().st_size / 1024
        
        conn.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


def test_artifacts_db() -> dict:
    """Test artifacts database with sample operations."""
    result = test_database_connection(ARTIFACTS_DB, "Artifacts")
    if not result["connected"]:
        return result
    
    try:
        conn = sqlite3.connect(ARTIFACTS_DB)
        conn.row_factory = sqlite3.Row
        
        # Test insert
        test_doc_id = f"test_doc_{int(time.time())}"
        conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (test_doc_id, "test", "Test Document", "Test content for AIKH", 
              f"/tmp/test_{test_doc_id}.md", "abc123"))
        conn.commit()
        
        # Test select
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (test_doc_id,))
        row = cursor.fetchone()
        result["crud_test"] = "INSERT/SELECT OK" if row else "SELECT FAILED"
        
        # Test delete
        conn.execute("DELETE FROM documents WHERE id = ?", (test_doc_id,))
        conn.commit()
        result["crud_test"] += " | DELETE OK"
        
        # Count existing records
        cursor = conn.execute("SELECT COUNT(*) FROM documents")
        result["document_count"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM chunks")
        result["chunk_count"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM embeddings")
        result["embedding_count"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


def test_chatlogs_db() -> dict:
    """Test chatlogs database with sample operations."""
    result = test_database_connection(CHATLOGS_DB, "Chatlogs")
    if not result["connected"]:
        return result
    
    try:
        conn = sqlite3.connect(CHATLOGS_DB)
        conn.row_factory = sqlite3.Row
        
        # Test insert
        test_id = int(time.time())
        conn.execute("""
            INSERT INTO chat_logs (file_path, filename, title, turn_count)
            VALUES (?, ?, ?, ?)
        """, (f"/tmp/test_{test_id}.md", f"test_{test_id}.md", "Test Chat", 0))
        conn.commit()
        
        # Test select
        cursor = conn.execute("SELECT * FROM chat_logs WHERE filename = ?", 
                              (f"test_{test_id}.md",))
        row = cursor.fetchone()
        result["crud_test"] = "INSERT/SELECT OK" if row else "SELECT FAILED"
        
        # Test delete
        conn.execute("DELETE FROM chat_logs WHERE filename = ?", (f"test_{test_id}.md",))
        conn.commit()
        result["crud_test"] += " | DELETE OK"
        
        # Count existing records
        cursor = conn.execute("SELECT COUNT(*) FROM chat_logs")
        result["chatlog_count"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM chat_turns")
        result["turn_count"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


def test_research_db() -> dict:
    """Test research database with sample operations."""
    result = test_database_connection(RESEARCH_DB, "Research")
    if not result["connected"]:
        return result
    
    try:
        conn = sqlite3.connect(RESEARCH_DB)
        conn.row_factory = sqlite3.Row
        
        # Test insert
        test_id = f"test_paper_{int(time.time())}"
        conn.execute("""
            INSERT INTO research_papers 
            (id, title, authors, source_path, content_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (test_id, "Test Paper", '["Test Author"]', "/tmp/test.pdf", "hash123"))
        conn.commit()
        
        # Test select
        cursor = conn.execute("SELECT * FROM research_papers WHERE id = ?", (test_id,))
        row = cursor.fetchone()
        result["crud_test"] = "INSERT/SELECT OK" if row else "SELECT FAILED"
        
        # Test delete
        conn.execute("DELETE FROM research_papers WHERE id = ?", (test_id,))
        conn.commit()
        result["crud_test"] += " | DELETE OK"
        
        # Count existing records
        cursor = conn.execute("SELECT COUNT(*) FROM research_papers")
        result["paper_count"] = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM paper_chunks")
        result["chunk_count"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        result["error"] = str(e)
    
    return result


def test_gpu_availability() -> dict:
    """Test GPU/MPS availability for embeddings."""
    result = {
        "pytorch_installed": False,
        "device": "cpu",
        "device_name": "CPU",
        "mps_available": False,
        "cuda_available": False,
    }
    
    try:
        import torch
        result["pytorch_installed"] = True
        result["pytorch_version"] = torch.__version__
        
        if torch.cuda.is_available():
            result["cuda_available"] = True
            result["device"] = "cuda"
            result["device_name"] = torch.cuda.get_device_name(0)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            result["mps_available"] = True
            result["device"] = "mps"
            result["device_name"] = "Apple Silicon (MPS)"
            
            # Quick MPS test
            try:
                x = torch.randn(100, 100, device="mps")
                y = x @ x.T
                result["mps_compute_test"] = "OK"
            except Exception as e:
                result["mps_compute_test"] = f"FAILED: {e}"
    except ImportError:
        result["error"] = "PyTorch not installed"
    
    return result


def test_embedding_generation() -> dict:
    """Test embedding generation with sentence-transformers."""
    result = {
        "sentence_transformers_installed": False,
        "model_loaded": False,
        "embedding_generated": False,
        "device_used": "cpu",
    }
    
    try:
        from sentence_transformers import SentenceTransformer
        result["sentence_transformers_installed"] = True
        
        # Determine device
        import torch
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        
        result["device_used"] = device
        
        # Load model (use small model for testing)
        print("      Loading embedding model (this may take a moment)...")
        start = time.time()
        model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        result["model_loaded"] = True
        result["model_load_time"] = f"{time.time() - start:.2f}s"
        
        # Generate test embedding
        test_text = "This is a test sentence for AIKH embedding generation."
        start = time.time()
        embedding = model.encode(test_text)
        result["embedding_generated"] = True
        result["embedding_time"] = f"{time.time() - start:.4f}s"
        result["embedding_dimensions"] = len(embedding)
        
    except ImportError:
        result["error"] = "sentence-transformers not installed. Run: pip install sentence-transformers"
    except Exception as e:
        result["error"] = str(e)
    
    return result


def print_result(result: dict, indent: int = 0):
    """Pretty print a result dictionary."""
    prefix = "  " * indent
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{prefix}{key}: [{len(value)} items]")
            if len(value) <= 10:
                for item in value:
                    print(f"{prefix}  - {item}")
        elif isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_result(value, indent + 1)
        else:
            print(f"{prefix}{key}: {value}")


def main():
    """Run all AIKH database tests."""
    print("=" * 70)
    print("AI Knowledge Hub (AIKH) Database & Embedding Tests")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Test 1: Artifacts Database
    print("\n[1/5] Testing Artifacts Database...")
    result = test_artifacts_db()
    status = "✓ PASS" if result.get("connected") and not result.get("error") else "✗ FAIL"
    print(f"      Status: {status}")
    print_result(result, indent=3)
    
    # Test 2: Chatlogs Database
    print("\n[2/5] Testing Chatlogs Database...")
    result = test_chatlogs_db()
    status = "✓ PASS" if result.get("connected") and not result.get("error") else "✗ FAIL"
    print(f"      Status: {status}")
    print_result(result, indent=3)
    
    # Test 3: Research Database
    print("\n[3/5] Testing Research Database...")
    result = test_research_db()
    status = "✓ PASS" if result.get("connected") and not result.get("error") else "✗ FAIL"
    print(f"      Status: {status}")
    print_result(result, indent=3)
    
    # Test 4: GPU Availability
    print("\n[4/5] Testing GPU/MPS Availability...")
    result = test_gpu_availability()
    status = "✓ PASS" if result.get("mps_available") or result.get("cuda_available") else "⚠ CPU ONLY"
    print(f"      Status: {status}")
    print_result(result, indent=3)
    
    # Test 5: Embedding Generation
    print("\n[5/5] Testing Embedding Generation...")
    result = test_embedding_generation()
    status = "✓ PASS" if result.get("embedding_generated") else "✗ FAIL"
    print(f"      Status: {status}")
    print_result(result, indent=3)
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
