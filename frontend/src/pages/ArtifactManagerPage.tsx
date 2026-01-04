import { useState, useEffect, useCallback } from 'react'
import { List, Network, BookOpen, Sparkles, Search } from 'lucide-react'
import {
  WorkflowSidebar,
  ArtifactGraph,
  ArtifactReader,
  ArtifactEditor,
  CommandPalette,
} from '../components/workflow'
import type { ArtifactType, FileFormat, ArtifactSummary } from '../components/workflow/types'
import { useResearch, type Paper } from '../hooks/useResearch'

const API_BASE = '/api/devtools'

export function ArtifactManagerPage() {
  const [selectedArtifact, setSelectedArtifact] = useState<{ id: string; type: ArtifactType; filePath: string; fileFormat: FileFormat } | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [allArtifacts, setAllArtifacts] = useState<ArtifactSummary[]>([])
  const [view, setView] = useState<'list' | 'graph'>('list')
  const [relatedPapers, setRelatedPapers] = useState<Paper[]>([])
  const [showRelatedPapers, setShowRelatedPapers] = useState(false)

  const { findRelatedPapersForArtifact } = useResearch()

  // Find related papers using GPU semantic search on artifact content (PLAN-0005 M02)
  const findRelatedPapers = useCallback(async (artifactId: string) => {
    const papers = await findRelatedPapersForArtifact(artifactId, 5)
    setRelatedPapers(papers)
    setShowRelatedPapers(true)
  }, [findRelatedPapersForArtifact])

  // Fetch all artifacts for command palette
  useEffect(() => {
    fetch(`${API_BASE}/artifacts`)
      .then(res => res.json())
      .then(data => setAllArtifacts(data.items || []))
      .catch(console.error)
  }, [])

  // Global Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleArtifactSelect = useCallback((artifact: ArtifactSummary) => {
    setSelectedArtifact({
      id: artifact.id,
      type: artifact.type,
      filePath: artifact.file_path,
      fileFormat: artifact.file_format || 'unknown'
    })
    setEditorOpen(false)
  }, [])

  // Graph nodes don't have file_format, so we need a separate handler
  const handleGraphNodeClick = useCallback((nodeId: string, type: ArtifactType) => {
    // Find the artifact in allArtifacts for file_format, fallback to 'unknown'
    const artifact = allArtifacts.find(a => a.id === nodeId)
    setSelectedArtifact({
      id: nodeId,
      type,
      filePath: artifact?.file_path || '',
      fileFormat: artifact?.file_format || 'unknown'
    })
    setEditorOpen(false)
  }, [allArtifacts])

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-white">
      {/* Header */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-zinc-800">
        <h1 className="text-lg font-semibold">Artifact Manager</h1>
        <button
          onClick={() => setPaletteOpen(true)}
          className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded text-sm bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white transition-colors"
        >
          <Search size={14} />
          Search (Cmd+K)
        </button>
      </div>

      {/* View Toggle + Research Button */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-zinc-800">
        <span className="text-xs text-zinc-500 mr-2">View:</span>
        <button
          onClick={() => setView('list')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            view === 'list' 
              ? 'bg-blue-600 text-white' 
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          }`}
        >
          <List size={14} />
          List
        </button>
        <button
          onClick={() => setView('graph')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors ${
            view === 'graph' 
              ? 'bg-blue-600 text-white' 
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          }`}
        >
          <Network size={14} />
          Graph
        </button>

        {/* Research Papers Button - Find related papers using GPU semantic search */}
        {selectedArtifact && (
          <button
            onClick={() => findRelatedPapers(selectedArtifact.id)}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded text-sm bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 transition-colors"
            title="Find related research papers"
          >
            <BookOpen size={14} />
            Related Papers
          </button>
        )}
      </div>

      {/* Related Papers Panel */}
      {showRelatedPapers && relatedPapers.length > 0 && (
        <div className="px-4 py-2 border-b border-zinc-800 bg-purple-950/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-purple-300 flex items-center gap-1">
              <Sparkles size={12} />
              Related Research ({relatedPapers.length} papers)
            </span>
            <button 
              onClick={() => setShowRelatedPapers(false)}
              className="text-xs text-zinc-500 hover:text-white"
            >
              Hide
            </button>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {relatedPapers.map(paper => (
              <a
                key={paper.paper_id}
                href={paper.arxiv_id ? `https://arxiv.org/abs/${paper.arxiv_id}` : '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 px-3 py-2 bg-zinc-800/50 rounded-lg hover:bg-zinc-700/50 transition-colors max-w-xs"
              >
                <p className="text-xs text-white truncate">{paper.title}</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {paper.similarity ? `${Math.round(paper.similarity * 100)}% match` : ''}
                  {paper.arxiv_id && ` • arXiv:${paper.arxiv_id}`}
                </p>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <WorkflowSidebar
          onArtifactSelect={handleArtifactSelect}
          selectedArtifactId={selectedArtifact?.id}
        />

        {/* Main panel */}
        <div className="flex-1 flex min-h-0 min-w-0">
          {view === 'graph' ? (
            <ArtifactGraph
              onNodeClick={handleGraphNodeClick}
              selectedNodeId={selectedArtifact?.id}
              className="flex-1"
            />
          ) : selectedArtifact ? (
            <ArtifactReader
              artifactId={selectedArtifact.id}
              artifactType={selectedArtifact.type}
              fileFormat={selectedArtifact.fileFormat}
              filePath={selectedArtifact.filePath}
              onEdit={() => setEditorOpen(true)}
              className="flex-1"
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-zinc-500">
              <div className="text-center">
                <p className="text-lg mb-2">No artifact selected</p>
                <p className="text-sm">Select an artifact from the sidebar or press Cmd+K to search</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Editor slide-in */}
      {selectedArtifact && (
        <ArtifactEditor
          artifactId={selectedArtifact.id}
          artifactType={selectedArtifact.type}
          isOpen={editorOpen}
          onClose={() => setEditorOpen(false)}
        />
      )}

      {/* Command palette */}
      <CommandPalette
        isOpen={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        artifacts={allArtifacts}
        onSelect={handleArtifactSelect}
      />
    </div>
  )
}
