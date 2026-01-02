import { useState, useEffect, useCallback } from 'react';
import { 
  Search, ChevronLeft, ChevronRight, Cpu, RefreshCw, 
  ExternalLink, Settings, X, Maximize2, Minimize2
} from 'lucide-react';
import { useResearch, Paper, GPUStats } from '../../hooks/useResearch';
import { PaperCard } from './PaperCard';
import { PaperDetailModal } from './PaperDetailModal';

interface ResearchPaneProps {
  defaultCollapsed?: boolean;
  onInsertReference?: (paper: Paper, format: 'bibtex' | 'markdown' | 'link') => void;
  position?: 'left' | 'right';
}

export function ResearchPane({ 
  defaultCollapsed = true, 
  onInsertReference,
  position = 'right'
}: ResearchPaneProps) {
  const { searchPapers, copyBibtex, getGPUStats, loading } = useResearch();
  
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [poppedOut, setPoppedOut] = useState(false);
  const [query, setQuery] = useState('');
  const [papers, setPapers] = useState<Paper[]>([]);
  const [gpuStats, setGpuStats] = useState<GPUStats | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Load GPU stats on mount
  useEffect(() => {
    getGPUStats().then(setGpuStats);
  }, [getGPUStats]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    const results = await searchPapers(query, 10);
    setPapers(results);
  }, [query, searchPapers]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleInsertReference = (paper: Paper) => {
    onInsertReference?.(paper, 'markdown');
  };

  const handlePopOut = () => {
    setPoppedOut(true);
    // In a real implementation, this would open a new window
    // For now, we'll just expand to full screen
  };

  if (collapsed && !poppedOut) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className={`fixed ${position === 'right' ? 'right-0' : 'left-0'} top-1/2 -translate-y-1/2 
          bg-slate-800 border border-slate-700 p-2 rounded-l-lg 
          hover:bg-slate-700 transition-colors z-40`}
        title="Open Research Pane"
      >
        {position === 'right' ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
    );
  }

  const paneContent = (
    <>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="text-lg">🔬</span>
          <h3 className="font-semibold text-white">Research Papers</h3>
        </div>
        <div className="flex items-center gap-1">
          {gpuStats?.gpu_available && (
            <div className="flex items-center gap-1 px-2 py-1 bg-green-500/10 rounded text-xs text-green-400">
              <Cpu className="w-3 h-3" />
              GPU
            </div>
          )}
          <button
            onClick={handlePopOut}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors"
            title={poppedOut ? "Dock panel" : "Pop out"}
          >
            {poppedOut ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
          <button
            onClick={() => poppedOut ? setPoppedOut(false) : setCollapsed(true)}
            className="p-1.5 hover:bg-slate-700 rounded transition-colors"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-3 border-b border-slate-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search papers, concepts..."
            className="w-full pl-9 pr-10 py-2 bg-slate-800 border border-slate-600 rounded-lg 
              text-sm text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500"
          />
          {loading ? (
            <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400 animate-spin" />
          ) : (
            <button
              onClick={handleSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-700 rounded"
            >
              <Search className="w-4 h-4 text-slate-400" />
            </button>
          )}
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && gpuStats && (
        <div className="p-3 border-b border-slate-700 bg-slate-800/50 text-xs">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-slate-400">GPU:</span>
              <span className="ml-1 text-white">{gpuStats.gpu_name}</span>
            </div>
            <div>
              <span className="text-slate-400">VRAM:</span>
              <span className="ml-1 text-white">{gpuStats.gpu_memory_gb} GB</span>
            </div>
            <div>
              <span className="text-slate-400">Papers:</span>
              <span className="ml-1 text-white">{gpuStats.papers_embedded}/{gpuStats.papers_total}</span>
            </div>
            <div>
              <span className="text-slate-400">Coverage:</span>
              <span className="ml-1 text-green-400">{gpuStats.embedding_coverage}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {papers.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Search for research papers</p>
            <p className="text-xs mt-1">GPU-accelerated semantic search</p>
          </div>
        ) : (
          papers.map(paper => (
            <PaperCard
              key={paper.paper_id}
              paper={paper}
              onCopyBibtex={copyBibtex}
              onInsertReference={handleInsertReference}
              onViewDetails={setSelectedPaper}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-slate-700 text-xs text-slate-500 text-center">
        {papers.length > 0 && `${papers.length} results`}
        {gpuStats?.gpu_available && ' • GPU-accelerated'}
      </div>
    </>
  );

  // Popped out view (full screen overlay)
  if (poppedOut) {
    return (
      <>
        <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setPoppedOut(false)} />
        <div className="fixed inset-4 bg-slate-900 border border-slate-700 rounded-xl z-50 flex flex-col overflow-hidden">
          {paneContent}
        </div>
        {selectedPaper && (
          <PaperDetailModal
            paper={selectedPaper}
            onClose={() => setSelectedPaper(null)}
            onInsertReference={handleInsertReference}
          />
        )}
      </>
    );
  }

  // Docked side panel
  return (
    <>
      <div 
        className={`fixed ${position === 'right' ? 'right-0' : 'left-0'} top-0 h-full w-80 
          bg-slate-900 border-l border-slate-700 z-40 flex flex-col`}
      >
        {paneContent}
      </div>
      {selectedPaper && (
        <PaperDetailModal
          paper={selectedPaper}
          onClose={() => setSelectedPaper(null)}
          onInsertReference={handleInsertReference}
        />
      )}
    </>
  );
}

export default ResearchPane;
