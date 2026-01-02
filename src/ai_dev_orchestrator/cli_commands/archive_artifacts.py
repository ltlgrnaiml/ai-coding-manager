"""CLI command for archiving markdown artifacts to knowledge database.

Provides command-line interface for batch processing markdown files
from Downloads folder or custom paths into the RAG knowledge system.
"""

import logging
from pathlib import Path
from typing import List, Optional

import click

from ai_dev_orchestrator.knowledge.artifact_processor import (
    ArtifactProcessor,
    ProcessingResult,
    create_processor,
    process_downloads_folder
)
from ai_dev_orchestrator.knowledge.database import init_database

logger = logging.getLogger(__name__)


def _print_results_summary(results: List[ProcessingResult]) -> None:
    """Print summary of processing results."""
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    
    total_chunks = sum(r.chunks_created for r in results if r.success)
    total_embeddings = sum(r.embeddings_created for r in results if r.success)
    
    click.echo(f"\n📊 Processing Summary:")
    click.echo(f"   Total files: {total}")
    click.echo(f"   ✅ Successful: {successful}")
    click.echo(f"   ❌ Failed: {failed}")
    click.echo(f"   📄 Chunks created: {total_chunks}")
    click.echo(f"   🔍 Embeddings created: {total_embeddings}")
    
    if failed > 0:
        click.echo(f"\n❌ Failed files:")
        for result in results:
            if not result.success:
                click.echo(f"   • {result.file_path}: {result.error}")


def _print_detailed_results(results: List[ProcessingResult]) -> None:
    """Print detailed results for each file."""
    click.echo(f"\n📋 Detailed Results:")
    
    for result in results:
        status = "✅" if result.success else "❌"
        click.echo(f"\n{status} {result.file_path.name}")
        
        if result.success and result.metadata:
            click.echo(f"   📝 Title: {result.metadata.title}")
            click.echo(f"   📂 Type: {result.metadata.doc_type}")
            click.echo(f"   🏷️  Tags: {', '.join(result.metadata.tags) if result.metadata.tags else 'None'}")
            click.echo(f"   📄 Chunks: {result.chunks_created}")
            click.echo(f"   🔍 Embeddings: {result.embeddings_created}")
            
            if result.metadata.summary:
                click.echo(f"   📋 Summary: {result.metadata.summary}")
            
            if result.metadata.key_insights:
                click.echo(f"   💡 Key Insights:")
                for insight in result.metadata.key_insights[:3]:  # Show first 3
                    click.echo(f"      • {insight}")
        
        elif not result.success:
            click.echo(f"   ❌ Error: {result.error}")


@click.group()
def archive():
    """Archive markdown artifacts to knowledge database."""
    pass


@archive.command()
@click.option('--downloads-path', '-d', type=str, help='Custom Downloads folder path')
@click.option('--pattern', '-p', default='*.md', help='File pattern to match (default: *.md)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed results')
@click.option('--init-db', is_flag=True, help='Initialize database before processing')
def downloads(downloads_path: Optional[str], pattern: str, verbose: bool, init_db: bool):
    """Process markdown files from Downloads folder.
    
    Automatically finds and processes all markdown files in the Downloads folder,
    extracting metadata, creating summaries, and indexing for RAG retrieval.
    
    Examples:
        ai-dev archive downloads
        ai-dev archive downloads --verbose
        ai-dev archive downloads -d /custom/downloads/path
        ai-dev archive downloads -p "*.txt" --verbose
    """
    if init_db:
        click.echo("🔧 Initializing database...")
        init_database()
    
    click.echo("🔍 Processing Downloads folder...")
    
    if downloads_path:
        processor = create_processor()
        results = processor.process_directory(Path(downloads_path), pattern)
    else:
        results = process_downloads_folder()
    
    if not results:
        click.echo("❌ No files found or processed")
        return
    
    _print_results_summary(results)
    
    if verbose:
        _print_detailed_results(results)


@archive.command()
@click.argument('files', nargs=-1, required=True)
@click.option('--verbose', '-v', is_flag=True, help='Show detailed results')
@click.option('--init-db', is_flag=True, help='Initialize database before processing')
def files(files: tuple, verbose: bool, init_db: bool):
    """Process specific markdown files.
    
    Process one or more specific markdown files by path.
    Supports both absolute and relative paths.
    
    Examples:
        ai-dev archive files document.md
        ai-dev archive files doc1.md doc2.md --verbose
        ai-dev archive files "/path/to/document.md"
    """
    if init_db:
        click.echo("🔧 Initializing database...")
        init_database()
    
    file_list = list(files)
    click.echo(f"🔍 Processing {len(file_list)} files...")
    
    processor = create_processor()
    results = processor.process_file_list(file_list)
    
    if not results:
        click.echo("❌ No files processed")
        return
    
    _print_results_summary(results)
    
    if verbose:
        _print_detailed_results(results)


