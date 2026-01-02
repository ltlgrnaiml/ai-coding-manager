"""DOI Lookup Tool for Academic Papers.

Uses CrossRef API and other services to get paper metadata from DOI.
"""

import json
import requests
from typing import Dict, Any, Optional


def lookup_doi_crossref(doi: str) -> Optional[Dict[str, Any]]:
    """Look up paper metadata using CrossRef API."""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        headers = {
            'User-Agent': 'AI-Coding-Manager/1.0 (mailto:research@example.com)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        work = data.get('message', {})
        
        # Extract relevant metadata
        metadata = {
            'doi': doi,
            'title': work.get('title', [''])[0] if work.get('title') else None,
            'authors': [],
            'abstract': work.get('abstract'),
            'publication_date': None,
            'venue': work.get('container-title', [''])[0] if work.get('container-title') else None,
            'publisher': work.get('publisher'),
            'url': work.get('URL'),
            'type': work.get('type'),
            'subject': work.get('subject', [])
        }
        
        # Extract authors
        if 'author' in work:
            for author in work['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                name = f"{given} {family}".strip()
                if name:
                    metadata['authors'].append(name)
        
        # Extract publication date
        if 'published-print' in work:
            date_parts = work['published-print'].get('date-parts', [[]])[0]
            if date_parts:
                metadata['publication_date'] = '-'.join(map(str, date_parts))
        elif 'published-online' in work:
            date_parts = work['published-online'].get('date-parts', [[]])[0]
            if date_parts:
                metadata['publication_date'] = '-'.join(map(str, date_parts))
        
        return metadata
        
    except Exception as e:
        print(f"CrossRef lookup failed: {e}")
        return None


def lookup_doi_semantic_scholar(doi: str) -> Optional[Dict[str, Any]]:
    """Look up paper using Semantic Scholar API."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
        params = {
            'fields': 'title,authors,abstract,venue,year,url,citationCount,referenceCount,fieldsOfStudy'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        metadata = {
            'doi': doi,
            'title': data.get('title'),
            'authors': [author.get('name', '') for author in data.get('authors', [])],
            'abstract': data.get('abstract'),
            'venue': data.get('venue'),
            'publication_date': str(data.get('year')) if data.get('year') else None,
            'url': data.get('url'),
            'citation_count': data.get('citationCount'),
            'reference_count': data.get('referenceCount'),
            'fields_of_study': data.get('fieldsOfStudy', [])
        }
        
        return metadata
        
    except Exception as e:
        print(f"Semantic Scholar lookup failed: {e}")
        return None


def main():
    """Command line interface for DOI lookup."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Look up paper metadata by DOI')
    parser.add_argument('doi', help='DOI of the paper to look up')
    parser.add_argument('--output', '-o', help='Output JSON file')
    
    args = parser.parse_args()
    
    print(f"Looking up DOI: {args.doi}")
    
    # Try CrossRef first
    metadata = lookup_doi_crossref(args.doi)
    if not metadata:
        # Try Semantic Scholar as fallback
        metadata = lookup_doi_semantic_scholar(args.doi)
    
    if metadata:
        print(f"Found paper: {metadata.get('title', 'Unknown title')}")
        print(f"Authors: {', '.join(metadata.get('authors', []))}")
        print(f"Venue: {metadata.get('venue', 'Unknown')}")
        print(f"Date: {metadata.get('publication_date', 'Unknown')}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata saved to: {args.output}")
        else:
            print("\nFull metadata:")
            print(json.dumps(metadata, indent=2))
    else:
        print("Failed to find metadata for this DOI")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
