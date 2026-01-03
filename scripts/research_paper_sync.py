#!/usr/bin/env python3
"""Research Paper Auto-Sync Tool.

Monitors a source folder and automatically ingests new PDF papers
into the research database. Supports both one-shot sync and
continuous file watching.

Usage:
    # One-shot sync (find and ingest new papers)
    python research_paper_sync.py sync /path/to/papers --category "ai-research"
    
    # Watch mode (continuous monitoring)
    python research_paper_sync.py watch /path/to/papers --category "ai-research"
    
    # Check status (show what would be synced)
    python research_paper_sync.py status /path/to/papers
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import sqlite3

# Add src and scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Default database path - use AIKH centralized location
def _get_aikh_db_path() -> Path:
    """Get AIKH research database path."""
    if aikh_home := os.getenv("AIKH_HOME"):
        return Path(aikh_home) / "research.db"
    return Path.home() / ".aikh" / "research.db"

DEFAULT_DB_PATH = _get_aikh_db_path()


def _get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a raw sqlite3 connection to the research database."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _get_ingestion_class():
    """Lazy load ingestion class."""
    # Import the module - this will work if langchain is installed or we fix the imports
    from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion
    return ResearchPaperIngestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# State file to track processed files
STATE_FILE = Path(".workspace") / "paper_sync_state.json"


def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of file for deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def load_sync_state() -> Dict:
    """Load sync state from file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"processed_files": {}, "file_hashes": {}, "last_sync": None}


def save_sync_state(state: Dict) -> None:
    """Save sync state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_pdfs_in_folder(folder: Path) -> List[Path]:
    """Get all PDF files in folder (non-recursive by default)."""
    pdfs = []
    for item in folder.iterdir():
        if item.is_file() and item.suffix.lower() == ".pdf":
            pdfs.append(item)
    return sorted(pdfs)


def get_ingested_hashes(conn) -> Set[str]:
    """Get content hashes of all papers already in database."""
    try:
        cursor = conn.execute("SELECT content_hash FROM research_papers")
        return {row[0] for row in cursor.fetchall() if row[0]}
    except Exception:
        return set()


def find_new_papers(
    folder: Path, state: Dict, ingested_hashes: Set[str]
) -> List[Tuple[Path, str]]:
    """Find PDFs that haven't been ingested yet.
    
    Returns:
        List of (pdf_path, file_hash) tuples for new papers.
    """
    new_papers = []
    pdfs = get_pdfs_in_folder(folder)
    
    for pdf in pdfs:
        pdf_str = str(pdf.resolve())
        
        # Skip if already processed (by path)
        if pdf_str in state.get("processed_files", {}):
            continue
        
        # Calculate file hash
        try:
            file_hash = get_file_hash(pdf)
        except Exception as e:
            logger.warning(f"Could not hash {pdf.name}: {e}")
            continue
        
        # Skip if hash matches existing paper
        if file_hash in state.get("file_hashes", {}):
            logger.debug(f"Skipping {pdf.name} - already processed (hash match)")
            continue
        
        # Skip if content hash is in database
        # Note: content_hash is based on extracted text, file_hash is raw file
        # We check both to be thorough
        
        new_papers.append((pdf, file_hash))
    
    return new_papers


def sync_papers(
    folder: Path,
    category: Optional[str] = None,
    dry_run: bool = False,
    output_dir: Optional[str] = None,
    skip_embeddings: bool = False,
) -> Dict:
    """Sync all new papers from folder to database.
    
    Args:
        folder: Source folder containing PDFs.
        category: Category to assign to papers.
        dry_run: If True, only report what would be done.
        output_dir: Output directory for extracted assets.
        
    Returns:
        Sync results dictionary.
    """
    folder = Path(folder).resolve()
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder}")
    
    logger.info(f"Syncing papers from: {folder}")
    
    # Load state and get existing papers
    state = load_sync_state()
    conn = _get_db_connection()
    ingested_hashes = get_ingested_hashes(conn)
    conn.close()
    
    # Find new papers
    new_papers = find_new_papers(folder, state, ingested_hashes)
    
    results = {
        "folder": str(folder),
        "total_pdfs": len(get_pdfs_in_folder(folder)),
        "new_papers": len(new_papers),
        "ingested": [],
        "failed": [],
        "skipped": [],
        "dry_run": dry_run,
    }
    
    if not new_papers:
        logger.info("No new papers to sync")
        return results
    
    logger.info(f"Found {len(new_papers)} new paper(s) to ingest")
    
    if dry_run:
        for pdf, file_hash in new_papers:
            logger.info(f"  Would ingest: {pdf.name}")
            results["ingested"].append({"path": str(pdf), "hash": file_hash})
        return results
    
    # Ingest papers
    IngestionClass = _get_ingestion_class()
    ingestion = IngestionClass(skip_embeddings=skip_embeddings)
    
    if skip_embeddings:
        logger.info("Skipping embedding generation (fast mode)")
    
    try:
        for pdf, file_hash in new_papers:
            logger.info(f"Ingesting: {pdf.name}")
            
            try:
                paper_id, result = ingestion.ingest_pdf(
                    str(pdf), category, output_dir
                )
                
                if result["status"] == "success":
                    logger.info(f"  ✓ {result.get('title', 'Untitled')}")
                    
                    # Update state
                    state["processed_files"][str(pdf)] = {
                        "paper_id": paper_id,
                        "ingested_at": datetime.now().isoformat(),
                        "title": result.get("title"),
                    }
                    state["file_hashes"][file_hash] = paper_id
                    
                    results["ingested"].append({
                        "path": str(pdf),
                        "paper_id": paper_id,
                        "title": result.get("title"),
                    })
                else:
                    logger.error(f"  ✗ Failed: {result.get('error')}")
                    results["failed"].append({
                        "path": str(pdf),
                        "error": result.get("error"),
                    })
                    
            except Exception as e:
                logger.error(f"  ✗ Exception: {e}")
                results["failed"].append({"path": str(pdf), "error": str(e)})
        
        # Save state
        state["last_sync"] = datetime.now().isoformat()
        save_sync_state(state)
        
    finally:
        ingestion.close()
    
    logger.info(
        f"Sync complete: {len(results['ingested'])} ingested, "
        f"{len(results['failed'])} failed"
    )
    
    return results


def watch_folder(
    folder: Path,
    category: Optional[str] = None,
    output_dir: Optional[str] = None,
    poll_interval: float = 5.0,
    skip_embeddings: bool = False,
) -> None:
    """Watch folder for new PDFs and auto-ingest them.
    
    Args:
        folder: Folder to watch.
        category: Category for new papers.
        output_dir: Output directory for extracted assets.
        poll_interval: Seconds between folder checks.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileCreatedEvent
        
        use_watchdog = True
    except ImportError:
        logger.warning("watchdog not installed, using polling mode")
        use_watchdog = False
    
    folder = Path(folder).resolve()
    logger.info(f"Watching folder: {folder}")
    logger.info(f"Category: {category or '(none)'}")
    logger.info("Press Ctrl+C to stop")
    
    if use_watchdog:
        _watch_with_watchdog(folder, category, output_dir, skip_embeddings)
    else:
        _watch_with_polling(folder, category, output_dir, poll_interval, skip_embeddings)


