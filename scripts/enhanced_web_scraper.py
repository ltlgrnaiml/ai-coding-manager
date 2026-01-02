"""Enhanced Web Scraper with DOI Lookup Fallback.

Combines web scraping with DOI metadata lookup for comprehensive paper extraction.
"""

import sys
import json
from pathlib import Path

# Import our existing modules
sys.path.append(str(Path(__file__).parent))
from web_scraper import WebScraper, ScrapedPaper, ScrapedPaperMetadata, save_scraped_paper
from doi_lookup import lookup_doi_crossref, lookup_doi_semantic_scholar

import re
import hashlib
from datetime import datetime


class EnhancedWebScraper(WebScraper):
    """Enhanced web scraper with DOI lookup fallback."""
    
    def scrape_paper_enhanced(self, url: str) -> ScrapedPaper:
        """Scrape paper with DOI lookup fallback."""
        print(f"Enhanced scraping from: {url}")
        
        # First try normal web scraping
        try:
            paper = self.scrape_paper(url)
            
            # If we got meaningful content, return it
            if paper.metadata.title and paper.metadata.title != "Failed to scrape":
                return paper
                
        except Exception as e:
            print(f"Web scraping failed: {e}")
        
        # Extract DOI from URL for metadata lookup
        doi_match = re.search(r'10\.\d{4,}/[^\s?]+', url)
        if doi_match:
            doi = doi_match.group(0)
            print(f"Extracted DOI: {doi}")
            
            # Try DOI lookup
            return self._create_paper_from_doi(url, doi)
        
        # If no DOI found, return minimal paper
        return self._create_minimal_paper(url)
    
    def _create_paper_from_doi(self, url: str, doi: str) -> ScrapedPaper:
        """Create paper object from DOI metadata lookup."""
        print(f"Looking up metadata for DOI: {doi}")
        
        # Try CrossRef first
        metadata_dict = lookup_doi_crossref(doi)
        
        # Try Semantic Scholar as fallback
        if not metadata_dict:
            metadata_dict = lookup_doi_semantic_scholar(doi)
        
        if not metadata_dict:
            print("DOI lookup failed, creating minimal paper")
            return self._create_minimal_paper(url, doi)
        
        # Convert to our metadata format
        metadata = ScrapedPaperMetadata(
            title=metadata_dict.get('title'),
            authors=metadata_dict.get('authors', []),
            abstract=metadata_dict.get('abstract'),
            publication_date=metadata_dict.get('publication_date'),
            doi=doi,
            venue=metadata_dict.get('venue'),
            url=url,
            publisher=metadata_dict.get('publisher', 'Unknown')
        )
        
        # Create full text from available metadata
        full_text_parts = []
        
        if metadata.title:
            full_text_parts.append(f"Title: {metadata.title}")
        
        if metadata.authors:
            full_text_parts.append(f"Authors: {', '.join(metadata.authors)}")
        
        if metadata.abstract:
            full_text_parts.append(f"Abstract: {metadata.abstract}")
        
        if metadata.venue:
            full_text_parts.append(f"Published in: {metadata.venue}")
        
        if metadata.publication_date:
            full_text_parts.append(f"Publication Date: {metadata.publication_date}")
        
        full_text_parts.append(f"DOI: {doi}")
        full_text_parts.append(f"Source URL: {url}")
        
        # Add additional metadata if available
        if 'citation_count' in metadata_dict:
            full_text_parts.append(f"Citation Count: {metadata_dict['citation_count']}")
        
        if 'fields_of_study' in metadata_dict:
            fields = metadata_dict['fields_of_study']
            if fields:
                full_text_parts.append(f"Fields of Study: {', '.join(fields)}")
        
        full_text = '\n\n'.join(full_text_parts)
        
        # Create sections from available content
        sections = []
        
        if metadata.abstract:
            from web_scraper import ScrapedSection
            sections.append(ScrapedSection(
                title="Abstract",
                content=metadata.abstract,
                level=1,
                order=0
            ))
        
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        
        paper = ScrapedPaper(
            source_url=url,
            extraction_date=datetime.now().isoformat(),
            content_hash=content_hash,
            metadata=metadata,
            full_text=full_text,
            sections=sections,
            references=[],
            figures=[],
            tables=[]
        )
        
        print(f"Successfully created paper from DOI metadata:")
        print(f"  Title: {metadata.title}")
        print(f"  Authors: {', '.join(metadata.authors) if metadata.authors else 'N/A'}")
        print(f"  Venue: {metadata.venue or 'N/A'}")
        print(f"  Date: {metadata.publication_date or 'N/A'}")
        
        return paper


def main():
    """Enhanced command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced web scraper with DOI lookup')
    parser.add_argument('url', help='URL of the paper to scrape')
    parser.add_argument('--output-dir', '-o', default='./scraped_papers',
                       help='Output directory for scraped files')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                       help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    scraper = EnhancedWebScraper(delay=args.delay)
    
    try:
        paper = scraper.scrape_paper_enhanced(args.url)
        json_path = save_scraped_paper(paper, args.output_dir)
        
        print(f"\nScraping completed successfully!")
        print(f"Title: {paper.metadata.title}")
        print(f"Authors: {', '.join(paper.metadata.authors) if paper.metadata.authors else 'N/A'}")
        print(f"Word count: {len(paper.full_text.split())}")
        print(f"Sections: {len(paper.sections)}")
        print(f"DOI: {paper.metadata.doi or 'N/A'}")
        print(f"Output: {json_path}")
        
    except Exception as e:
        print(f"Error scraping paper: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
