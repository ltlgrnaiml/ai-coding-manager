import { useState, useCallback } from 'react';

// API base - empty string uses relative URLs (works in Docker with nginx proxy)
const API_BASE = '';

export interface Paper {
  paper_id: string;
  title: string;
  abstract?: string;
  authors?: string;
  arxiv_id?: string;
  similarity?: number;
}

export interface Concept {
  value: string;
  type: string;
  display: string;
  metadata?: {
    frequency?: number;
    concept_type?: string;
  };
}

export interface AutocompleteResult {
  value: string;
  type: 'paper' | 'concept' | 'author';
  display: string;
  metadata?: Record<string, unknown>;
}

export interface BibtexResult {
  bibtex: string;
  cite_key: string;
  paper_id: string;
}

export interface GPUStats {
  gpu_available: boolean;
  gpu_name: string;
  gpu_memory_gb: number;
  device: string;
  batch_size: number;
  model: string;
  papers_embedded: number;
  papers_total: number;
  chunks_embedded: number;
  chunks_total: number;
  embedding_coverage: number;
}

export function useResearch() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchPapers = useCallback(async (query: string, topK = 10): Promise<Paper[]> => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/gpu/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK, search_type: 'hybrid' })
      });
      if (!res.ok) throw new Error('Search failed');
      return await res.json();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const autocomplete = useCallback(async (
    prefix: string, 
    type?: 'paper' | 'concept' | 'author'
  ): Promise<AutocompleteResult[]> => {
    if (prefix.length < 2) return [];
    try {
      const params = new URLSearchParams({ prefix });
      if (type) params.append('type', type);
      const res = await fetch(`${API_BASE}/api/aikh/autocomplete?${params}`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }, []);

  const getBibtex = useCallback(async (paperId: string): Promise<BibtexResult | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/aikh/papers/${paperId}/bibtex`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  const copyBibtex = useCallback(async (paperId: string): Promise<boolean> => {
    const result = await getBibtex(paperId);
    if (result) {
      await navigator.clipboard.writeText(result.bibtex);
      return true;
    }
    return false;
  }, [getBibtex]);

  const getGPUStats = useCallback(async (): Promise<GPUStats | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/gpu/stats`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  const enrichContext = useCallback(async (message: string, maxPapers = 3): Promise<{
    papers: Paper[];
    concepts: string[];
    related_concepts: { concept: string; strength: number }[];
  } | null> => {
    try {
      const res = await fetch(`${API_BASE}/api/aikh/enrich/gpu`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, max_papers: maxPapers, include_concepts: true })
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  // Get all papers (for initial display)
  const listAllPapers = useCallback(async (limit = 100): Promise<Paper[]> => {
    try {
      const res = await fetch(`${API_BASE}/api/aikh/papers?limit=${limit}`);
      if (!res.ok) {
        // Fallback: use search with empty query
        return searchPapers('', limit);
      }
      const data = await res.json();
      return data.papers || data || [];
    } catch {
      // Fallback to search
      return searchPapers('', limit);
    }
  }, [searchPapers]);

  // Get categories/topics for exploration
  const getCategories = useCallback(async (): Promise<{ category: string; count: number }[]> => {
    try {
      const res = await fetch(`${API_BASE}/api/aikh/categories`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }, []);

  // Get top concepts for exploration
  const getTopConcepts = useCallback(async (limit = 20): Promise<{ concept: string; frequency: number }[]> => {
    try {
      const res = await fetch(`${API_BASE}/api/aikh/concepts?limit=${limit}`);
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }, []);

  return {
    loading,
    error,
    searchPapers,
    listAllPapers,
    getCategories,
    getTopConcepts,
    autocomplete,
    getBibtex,
    copyBibtex,
    getGPUStats,
    enrichContext
  };
}
