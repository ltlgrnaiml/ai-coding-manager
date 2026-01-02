import { useState, useEffect, useCallback } from 'react'
import { 
  Search, 
  Grid3X3, 
  LayoutList, 
  Box, 
  Cpu, 
  AlertTriangle,
  BookOpen,
  Network,
  Maximize2,
  Filter
} from 'lucide-react'
import { useResearch, Paper } from '../hooks/useResearch'
import { PaperCard, PaperDetailModal, PaperGraph2D, PaperGraph3D } from '../components/research'

type ViewMode = 'list' | 'grid' | '2d' | '3d'

interface GPUCapabilities {
  webgl2: boolean
  webgpu: boolean
  maxTextureSize: number
  renderer: string
  estimatedMaxNodes: number
}

function detectGPUCapabilities(): GPUCapabilities {
  const canvas = document.createElement('canvas')
  const gl = canvas.getContext('webgl2')
  
  let webgl2 = false
  let maxTextureSize = 0
  let renderer = 'Unknown'
  
  if (gl) {
    webgl2 = true
    maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE)
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
    }
  }
  
  // Estimate max nodes based on GPU capability
  const estimatedMaxNodes = webgl2 ? Math.min(maxTextureSize / 4, 50000) : 1000
  
  // WebGPU detection (experimental)
  const webgpu = 'gpu' in navigator
  
  return {
    webgl2,
    webgpu,
    maxTextureSize,
    renderer,
    estimatedMaxNodes
  }
}

export default function ResearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [papers, setPapers] = useState<Paper[]>([])
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [gpuCapabilities, setGpuCapabilities] = useState<GPUCapabilities | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  
  const { searchPapers, getGPUStats, copyBibtex } = useResearch()
  const [gpuStats, setGpuStats] = useState<{ papersEmbedded: number; totalPapers: number } | null>(null)

  // Detect GPU capabilities on mount
  useEffect(() => {
    const caps = detectGPUCapabilities()
    setGpuCapabilities(caps)
    
    // If no WebGL2, force 2D mode max
    if (!caps.webgl2) {
      setViewMode('list')
    }
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

  // Load initial papers
  useEffect(() => {
    setIsLoading(true)
    searchPapers('', 50).then(results => {
      setPapers(results)
      setIsLoading(false)
    })
  }, [searchPapers])

  // Search handler
  const handleSearch = useCallback(async () => {
    setIsLoading(true)
    const results = await searchPapers(searchQuery, 50)
    setPapers(results)
    setIsLoading(false)
  }, [searchQuery, searchPapers])

  // Determine if 3D is available
  const is3DAvailable = gpuCapabilities?.webgl2 && papers.length < (gpuCapabilities?.estimatedMaxNodes || 1000)

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-950">
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
                {gpuStats ? `${gpuStats.papersEmbedded}/${gpuStats.totalPapers} papers embedded` : 'Loading...'}
                {gpuCapabilities?.webgl2 && (
                  <span className="ml-2 text-green-400">• GPU Accelerated</span>
                )}
              </p>
            </div>
          </div>

          {/* GPU Status Badge */}
          <div className="flex items-center gap-4">
            {gpuCapabilities && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs ${
                gpuCapabilities.webgl2 
                  ? 'bg-green-900/30 text-green-400' 
                  : 'bg-amber-900/30 text-amber-400'
              }`}>
                <Cpu className="w-4 h-4" />
                {gpuCapabilities.webgl2 ? 'WebGL2' : 'CPU Fallback'}
                {gpuCapabilities.webgpu && <span className="text-cyan-400">+ WebGPU</span>}
              </div>
            )}
          </div>
        </div>

        {/* Search & View Controls */}
        <div className="mt-4 flex items-center gap-4">
          {/* Search */}
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

          {/* Filter Button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-3 rounded-lg transition-colors ${
              showFilters ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            <Filter className="w-5 h-5" />
          </button>

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
            <button
              onClick={() => setViewMode('2d')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === '2d' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
              title="2D Graph (WebGL)"
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
              title={is3DAvailable ? '3D Graph (WebGL2)' : '3D unavailable - too many nodes or no WebGL2'}
            >
              <Box className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* GPU Fallback Warning */}
        {!gpuCapabilities?.webgl2 && (
          <div className="mt-3 flex items-center gap-2 text-amber-400 text-sm bg-amber-900/20 px-4 py-2 rounded-lg">
            <AlertTriangle className="w-4 h-4" />
            <span>WebGL2 not available. Running in CPU fallback mode with limited visualization.</span>
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-400">Loading papers...</div>
          </div>
        ) : viewMode === 'list' || viewMode === 'grid' ? (
          /* List/Grid View */
          <div className={`h-full overflow-y-auto p-6 ${
            viewMode === 'grid' 
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 content-start' 
              : 'space-y-3'
          }`}>
            {papers.length === 0 ? (
              <div className="col-span-full flex flex-col items-center justify-center py-20 text-gray-500">
                <BookOpen className="w-16 h-16 mb-4" />
                <p className="text-lg">No papers found</p>
                <p className="text-sm">Try a different search query</p>
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
        ) : viewMode === '2d' ? (
          /* 2D Graph View - Sigma.js WebGL */
          <PaperGraph2D
            papers={papers}
            onNodeClick={(paperId) => {
              const paper = papers.find(p => p.paper_id === paperId)
              if (paper) setSelectedPaper(paper)
            }}
            className="h-full"
          />
        ) : (
          /* 3D Graph View - deck.gl WebGL2 */
          <PaperGraph3D
            papers={papers}
            onNodeClick={(paperId) => {
              const paper = papers.find(p => p.paper_id === paperId)
              if (paper) setSelectedPaper(paper)
            }}
            className="h-full"
          />
        )}
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
