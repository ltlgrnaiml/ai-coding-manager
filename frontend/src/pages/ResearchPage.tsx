import { useState, useEffect, useCallback } from 'react'
import { 
  Search, 
  Grid3X3, 
  LayoutList, 
  Box, 
  Cpu, 
  BookOpen,
  Network,
  Tag,
  Users,
  TrendingUp,
  Clock,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  PanelLeftClose,
  PanelLeft,
  Layers,
  Link2,
  Calendar,
  LayoutGrid
} from 'lucide-react'
import { useResearch, Paper } from '../hooks/useResearch'
import { PaperCard, PaperDetailModal, PaperGraph3D } from '../components/research'
import RelationshipGraph from '../components/research/RelationshipGraph'
import SimilarityGraph from '../components/research/SimilarityGraphV2'
import TimelineGraph from '../components/research/TimelineGraphV2'
import TopicTreemap from '../components/research/TopicTreemap'

type ViewMode = 'list' | 'grid' | 'similarity' | 'timeline' | 'treemap' | '2d' | '3d'

interface GPUCapabilities {
  webgl2: boolean
  webgpu: boolean
  renderer: string
  estimatedMaxNodes: number
}

interface Category {
  category: string
  count: number
}

interface Concept {
  concept: string
  frequency: number
}

function detectGPUCapabilities(): GPUCapabilities {
  const canvas = document.createElement('canvas')
  const gl = canvas.getContext('webgl2')
  
  let webgl2 = false
  let renderer = 'Unknown'
  
  if (gl) {
    webgl2 = true
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
    }
  }
  
  const estimatedMaxNodes = webgl2 ? 50000 : 1000
  const webgpu = 'gpu' in navigator
  
  return { webgl2, webgpu, renderer, estimatedMaxNodes }
}

// Sample categories for exploration (will be fetched from API)
// Maps display name to search query (acronyms don't embed well semantically)
const SAMPLE_CATEGORIES = [
  { category: 'Agentic AI', count: 24, searchQuery: 'agentic AI agent autonomous' },
  { category: 'RAG Systems', count: 18, searchQuery: 'retrieval augmented generation RAG' },
  { category: 'Context Compression', count: 12, searchQuery: 'context compression window length' },
  { category: 'Code Generation', count: 15, searchQuery: 'code generation programming synthesis' },
  { category: 'Multi-Agent', count: 9, searchQuery: 'multi-agent collaboration cooperation' },
  { category: 'Prompt Engineering', count: 8, searchQuery: 'prompt engineering instruction tuning' },
]

// Helper to get search query for a category
const getCategorySearchQuery = (categoryName: string): string => {
  const cat = SAMPLE_CATEGORIES.find(c => c.category === categoryName)
  return cat?.searchQuery || categoryName
}

// Sample concepts for exploration
const SAMPLE_CONCEPTS = [
  { concept: 'transformer', frequency: 45 },
  { concept: 'attention mechanism', frequency: 38 },
  { concept: 'embedding', frequency: 35 },
  { concept: 'retrieval', frequency: 32 },
  { concept: 'context window', frequency: 28 },
  { concept: 'fine-tuning', frequency: 25 },
  { concept: 'prompt', frequency: 22 },
  { concept: 'agent', frequency: 20 },
]

