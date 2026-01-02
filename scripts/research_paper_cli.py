#!/usr/bin/env python3
"""Research Paper Management CLI.

Command-line interface for managing research papers in the RAG system.
Provides ingestion, search, and retrieval capabilities.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion
from ai_dev_orchestrator.knowledge.research_rag import ResearchRAGService
from ai_dev_orchestrator.knowledge.research_database import (
    get_research_connection, 
    get_research_stats,
    get_papers_by_category
)


def cmd_ingest(args):
    """Ingest PDF papers into the research database."""
    print(f"Ingesting {len(args.pdf_paths)} PDF(s)...")
    
    ingestion = ResearchPaperIngestion()
    
    try:
        if len(args.pdf_paths) == 1:
            paper_id, result = ingestion.ingest_pdf(
                args.pdf_paths[0], 
                args.category, 
                args.output_dir
            )
            
            if result["status"] == "success":
                print(f"✓ Successfully ingested: {paper_id}")
                print(f"  Title: {result.get('title', 'Unknown')}")
                print(f"  Pages: {result.get('pages', 0)}")
                print(f"  Words: {result.get('words', 0):,}")
                if args.category:
                    print(f"  Category: {args.category}")
            else:
                print(f"✗ Failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            results = ingestion.ingest_batch(
                args.pdf_paths, 
                args.category, 
                args.output_dir
            )
            
            print(f"\nBatch Results:")
            print(f"  Success: {results['summary']['success_count']}")
            print(f"  Failed: {results['summary']['failure_count']}")
            print(f"  Rate: {results['summary']['success_rate']:.1%}")
            
            if results["failed"]:
                print(f"\nFailed papers:")
                for failure in results["failed"]:
                    print(f"  ✗ {Path(failure['pdf_path']).name}")
    
    finally:
        ingestion.close()


def cmd_search(args):
    """Search research papers."""
    rag_service = ResearchRAGService()
    
    try:
        print(f"Searching for: '{args.query}'")
        
        if args.method == "semantic":
            results = rag_service.search_papers_semantic(
                args.query, args.limit, args.category
            )
        elif args.method == "fulltext":
            results = rag_service.search_papers_fulltext(
                args.query, args.limit, args.category
            )
        else:  # hybrid
            results = rag_service.search_papers_hybrid(
                args.query, args.limit, args.category
            )
        
        if not results:
            print("No results found.")
            return
        
        print(f"\nFound {len(results)} results:")
        print("=" * 80)
        
        for i, hit in enumerate(results, 1):
            print(f"\n{i}. {hit.title}")
            print(f"   ID: {hit.paper_id}")
            if hit.authors:
                authors_str = ", ".join(hit.authors[:3])
                if len(hit.authors) > 3:
                    authors_str += f" (+{len(hit.authors) - 3} more)"
                print(f"   Authors: {authors_str}")
            
            if hit.arxiv_id:
                print(f"   arXiv: {hit.arxiv_id}")
            if hit.doi:
                print(f"   DOI: {hit.doi}")
            if hit.venue:
                print(f"   Venue: {hit.venue}")
            if hit.categories:
                print(f"   Categories: {', '.join(hit.categories)}")
            
            print(f"   Score: {hit.score:.3f}")
            print(f"   Type: {hit.chunk_type}")
            
            # Show snippet
            content = hit.chunk_content or hit.snippet or ""
            if content:
                snippet = content[:200] + "..." if len(content) > 200 else content
                print(f"   Content: {snippet}")
    
    finally:
        rag_service.close()


def cmd_show(args):
    """Show details of a specific paper."""
    rag_service = ResearchRAGService()
    
    try:
        context = rag_service.get_paper_context(args.paper_id, args.query)
        
        if not context:
            print(f"Paper not found: {args.paper_id}")
            sys.exit(1)
        
        print(f"Paper: {context['title']}")
        print("=" * 80)
        
        if context.get('authors'):
            print(f"Authors: {', '.join(context['authors'])}")
        
        if context.get('arxiv_id'):
            print(f"arXiv: {context['arxiv_id']}")
        if context.get('doi'):
            print(f"DOI: {context['doi']}")
        if context.get('venue'):
            print(f"Venue: {context['venue']}")
        if context.get('publication_date'):
            print(f"Date: {context['publication_date']}")
        
        print(f"Pages: {context.get('page_count', 0)}")
        print(f"Words: {context.get('word_count', 0):,}")
        
        if context.get('categories'):
            print(f"Categories: {', '.join(context['categories'])}")
        
        if context.get('abstract'):
            print(f"\nAbstract:")
            print(context['abstract'])
        
        if context.get('relevant_chunks'):
            print(f"\nRelevant Content:")
            for i, chunk in enumerate(context['relevant_chunks'][:3], 1):
                print(f"\n{i}. [{chunk['chunk_type']}] (score: {chunk['similarity']:.3f})")
                content = chunk['content'][:300] + "..." if len(chunk['content']) > 300 else chunk['content']
                print(f"   {content}")
    
    finally:
        rag_service.close()


def cmd_list(args):
    """List papers by category or show all categories."""
    conn = get_research_connection()
    
    try:
        if args.category:
            papers = get_papers_by_category(conn, args.category, args.limit)
            
            if not papers:
                print(f"No papers found in category: {args.category}")
                return
            
            print(f"Papers in category '{args.category}' ({len(papers)} found):")
            print("=" * 80)
            
            for paper in papers:
                import json
                authors = json.loads(paper['authors'] or '[]')
                authors_str = ", ".join(authors[:2])
                if len(authors) > 2:
                    authors_str += f" (+{len(authors) - 2} more)"
                
                print(f"\n• {paper['title']}")
                print(f"  ID: {paper['id']}")
                if authors_str:
                    print(f"  Authors: {authors_str}")
                if paper.get('arxiv_id'):
                    print(f"  arXiv: {paper['arxiv_id']}")
                print(f"  Confidence: {paper['confidence']:.2f}")
        
        else:
            # Show category statistics
            stats = get_research_stats(conn)
            
            print(f"Research Paper Database Statistics:")
            print("=" * 80)
            print(f"Total papers: {stats['total_papers']}")
            
            if stats['categories']:
                print(f"\nCategories:")
                for cat in stats['categories']:
                    print(f"  • {cat['category']}: {cat['count']} papers")
            
            if stats['top_venues']:
                print(f"\nTop venues:")
                for venue in stats['top_venues']:
                    print(f"  • {venue['venue']}: {venue['count']} papers")
    
    finally:
        conn.close()


def cmd_stats(args):
    """Show database statistics."""
    conn = get_research_connection()
    
    try:
        stats = get_research_stats(conn)
        
        print("Research Paper Database Statistics:")
        print("=" * 80)
        print(f"Total papers: {stats['total_papers']}")
        print(f"Recent papers (30 days): {stats['recent_papers']}")
        
        if stats['categories']:
            print(f"\nCategory distribution:")
            for cat in stats['categories'][:10]:  # Top 10
                print(f"  {cat['category']:20} {cat['count']:3d} papers")
        
        if stats['top_venues']:
            print(f"\nTop venues:")
            for venue in stats['top_venues']:
                print(f"  {venue['venue']:30} {venue['count']:3d} papers")
        
        # Get ingestion stats if available
        try:
            from ai_dev_orchestrator.knowledge.research_ingestion import ResearchPaperIngestion
            ingestion = ResearchPaperIngestion()
            ing_stats = ingestion.get_ingestion_stats()
            
            print(f"\nProcessing statistics:")
            print(f"  Papers with chunks: {ing_stats.get('papers_with_chunks', 0)}")
            print(f"  Total chunks: {ing_stats.get('total_chunks', 0)}")
            print(f"  Total embeddings: {ing_stats.get('total_embeddings', 0)}")
            
            if ing_stats.get('avg_word_count'):
                print(f"  Avg words per paper: {ing_stats['avg_word_count']:.0f}")
            if ing_stats.get('avg_page_count'):
                print(f"  Avg pages per paper: {ing_stats['avg_page_count']:.1f}")
            
            ingestion.close()
        except Exception:
            pass
    
    finally:
        conn.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Research Paper Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a single paper
  python research_paper_cli.py ingest paper.pdf --category "machine-learning"
  
  # Ingest multiple papers
  python research_paper_cli.py ingest *.pdf --category "nlp"
  
  # Search papers
  python research_paper_cli.py search "transformer architecture" --method hybrid
  
  # Show paper details
  python research_paper_cli.py show paper_abc123def456
  
  # List papers by category
  python research_paper_cli.py list --category "machine-learning"
  
  # Show statistics
  python research_paper_cli.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDF papers")
    ingest_parser.add_argument("pdf_paths", nargs="+", help="PDF file paths")
    ingest_parser.add_argument("--category", "-c", help="Category for the papers")
    ingest_parser.add_argument("--output-dir", "-o", help="Output directory for assets")
    ingest_parser.set_defaults(func=cmd_ingest)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search papers")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--method", "-m", choices=["semantic", "fulltext", "hybrid"], 
                              default="hybrid", help="Search method")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    search_parser.add_argument("--category", "-c", help="Filter by category")
    search_parser.set_defaults(func=cmd_search)
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show paper details")
    show_parser.add_argument("paper_id", help="Paper ID")
    show_parser.add_argument("--query", "-q", help="Query for relevant chunks")
    show_parser.set_defaults(func=cmd_show)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List papers or categories")
    list_parser.add_argument("--category", "-c", help="List papers in category")
    list_parser.add_argument("--limit", "-l", type=int, default=20, help="Max results")
    list_parser.set_defaults(func=cmd_list)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