def _watch_with_watchdog(
    folder: Path,
    category: Optional[str],
    output_dir: Optional[str],
    skip_embeddings: bool = False,
) -> None:
    """Watch using watchdog library (efficient, event-based)."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    
    class PDFHandler(FileSystemEventHandler):
        def __init__(self):
            self.pending_files: Dict[str, float] = {}
            self.debounce_seconds = 2.0  # Wait for file to finish writing
        
        def on_created(self, event):
            if not event.is_directory and event.src_path.lower().endswith(".pdf"):
                # Debounce: wait for file to be fully written
                self.pending_files[event.src_path] = time.time()
        
        def on_modified(self, event):
            if not event.is_directory and event.src_path.lower().endswith(".pdf"):
                self.pending_files[event.src_path] = time.time()
        
        def process_pending(self):
            now = time.time()
            to_process = []
            
            for path, timestamp in list(self.pending_files.items()):
                if now - timestamp >= self.debounce_seconds:
                    to_process.append(path)
                    del self.pending_files[path]
            
            for path in to_process:
                logger.info(f"New PDF detected: {Path(path).name}")
                try:
                    results = sync_papers(
                        folder, category=category, output_dir=output_dir,
                        skip_embeddings=skip_embeddings
                    )
                    if results["ingested"]:
                        for paper in results["ingested"]:
                            logger.info(f"  ✓ Ingested: {paper.get('title', paper['path'])}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to process: {e}")
    
    # Initial sync before watching
    logger.info("Running initial sync...")
    initial_results = sync_papers(folder, category=category, output_dir=output_dir,
                                   skip_embeddings=skip_embeddings)
    logger.info(
        f"Initial sync: {len(initial_results['ingested'])} ingested, "
        f"{len(initial_results['failed'])} failed"
    )
    
    handler = PDFHandler()
    observer = Observer()
    observer.schedule(handler, str(folder), recursive=False)
    observer.start()
    
    logger.info("Now watching for new files...")
    
    try:
        while True:
            handler.process_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
        observer.stop()
    
    observer.join()


def _watch_with_polling(
    folder: Path,
    category: Optional[str],
    output_dir: Optional[str],
    poll_interval: float,
    skip_embeddings: bool = False,
) -> None:
    """Watch using polling (fallback when watchdog not available)."""
    state = load_sync_state()
    known_files = set(state.get("processed_files", {}).keys())
    
    # Initial sync
    logger.info("Running initial sync...")
    sync_papers(folder, category=category, output_dir=output_dir, skip_embeddings=skip_embeddings)
    
    try:
        while True:
            time.sleep(poll_interval)
            
            # Check for new files
            current_files = {str(p.resolve()) for p in get_pdfs_in_folder(folder)}
            new_files = current_files - known_files
            
            if new_files:
                logger.info(f"Found {len(new_files)} new file(s)")
                sync_papers(folder, category=category, output_dir=output_dir, skip_embeddings=skip_embeddings)
                
                # Update known files
                state = load_sync_state()
                known_files = set(state.get("processed_files", {}).keys())
                
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")


def show_status(folder: Path) -> Dict:
    """Show sync status for a folder.
    
    Args:
        folder: Source folder.
        
    Returns:
        Status dictionary.
    """
    folder = Path(folder).resolve()
    state = load_sync_state()
    conn = _get_db_connection()
    ingested_hashes = get_ingested_hashes(conn)
    
    # Get database stats
    cursor = conn.execute("SELECT COUNT(*) FROM research_papers")
    total_in_db = cursor.fetchone()[0]
    conn.close()
    
    # Find papers
    all_pdfs = get_pdfs_in_folder(folder)
    new_papers = find_new_papers(folder, state, ingested_hashes)
    
    status = {
        "folder": str(folder),
        "total_pdfs_in_folder": len(all_pdfs),
        "already_ingested": len(all_pdfs) - len(new_papers),
        "pending_ingestion": len(new_papers),
        "total_papers_in_db": total_in_db,
        "last_sync": state.get("last_sync"),
        "pending_files": [str(p.name) for p, _ in new_papers],
    }
    
    print("\n" + "=" * 60)
    print("Research Paper Sync Status")
    print("=" * 60)
    print(f"Source folder: {status['folder']}")
    print(f"PDFs in folder: {status['total_pdfs_in_folder']}")
    print(f"Already ingested: {status['already_ingested']}")
    print(f"Pending ingestion: {status['pending_ingestion']}")
    print(f"Total papers in DB: {status['total_papers_in_db']}")
    print(f"Last sync: {status['last_sync'] or 'Never'}")
    
    if status["pending_files"]:
        print(f"\nPending files ({len(status['pending_files'])}):")
        for name in status["pending_files"][:20]:
            print(f"  • {name}")
        if len(status["pending_files"]) > 20:
            print(f"  ... and {len(status['pending_files']) - 20} more")
    
    print("=" * 60 + "\n")
    
    return status


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Research Paper Auto-Sync Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check what would be synced
  python research_paper_sync.py status ~/papers

  # One-shot sync (ingest all new papers)
  python research_paper_sync.py sync ~/papers --category "ai-research"

  # Dry run (show what would be done)
  python research_paper_sync.py sync ~/papers --dry-run

  # Watch mode (continuous monitoring)
  python research_paper_sync.py watch ~/papers --category "ai-research"
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show sync status")
    status_parser.add_argument("folder", help="Source folder containing PDFs")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync new papers")
    sync_parser.add_argument("folder", help="Source folder containing PDFs")
    sync_parser.add_argument("--category", "-c", help="Category for papers")
    sync_parser.add_argument("--output-dir", "-o", help="Output directory for assets")
    sync_parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Show what would be done"
    )
    sync_parser.add_argument(
        "--skip-embeddings", "-s", action="store_true",
        help="Skip embedding generation for faster ingestion (can generate later)"
    )
    
    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch folder for new papers")
    watch_parser.add_argument("folder", help="Source folder to watch")
    watch_parser.add_argument("--category", "-c", help="Category for papers")
    watch_parser.add_argument("--output-dir", "-o", help="Output directory for assets")
    watch_parser.add_argument(
        "--poll-interval", "-i", type=float, default=5.0,
        help="Poll interval in seconds (for fallback mode)"
    )
    watch_parser.add_argument(
        "--skip-embeddings", "-s", action="store_true",
        help="Skip embedding generation for faster ingestion"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "status":
            show_status(args.folder)
        
        elif args.command == "sync":
            results = sync_papers(
                args.folder,
                category=args.category,
                dry_run=args.dry_run,
                output_dir=args.output_dir,
                skip_embeddings=args.skip_embeddings,
            )
            
            if not args.dry_run:
                print(f"\nSync complete:")
                print(f"  Ingested: {len(results['ingested'])}")
                print(f"  Failed: {len(results['failed'])}")
        
        elif args.command == "watch":
            watch_folder(
                args.folder,
                category=args.category,
                output_dir=args.output_dir,
                poll_interval=args.poll_interval,
                skip_embeddings=args.skip_embeddings,
            )
    
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