export default function ResearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [papers, setPapers] = useState<Paper[]>([])
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [gpuCapabilities, setGpuCapabilities] = useState<GPUCapabilities | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [categories] = useState<Category[]>(SAMPLE_CATEGORIES)
  const [concepts] = useState<Concept[]>(SAMPLE_CONCEPTS)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Auto-collapse sidebar when viewing graphs
  useEffect(() => {
    if (viewMode === '2d' || viewMode === '3d' || viewMode === 'similarity' || viewMode === 'timeline' || viewMode === 'treemap') {
      setSidebarOpen(false)
    }
  }, [viewMode])
  
  const { searchPapers, listAllPapers, getGPUStats, copyBibtex } = useResearch()
  const [gpuStats, setGpuStats] = useState<{ papersEmbedded: number; totalPapers: number } | null>(null)

  // Detect GPU capabilities on mount
  useEffect(() => {
    const caps = detectGPUCapabilities()
    setGpuCapabilities(caps)
    if (!caps.webgl2) setViewMode('list')
  }, [])

  // Load GPU stats
  useEffect(() => {
    getGPUStats().then(stats => {
      if (stats) {
        setGpuStats({
          papersEmbedded: stats.papers_embedded,
          totalPapers: stats.papers_total
        })
      }
    })
  }, [getGPUStats])

  // Load papers on mount - THIS IS THE KEY FIX
  useEffect(() => {
    setIsLoading(true)
    listAllPapers(79).then(results => {
      setPapers(results)
      setIsLoading(false)
    })
  }, [listAllPapers])

  // Search handler
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      const results = await listAllPapers(79)
      setPapers(results)
      return
    }
    setIsLoading(true)
    const results = await searchPapers(searchQuery, 50)
    setPapers(results)
    setIsLoading(false)
  }, [searchQuery, searchPapers, listAllPapers])

  // Category filter handler
  const handleCategoryClick = useCallback(async (category: string) => {
    setSelectedCategory(category === selectedCategory ? null : category)
    setIsLoading(true)
    // Use expanded search query for better semantic matching
    const searchQuery = getCategorySearchQuery(category)
    const results = await searchPapers(searchQuery, 50)
    setPapers(results)
    setIsLoading(false)
  }, [selectedCategory, searchPapers])

  // Concept click handler
  const handleConceptClick = useCallback(async (concept: string) => {
    setSearchQuery(concept)
    setIsLoading(true)
    const results = await searchPapers(concept, 50)
    setPapers(results)
    setIsLoading(false)
  }, [searchPapers])

  const is3DAvailable = gpuCapabilities?.webgl2 && papers.length < (gpuCapabilities?.estimatedMaxNodes || 1000)

  return (
    <div className="flex-1 flex h-full bg-gray-950 relative">
      {/* Sidebar Toggle Button (visible when collapsed) */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="absolute left-2 top-2 z-20 p-2 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors"
          title="Open sidebar"
        >
          <PanelLeft className="w-5 h-5 text-gray-400" />
        </button>
      )}

      {/* Left Sidebar - Discovery Panel */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-0'} border-r border-gray-800 flex flex-col bg-gray-900/50 overflow-hidden transition-all duration-300 ease-in-out`}>
        {/* Stats Header */}
        <div className="p-4 border-b border-gray-800 min-w-[256px]">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-purple-400">
              <Layers className="w-5 h-5" />
              <span className="font-semibold">Knowledge Base</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1 hover:bg-gray-700 rounded transition-colors"
              title="Close sidebar"
            >
              <PanelLeftClose className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-800/50 rounded-lg p-2 text-center">
              <p className="text-2xl font-bold text-white">{gpuStats?.totalPapers ?? 0}</p>
              <p className="text-gray-400">Papers</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-2 text-center">
              <p className="text-2xl font-bold text-green-400">{gpuStats?.papersEmbedded ?? 0}</p>
              <p className="text-gray-400">Embedded</p>
            </div>
          </div>
        </div>

        {/* Topics/Categories */}
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Tag className="w-3 h-3" />
            Topics
          </h3>
          <div className="space-y-1">
            {categories.map(cat => (
              <button
                key={cat.category}
                onClick={() => handleCategoryClick(cat.category)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between transition-colors ${
                  selectedCategory === cat.category
                    ? 'bg-purple-600/30 text-purple-300'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                <span>{cat.category}</span>
                <span className="text-xs text-gray-500">{cat.count}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Concept Cloud */}
        <div className="p-4 border-b border-gray-800">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Sparkles className="w-3 h-3" />
            Top Concepts
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {concepts.map(c => (
              <button
                key={c.concept}
                onClick={() => handleConceptClick(c.concept)}
                className="px-2 py-1 text-xs bg-gray-800 hover:bg-purple-600/30 text-gray-300 hover:text-purple-300 rounded-full transition-colors"
                title={`${c.frequency} occurrences`}
              >
                {c.concept}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="p-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <TrendingUp className="w-3 h-3" />
            Explore
          </h3>
          <div className="space-y-2">
            <button 
              onClick={() => handleSearch()}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <Clock className="w-4 h-4 text-cyan-400" />
              <span>Recent Papers</span>
              <ChevronRight className="w-4 h-4 ml-auto text-gray-600" />
            </button>
            <button 
              onClick={() => setViewMode('2d')}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <Network className="w-4 h-4 text-purple-400" />
              <span>Relationship Graph</span>
              <ChevronRight className="w-4 h-4 ml-auto text-gray-600" />
            </button>
            <button 
              onClick={() => setViewMode('3d')}
              disabled={!is3DAvailable}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <Box className="w-4 h-4 text-cyan-400" />
              <span>3D Explorer</span>
              <ChevronRight className="w-4 h-4 ml-auto text-gray-600" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-600/20 rounded-lg">
                <BookOpen className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Research Papers</h1>
                <p className="text-sm text-gray-400">
                  {papers.length} papers loaded
                  {gpuCapabilities?.webgl2 && (
                    <span className="ml-2 text-green-400">• GPU Accelerated</span>
                  )}
                </p>
              </div>
            </div>

            {/* GPU Status Badge */}
            {gpuCapabilities && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs ${
                gpuCapabilities.webgl2 
                  ? 'bg-green-900/30 text-green-400' 
                  : 'bg-amber-900/30 text-amber-400'
              }`}>
                <Cpu className="w-4 h-4" />
                {gpuCapabilities.webgl2 ? 'WebGL2' : 'CPU'}
                {gpuCapabilities.webgpu && <span className="text-cyan-400">+ WebGPU</span>}
              </div>
            )}
          </div>

          {/* Search & View Controls */}
          <div className="mt-4 flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search papers by title, abstract, or concepts..."
                className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-11 pr-4 py-3 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'list' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="List View"
              >
                <LayoutList className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'grid' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="Grid View"
              >
                <Grid3X3 className="w-5 h-5" />
              </button>
              <div className="w-px h-6 bg-gray-700 mx-1" />
              <button
                onClick={() => setViewMode('similarity')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'similarity' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="Similarity Graph (Connected Papers style)"
              >
                <Link2 className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('timeline')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'timeline' ? 'bg-amber-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="Timeline (Litmaps style)"
              >
                <Calendar className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('treemap')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === 'treemap' ? 'bg-green-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="Topic Treemap"
              >
                <LayoutGrid className="w-5 h-5" />
              </button>
              <div className="w-px h-6 bg-gray-700 mx-1" />
              <button
                onClick={() => setViewMode('2d')}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === '2d' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
                }`}
                title="Relationship Explorer"
              >
                <Network className="w-5 h-5" />
              </button>
              <button
                onClick={() => is3DAvailable && setViewMode('3d')}
                disabled={!is3DAvailable}
                className={`p-2 rounded-md transition-colors ${
                  viewMode === '3d' 
                    ? 'bg-purple-600 text-white' 
                    : is3DAvailable 
                      ? 'text-gray-400 hover:text-white' 
                      : 'text-gray-600 cursor-not-allowed'
                }`}
                title={is3DAvailable ? '3D Graph (WebGL2)' : '3D unavailable'}
              >
                <Box className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-400">Loading papers...</p>
              </div>
            </div>
          ) : viewMode === 'list' || viewMode === 'grid' ? (
            <div className={`h-full overflow-y-auto p-6 ${
              viewMode === 'grid' 
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 content-start' 
                : 'space-y-3'
            }`}>
              {papers.length === 0 ? (
                <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500">
                  <BookOpen className="w-16 h-16 mb-4" />
                  <p className="text-lg">No papers found</p>
                  <p className="text-sm mb-4">Try selecting a topic from the sidebar</p>
                  <button
                    onClick={async () => {
                      setSearchQuery('')
                      setSelectedCategory(null)
                      setIsLoading(true)
                      const results = await listAllPapers(79)
                      setPapers(results)
                      setIsLoading(false)
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500"
                  >
                    Show All Papers
                  </button>
                </div>
              ) : (
                papers.map(paper => (
                  <PaperCard
                    key={paper.paper_id}
                    paper={paper}
                    onCopyBibtex={copyBibtex}
                    onInsertReference={() => {}}
                    onViewDetails={() => setSelectedPaper(paper)}
                    compact={viewMode === 'grid'}
                  />
                ))
              )}
            </div>
          ) : viewMode === 'similarity' ? (
            <SimilarityGraph
              key={`similarity-${papers.length}`}
              papers={papers}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.paper_id === paperId)
                if (paper) setSelectedPaper(paper)
              }}
              className="h-full"
            />
          ) : viewMode === 'timeline' ? (
            <TimelineGraph
              key={`timeline-${papers.length}`}
              papers={papers}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.paper_id === paperId)
                if (paper) setSelectedPaper(paper)
              }}
              className="h-full"
            />
          ) : viewMode === 'treemap' ? (
            <TopicTreemap
              key={`treemap-${papers.length}`}
              papers={papers}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.paper_id === paperId)
                if (paper) setSelectedPaper(paper)
              }}
              className="h-full"
            />
          ) : viewMode === '2d' ? (
            <RelationshipGraph
              key={`rel-${papers.length}`}
              papers={papers}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.paper_id === paperId)
                if (paper) setSelectedPaper(paper)
              }}
              className="h-full"
            />
          ) : (
            <PaperGraph3D
              key={`3d-${papers.length}`}
              papers={papers}
              onNodeClick={(paperId) => {
                const paper = papers.find(p => p.paper_id === paperId)
                if (paper) setSelectedPaper(paper)
              }}
              className="h-full"
            />
          )}
        </div>
      </div>

      {/* Paper Detail Modal */}
      {selectedPaper && (
        <PaperDetailModal
          paper={selectedPaper}
          onClose={() => setSelectedPaper(null)}
          onInsertReference={() => {}}
        />
      )}
    </div>
  )
}
