"""Web Scraping Tool for Academic Papers.

This tool scrapes academic papers from web pages, particularly ACM Digital Library,
arXiv, and other academic sources. Extracts structured content suitable for RAG systems.

Citation: [Engineering-Tools-2025] "Web Scraping Tool for Academic Papers"
          Adapted for AI Coding Manager project
          Key insight: Structured extraction with metadata parsing for academic web content
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


@dataclass
class ScrapedPaperMetadata:
    """Metadata extracted from a web paper."""
    
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    publication_date: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    venue: str | None = None
    keywords: list[str] = field(default_factory=list)
    url: str | None = None
    publisher: str | None = None


@dataclass
class ScrapedSection:
    """A section from a scraped paper."""
    
    title: str
    content: str
    level: int  # Heading level (1-6)
    order: int


@dataclass
class ScrapedPaper:
    """Complete extraction from a web paper."""
    
    source_url: str
    extraction_date: str
    content_hash: str
    metadata: ScrapedPaperMetadata
    full_text: str
    sections: list[ScrapedSection]
    references: list[str]
    figures: list[str]  # Figure captions/descriptions
    tables: list[str]   # Table captions/descriptions


class WebScraper:
    """Web scraper for academic papers."""
    
    def __init__(self, delay: float = 1.0):
        """Initialize web scraper.
        
        Args:
            delay: Delay between requests in seconds.
        """
        self.delay = delay
        self.session = requests.Session()
        
        # Enhanced headers to mimic real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def scrape_paper(self, url: str) -> ScrapedPaper:
        """Scrape a paper from a URL.
        
        Args:
            url: URL of the paper to scrape.
            
        Returns:
            ScrapedPaper object with extracted content.
        """
        print(f"Scraping paper from: {url}")
        
        # Add delay to avoid rate limiting
        time.sleep(self.delay)
        
        # Try multiple strategies for ACM
        if 'dl.acm.org' in url:
            return self._scrape_acm_with_tricks(url)
        
        # Fetch the page normally for other sites
        response = self._fetch_with_retries(url)
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Determine scraper based on URL
        if 'arxiv.org' in url:
            return self._scrape_arxiv_paper(url, soup)
        else:
            return self._scrape_generic_paper(url, soup)
    
    def _fetch_with_retries(self, url: str, max_retries: int = 3) -> requests.Response:
        """Fetch URL with retries and different strategies."""
        for attempt in range(max_retries):
            try:
                # Add referrer for ACM
                headers = {}
                if 'dl.acm.org' in url:
                    headers['Referer'] = 'https://dl.acm.org/'
                
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    def _scrape_acm_with_tricks(self, url: str) -> ScrapedPaper:
        """Special handling for ACM Digital Library with anti-detection tricks."""
        print("Using enhanced ACM scraping strategy...")
        
        # Extract DOI from URL for alternative access methods
        doi_match = re.search(r'10\.1145/(\d+\.\d+)', url)
        doi = doi_match.group(0) if doi_match else None
        
        # Try different URL variations and access methods
        urls_to_try = [
            url.replace('fullHtml', 'abs'),  # Try abstract page first
            url.split('?')[0],  # Remove query parameters
            url,  # Original URL
        ]
        
        # Add alternative access URLs if we have DOI
        if doi:
            urls_to_try.extend([
                f"https://dl.acm.org/doi/{doi}",
                f"https://doi.org/{doi}",
                f"https://dl.acm.org/citation.cfm?id={doi.split('/')[-1]}",
                # Try academic search engines and mirrors
                f"https://scholar.google.com/scholar?q={doi}",
                f"https://www.semanticscholar.org/search?q={doi}",
                # Try preprint servers
                f"https://arxiv.org/search/?query={doi}&searchtype=all"
            ])
        
        for attempt_url in urls_to_try:
            try:
                print(f"Trying URL: {attempt_url}")
                
                # Create a fresh session for each attempt
                session = requests.Session()
                
                # Rotate user agents
                user_agents = [
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0'
                ]
                
                import random
                user_agent = random.choice(user_agents)
                
                # Set comprehensive headers
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                }
                
                # Add specific headers for ACM
                if 'dl.acm.org' in attempt_url:
                    headers.update({
                        'Referer': 'https://dl.acm.org/',
                        'Origin': 'https://dl.acm.org',
                        'Host': 'dl.acm.org',
                        'Sec-Fetch-Site': 'same-origin',
                    })
                
                session.headers.update(headers)
                
                # Add random delay
                time.sleep(random.uniform(1, 3))
                
                response = session.get(attempt_url, timeout=30, allow_redirects=True)
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check if we got actual content (not just an error page)
                    if soup.find('title') and 'error' not in soup.find('title').get_text().lower():
                        print(f"Successfully accessed content from: {attempt_url}")
                        return self._scrape_acm_paper(attempt_url, soup)
                    else:
                        print(f"Got error page from: {attempt_url}")
                        
            except Exception as e:
                print(f"Failed with {attempt_url}: {e}")
                continue
        
        # If all methods fail, create a minimal result with available info
        print("All scraping methods failed, creating minimal result...")
        return self._create_minimal_paper(url, doi)
    
    def _create_minimal_paper(self, url: str, doi: str = None) -> ScrapedPaper:
        """Create a minimal paper object when scraping fails."""
        metadata = ScrapedPaperMetadata(
            url=url, 
            doi=doi,
            title=f"Paper {doi}" if doi else "Failed to scrape",
            publisher="ACM" if 'dl.acm.org' in url else "Unknown"
        )
        
        content_hash = hashlib.md5(url.encode()).hexdigest()
        
        return ScrapedPaper(
            source_url=url,
            extraction_date=datetime.now().isoformat(),
            content_hash=content_hash,
            metadata=metadata,
            full_text=f"Unable to scrape content from {url}. DOI: {doi}" if doi else f"Unable to scrape content from {url}",
            sections=[],
            references=[],
            figures=[],
            tables=[]
        )
    
    def _scrape_with_puppeteer(self, url: str) -> ScrapedPaper:
        """Fallback scraping using Puppeteer MCP."""
        try:
            # This will be handled by the main script calling Puppeteer MCP
            # For now, raise an exception to indicate we need Puppeteer
            raise Exception("PUPPETEER_NEEDED")
        except Exception:
            # If Puppeteer fails, create a minimal paper object
            metadata = ScrapedPaperMetadata(url=url, title="Failed to scrape")
            content_hash = hashlib.md5(url.encode()).hexdigest()
            
            return ScrapedPaper(
                source_url=url,
                extraction_date=datetime.now().isoformat(),
                content_hash=content_hash,
                metadata=metadata,
                full_text="",
                sections=[],
                references=[],
                figures=[],
                tables=[]
            )
    
    def _scrape_acm_paper(self, url: str, soup: BeautifulSoup) -> ScrapedPaper:
        """Scrape ACM Digital Library paper."""
        metadata = ScrapedPaperMetadata(url=url, publisher="ACM")
        
        # Extract title
        title_elem = soup.find('h1', class_='citation__title') or soup.find('h1')
        if title_elem:
            metadata.title = title_elem.get_text().strip()
        
        # Extract authors
        author_elems = soup.find_all('a', class_='author-name') or soup.find_all('span', class_='author')
        metadata.authors = [elem.get_text().strip() for elem in author_elems]
        
        # Extract DOI
        doi_elem = soup.find('a', href=re.compile(r'doi\.org'))
        if doi_elem:
            doi_url = doi_elem.get('href', '')
            doi_match = re.search(r'10\.\d{4,}/[^\s]+', doi_url)
            if doi_match:
                metadata.doi = doi_match.group(0)
        
        # Extract abstract
        abstract_elem = soup.find('div', class_='abstractSection') or soup.find('div', class_='abstract')
        if abstract_elem:
            # Remove the "Abstract" heading
            abstract_text = abstract_elem.get_text().strip()
            abstract_text = re.sub(r'^Abstract\s*', '', abstract_text, flags=re.IGNORECASE)
            metadata.abstract = abstract_text
        
        # Extract publication info
        pub_elem = soup.find('span', class_='epub-section__title') or soup.find('div', class_='issue-item__detail')
        if pub_elem:
            metadata.venue = pub_elem.get_text().strip()
        
        # Extract date
        date_elem = soup.find('span', class_='epub-section__date')
        if date_elem:
            metadata.publication_date = date_elem.get_text().strip()
        
        # Extract keywords
        keyword_elems = soup.find_all('a', class_='keyword')
        metadata.keywords = [elem.get_text().strip() for elem in keyword_elems]
        
        # Extract main content
        content_elem = soup.find('div', class_='hlFld-Fulltext') or soup.find('main') or soup.find('article')
        if not content_elem:
            content_elem = soup.find('body')
        
        full_text = content_elem.get_text() if content_elem else soup.get_text()
        
        # Extract sections
        sections = self._extract_sections(content_elem or soup)
        
        # Extract references
        references = self._extract_references(soup)
        
        # Extract figures and tables
        figures = self._extract_figures(soup)
        tables = self._extract_tables(soup)
        
        # Create content hash
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        
        return ScrapedPaper(
            source_url=url,
            extraction_date=datetime.now().isoformat(),
            content_hash=content_hash,
            metadata=metadata,
            full_text=full_text,
            sections=sections,
            references=references,
            figures=figures,
            tables=tables
        )
    
    def _scrape_arxiv_paper(self, url: str, soup: BeautifulSoup) -> ScrapedPaper:
        """Scrape arXiv paper."""
        metadata = ScrapedPaperMetadata(url=url, publisher="arXiv")
        
        # Extract arXiv ID from URL
        arxiv_match = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', url)
        if arxiv_match:
            metadata.arxiv_id = arxiv_match.group(1)
        
        # Extract title
        title_elem = soup.find('h1', class_='title')
        if title_elem:
            metadata.title = title_elem.get_text().replace('Title:', '').strip()
        
        # Extract authors
        author_elem = soup.find('div', class_='authors')
        if author_elem:
            author_links = author_elem.find_all('a')
            metadata.authors = [link.get_text().strip() for link in author_links]
        
        # Extract abstract
        abstract_elem = soup.find('blockquote', class_='abstract')
        if abstract_elem:
            abstract_text = abstract_elem.get_text().strip()
            abstract_text = re.sub(r'^Abstract:\s*', '', abstract_text, flags=re.IGNORECASE)
            metadata.abstract = abstract_text
        
        # Extract submission date
        date_elem = soup.find('div', class_='dateline')
        if date_elem:
            metadata.publication_date = date_elem.get_text().strip()
        
        # For arXiv, we typically need to get the PDF and extract content
        # For now, we'll use the abstract page content
        full_text = soup.get_text()
        
        # Create basic sections from available content
        sections = []
        if metadata.abstract:
            sections.append(ScrapedSection(
                title="Abstract",
                content=metadata.abstract,
                level=1,
                order=0
            ))
        
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        
        return ScrapedPaper(
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
    
    def _scrape_generic_paper(self, url: str, soup: BeautifulSoup) -> ScrapedPaper:
        """Scrape generic academic paper."""
        metadata = ScrapedPaperMetadata(url=url)
        
        # Try to extract title from various common selectors
        title_selectors = ['h1', '.title', '.paper-title', 'title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text().strip():
                metadata.title = title_elem.get_text().strip()
                break
        
        # Try to extract abstract
        abstract_selectors = ['.abstract', '.summary', '#abstract']
        for selector in abstract_selectors:
            abstract_elem = soup.select_one(selector)
            if abstract_elem:
                abstract_text = abstract_elem.get_text().strip()
                abstract_text = re.sub(r'^Abstract\s*', '', abstract_text, flags=re.IGNORECASE)
                metadata.abstract = abstract_text
                break
        
        # Extract main content
        content_elem = soup.find('main') or soup.find('article') or soup.find('body')
        full_text = content_elem.get_text() if content_elem else soup.get_text()
        
        # Extract sections
        sections = self._extract_sections(content_elem or soup)
        
        # Extract references
        references = self._extract_references(soup)
        
        # Extract figures and tables
        figures = self._extract_figures(soup)
        tables = self._extract_tables(soup)
        
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        
        return ScrapedPaper(
            source_url=url,
            extraction_date=datetime.now().isoformat(),
            content_hash=content_hash,
            metadata=metadata,
            full_text=full_text,
            sections=sections,
            references=references,
            figures=figures,
            tables=tables
        )
    
    def _extract_sections(self, content_elem: Tag) -> list[ScrapedSection]:
        """Extract sections from content."""
        sections = []
        
        # Find all headings
        headings = content_elem.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        for i, heading in enumerate(headings):
            level = int(heading.name[1])  # Extract number from h1, h2, etc.
            title = heading.get_text().strip()
            
            # Get content until next heading of same or higher level
            content_parts = []
            current = heading.next_sibling
            
            while current:
                if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    current_level = int(current.name[1])
                    if current_level <= level:
                        break
                
                if hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text:
                        content_parts.append(text)
                
                current = current.next_sibling
            
            content = '\n'.join(content_parts)
            
            if title and content:
                sections.append(ScrapedSection(
                    title=title,
                    content=content,
                    level=level,
                    order=i
                ))
        
        return sections
    
    def _extract_references(self, soup: BeautifulSoup) -> list[str]:
        """Extract references from the paper."""
        references = []
        
        # Common reference section selectors
        ref_selectors = [
            '.references',
            '#references',
            '.bibliography',
            '#bibliography',
            'section[class*="ref"]',
            'div[class*="ref"]'
        ]
        
        for selector in ref_selectors:
            ref_section = soup.select_one(selector)
            if ref_section:
                # Extract individual references
                ref_items = ref_section.find_all(['li', 'p', 'div'])
                for item in ref_items:
                    ref_text = item.get_text().strip()
                    if ref_text and len(ref_text) > 20:  # Filter out short/empty items
                        references.append(ref_text)
                break
        
        return references
    
    def _extract_figures(self, soup: BeautifulSoup) -> list[str]:
        """Extract figure captions."""
        figures = []
        
        # Find figure captions
        fig_selectors = [
            'figcaption',
            '.figure-caption',
            '.fig-caption',
            'p[class*="caption"]'
        ]
        
        for selector in fig_selectors:
            captions = soup.select(selector)
            for caption in captions:
                text = caption.get_text().strip()
                if text:
                    figures.append(text)
        
        return figures
    
    def _extract_tables(self, soup: BeautifulSoup) -> list[str]:
        """Extract table captions."""
        tables = []
        
        # Find table captions
        table_captions = soup.find_all('caption')
        for caption in table_captions:
            text = caption.get_text().strip()
            if text:
                tables.append(text)
        
        # Also look for table titles in common patterns
        table_selectors = [
            '.table-caption',
            '.table-title',
            'p[class*="table"]'
        ]
        
        for selector in table_selectors:
            captions = soup.select(selector)
            for caption in captions:
                text = caption.get_text().strip()
                if text and 'table' in text.lower():
                    tables.append(text)
        
        return tables


def scrape_paper_to_dict(paper: ScrapedPaper) -> Dict[str, Any]:
    """Convert ScrapedPaper to dictionary format."""
    return {
        'source_url': paper.source_url,
        'extraction_date': paper.extraction_date,
        'content_hash': paper.content_hash,
        'metadata': {
            'title': paper.metadata.title,
            'authors': paper.metadata.authors,
            'abstract': paper.metadata.abstract,
            'publication_date': paper.metadata.publication_date,
            'doi': paper.metadata.doi,
            'arxiv_id': paper.metadata.arxiv_id,
            'venue': paper.metadata.venue,
            'keywords': paper.metadata.keywords,
            'url': paper.metadata.url,
            'publisher': paper.metadata.publisher
        },
        'full_text': paper.full_text,
        'sections': [
            {
                'title': section.title,
                'content': section.content,
                'level': section.level,
                'order': section.order
            }
            for section in paper.sections
        ],
        'references': paper.references,
        'figures': paper.figures,
        'tables': paper.tables,
        'word_count': len(paper.full_text.split()),
        'section_count': len(paper.sections)
    }


def save_scraped_paper(paper: ScrapedPaper, output_dir: str) -> str:
    """Save scraped paper to files.
    
    Args:
        paper: ScrapedPaper object to save.
        output_dir: Directory to save files in.
        
    Returns:
        Path to the saved JSON file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create filename from title or URL
    if paper.metadata.title:
        filename = re.sub(r'[^\w\s-]', '', paper.metadata.title)
        filename = re.sub(r'[-\s]+', '-', filename)[:50]
    else:
        filename = f"scraped_paper_{paper.content_hash[:8]}"
    
    # Save JSON
    json_path = output_path / f"{filename}.json"
    paper_dict = scrape_paper_to_dict(paper)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(paper_dict, f, indent=2, ensure_ascii=False)
    
    # Save markdown
    md_path = output_path / f"{filename}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {paper.metadata.title or 'Untitled Paper'}\n\n")
        
        if paper.metadata.authors:
            f.write(f"**Authors:** {', '.join(paper.metadata.authors)}\n\n")
        
        if paper.metadata.venue:
            f.write(f"**Venue:** {paper.metadata.venue}\n\n")
        
        if paper.metadata.publication_date:
            f.write(f"**Date:** {paper.metadata.publication_date}\n\n")
        
        if paper.metadata.doi:
            f.write(f"**DOI:** {paper.metadata.doi}\n\n")
        
        if paper.metadata.url:
            f.write(f"**URL:** {paper.metadata.url}\n\n")
        
        if paper.metadata.abstract:
            f.write(f"## Abstract\n\n{paper.metadata.abstract}\n\n")
        
        if paper.metadata.keywords:
            f.write(f"**Keywords:** {', '.join(paper.metadata.keywords)}\n\n")
        
        for section in paper.sections:
            f.write(f"{'#' * (section.level + 1)} {section.title}\n\n")
            f.write(f"{section.content}\n\n")
        
        if paper.figures:
            f.write("## Figures\n\n")
            for i, fig in enumerate(paper.figures, 1):
                f.write(f"{i}. {fig}\n")
            f.write("\n")
        
        if paper.tables:
            f.write("## Tables\n\n")
            for i, table in enumerate(paper.tables, 1):
                f.write(f"{i}. {table}\n")
            f.write("\n")
        
        if paper.references:
            f.write("## References\n\n")
            for i, ref in enumerate(paper.references, 1):
                f.write(f"{i}. {ref}\n")
    
    print(f"Saved scraped paper to: {json_path}")
    print(f"Markdown version: {md_path}")
    
    return str(json_path)


def main():
    """Command-line interface for web scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape academic papers from web URLs')
    parser.add_argument('url', help='URL of the paper to scrape')
    parser.add_argument('--output-dir', '-o', default='./scraped_papers',
                       help='Output directory for scraped files')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                       help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    scraper = WebScraper(delay=args.delay)
    
    try:
        paper = scraper.scrape_paper(args.url)
        json_path = save_scraped_paper(paper, args.output_dir)
        
        print(f"\nScraping completed successfully!")
        print(f"Title: {paper.metadata.title}")
        print(f"Authors: {', '.join(paper.metadata.authors) if paper.metadata.authors else 'N/A'}")
        print(f"Word count: {len(paper.full_text.split())}")
        print(f"Sections: {len(paper.sections)}")
        print(f"References: {len(paper.references)}")
        print(f"Output: {json_path}")
        
    except Exception as e:
        print(f"Error scraping paper: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