@archive.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--pattern', '-p', default='*.md', help='File pattern to match (default: *.md)')
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories recursively')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed results')
@click.option('--init-db', is_flag=True, help='Initialize database before processing')
def directory(directory: str, pattern: str, recursive: bool, verbose: bool, init_db: bool):
    """Process all markdown files in a directory.
    
    Process all matching files in the specified directory.
    Optionally process subdirectories recursively.
    
    Examples:
        ai-dev archive directory /path/to/docs
        ai-dev archive directory ./docs --recursive
        ai-dev archive directory ~/documents -p "*.txt" --verbose
    """
    if init_db:
        click.echo("🔧 Initializing database...")
        init_database()
    
    dir_path = Path(directory)
    
    if recursive:
        pattern = f"**/{pattern}"
    
    click.echo(f"🔍 Processing directory: {dir_path}")
    click.echo(f"📁 Pattern: {pattern}")
    
    processor = create_processor()
    results = processor.process_directory(dir_path, pattern)
    
    if not results:
        click.echo("❌ No files found or processed")
        return
    
    _print_results_summary(results)
    
    if verbose:
        _print_detailed_results(results)


@archive.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed database statistics')
def status(verbose: bool):
    """Show knowledge database status and statistics.
    
    Display current state of the knowledge database including
    document counts, chunk statistics, and embedding status.
    """
    from ai_dev_orchestrator.knowledge.database import get_connection
    
    try:
        conn = get_connection()
        
        # Document statistics
        doc_stats = conn.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                SUM(CASE WHEN archived_at IS NULL THEN 1 ELSE 0 END) as active
            FROM documents 
            GROUP BY type
            ORDER BY count DESC
        """).fetchall()
        
        # Overall statistics
        overall = conn.execute("""
            SELECT 
                COUNT(*) as total_docs,
                SUM(CASE WHEN archived_at IS NULL THEN 1 ELSE 0 END) as active_docs,
                (SELECT COUNT(*) FROM chunks) as total_chunks,
                (SELECT COUNT(*) FROM embeddings) as total_embeddings
            FROM documents
        """).fetchone()
        
        click.echo("📊 Knowledge Database Status")
        click.echo("=" * 40)
        click.echo(f"📄 Total Documents: {overall['total_docs']}")
        click.echo(f"✅ Active Documents: {overall['active_docs']}")
        click.echo(f"📝 Total Chunks: {overall['total_chunks']}")
        click.echo(f"🔍 Total Embeddings: {overall['total_embeddings']}")
        
        if doc_stats:
            click.echo(f"\n📂 Documents by Type:")
            for stat in doc_stats:
                click.echo(f"   {stat['type']}: {stat['active']}/{stat['count']} (active/total)")
        
        if verbose:
            # Recent documents
            recent = conn.execute("""
                SELECT title, type, created_at, file_path
                FROM documents 
                WHERE archived_at IS NULL
                ORDER BY created_at DESC 
                LIMIT 10
            """).fetchall()
            
            if recent:
                click.echo(f"\n📅 Recent Documents:")
                for doc in recent:
                    click.echo(f"   • {doc['title']} ({doc['type']}) - {doc['created_at']}")
        
        # Embedding coverage
        coverage = conn.execute("""
            SELECT 
                COUNT(DISTINCT c.id) as total_chunks,
                COUNT(DISTINCT e.chunk_id) as embedded_chunks
            FROM chunks c
            LEFT JOIN embeddings e ON c.id = e.chunk_id
        """).fetchone()
        
        if coverage['total_chunks'] > 0:
            coverage_pct = (coverage['embedded_chunks'] / coverage['total_chunks']) * 100
            click.echo(f"\n🎯 Embedding Coverage: {coverage_pct:.1f}% ({coverage['embedded_chunks']}/{coverage['total_chunks']})")
        
    except Exception as e:
        click.echo(f"❌ Error accessing database: {e}")


if __name__ == '__main__':
    archive()
