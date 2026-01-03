#!/usr/bin/env python3
"""Batch PDF Download and Ingestion Pipeline.

Downloads PDFs from URLs and ingests them into the research database.

Usage:
    # From URL list file:
    python scripts/download_and_ingest.py urls.txt --category p2re-evaluation
    
    # From stdin:
    cat urls.txt | python scripts/download_and_ingest.py - --category p2re-evaluation
    
    # Direct URLs:
    python scripts/download_and_ingest.py --urls "url1" "url2" --category p2re-evaluation
"""

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion
from gpu_batch_embedder import GPUBatchEmbedder


def extract_paper_id(url: str) -> str:
    """Extract a meaningful paper ID from URL."""
    parsed = urlparse(url)
    
    # ArXiv: https://arxiv.org/pdf/2306.05685.pdf
    if "arxiv.org" in parsed.netloc:
        match = re.search(r"(\d{4}\.\d{4,5})", url)
        if match:
            return f"arxiv_{match.group(1)}"
    
    # ACL Anthology: https://aclanthology.org/2023.emnlp-main.153.pdf
    if "aclanthology.org" in parsed.netloc:
        match = re.search(r"/([^/]+)\.pdf", parsed.path)
        if match:
            return f"acl_{match.group(1)}"
    
    # OpenReview: https://openreview.net/pdf?id=xxx
    if "openreview.net" in parsed.netloc:
        query = parse_qs(parsed.query)
        if "id" in query:
            paper_id = query["id"][0][:20]  # Truncate long IDs
            return f"openreview_{paper_id}"
    
    # Fallback: hash the URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"paper_{url_hash}"


def download_pdf(url: str, output_dir: Path, paper_id: str) -> Path | None:
    """Download PDF from URL."""
    output_path = output_dir / f"{paper_id}.pdf"
    
    # Skip if already downloaded
    if output_path.exists():
        print(f"  ⏭️  Already exists: {output_path.name}")
        return output_path
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0; academic research)"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        # Verify it's a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not response.content[:4] == b"%PDF":
            print(f"  ⚠️  Not a PDF: {url}")
            return None
        
        output_path.write_bytes(response.content)
        print(f"  ✅ Downloaded: {output_path.name} ({len(response.content) / 1024:.1f} KB)")
        return output_path
        
    except requests.RequestException as e:
        print(f"  ❌ Download failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Download and ingest research PDFs")
    parser.add_argument(
        "url_file", 
        nargs="?",
        help="File containing URLs (one per line), or '-' for stdin"
    )
    parser.add_argument(
        "--urls", 
        nargs="+",
        help="Direct list of URLs"
    )
    parser.add_argument(
        "--category", 
        default="research",
        help="Category for ingested papers (default: research)"
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("downloads/pdfs"),
        help="Directory to save downloaded PDFs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("extracted_papers"),
        help="Directory for extracted paper data"
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download, don't ingest"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between downloads in seconds (be nice to servers)"
    )
    parser.add_argument(
        "--skip-gpu-embed",
        action="store_true",
        help="Skip GPU embedding phase (run gpu_batch_embedder.py manually later)"
    )
    
    args = parser.parse_args()
    
    # Collect URLs
    urls = []
    if args.urls:
        urls = args.urls
    elif args.url_file:
        if args.url_file == "-":
            urls = [line.strip() for line in sys.stdin if line.strip()]
        else:
            url_file = Path(args.url_file)
            if not url_file.exists():
                print(f"Error: File not found: {url_file}")
                sys.exit(1)
            urls = [line.strip() for line in url_file.read_text().splitlines() if line.strip()]
    else:
        parser.print_help()
        sys.exit(1)
    
    # Filter valid URLs and dedupe
    urls = list(dict.fromkeys([u for u in urls if u.startswith("http")]))
    print(f"📥 Processing {len(urls)} URLs...")
    print(f"   Category: {args.category}")
    print(f"   Download dir: {args.download_dir}")
    print()
    
    # Create directories
    args.download_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Phase 1: Download all PDFs
    print("=" * 60)
    print("PHASE 1: Downloading PDFs")
    print("=" * 60)
    
    downloaded = []
    failed_downloads = []
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url[:80]}...")
        paper_id = extract_paper_id(url)
        pdf_path = download_pdf(url, args.download_dir, paper_id)
        
        if pdf_path:
            downloaded.append(pdf_path)
        else:
            failed_downloads.append(url)
        
        if i < len(urls):
            time.sleep(args.delay)
    
    print()
    print(f"Downloaded: {len(downloaded)}/{len(urls)}")
    
    if args.download_only:
        print("\n--download-only specified, skipping ingestion.")
        return
    
    if not downloaded:
        print("No PDFs to ingest.")
        return
    
    # Phase 2: Ingest into database
    print()
    print("=" * 60)
    print("PHASE 2: Ingesting into Research Database")
    print("=" * 60)
    
    # Use skip_embeddings=True for fast ingestion, GPU embedder handles embeddings
    ingestion = ResearchPaperIngestion(skip_embeddings=True)
    
    try:
        results = ingestion.ingest_batch(
            [str(p) for p in downloaded],
            args.category,
            str(args.output_dir / args.category)
        )
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Downloads:  {len(downloaded)}/{len(urls)} successful")
        print(f"Ingestion:  {results['summary']['success_count']}/{len(downloaded)} successful")
        print(f"Category:   {args.category}")
        
        if failed_downloads:
            print(f"\nFailed downloads ({len(failed_downloads)}):")
            for url in failed_downloads[:5]:
                print(f"  - {url}")
            if len(failed_downloads) > 5:
                print(f"  ... and {len(failed_downloads) - 5} more")
        
        if results["failed"]:
            print(f"\nFailed ingestion ({len(results['failed'])}):")
            for f in results["failed"][:5]:
                print(f"  - {Path(f['pdf_path']).name}")
    
    finally:
        ingestion.close()
    
    # Phase 3: GPU Embedding
    if not args.skip_gpu_embed:
        print()
        print("=" * 60)
        print("PHASE 3: GPU Embedding Generation (RTX 5090)")
        print("=" * 60)
        
        try:
            embedder = GPUBatchEmbedder()
            print(f"GPU: {embedder.device}")
            print(f"Model: {embedder.model_name}")
            print(f"Batch size: {embedder.batch_size}")
            print()
            
            # Embed papers first (summaries)
            paper_count, paper_time = embedder.process_papers()
            
            # Then embed chunks (for detailed search)
            chunk_count, chunk_time = embedder.process_chunks()
            
            print()
            print("GPU Embedding Summary:")
            print(f"  Papers: {paper_count} ({paper_time:.1f}s)")
            print(f"  Chunks: {chunk_count} ({chunk_time:.1f}s)")
            
        except Exception as e:
            print(f"⚠️  GPU embedding failed: {e}")
            print("   Run manually: python scripts/gpu_batch_embedder.py")


if __name__ == "__main__":
    main()
