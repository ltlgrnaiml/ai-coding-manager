import { useEffect, useState, useCallback, useMemo, Component, ReactNode } from 'react'
import Graph from 'graphology'
import { SigmaContainer, useLoadGraph, useSigma, useRegisterEvents } from '@react-sigma/core'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import '@react-sigma/core/lib/style.css'
import { Paper } from '../../hooks/useResearch'

// Error boundary for Sigma WebGL errors
class SigmaErrorBoundary extends Component<{ children: ReactNode; onError: (error: string) => void }, { hasError: boolean }> {
  constructor(props: { children: ReactNode; onError: (error: string) => void }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    this.props.onError(error.message)
  }

  render() {
    if (this.state.hasError) {
      return null
    }
    return this.props.children
  }
}

interface PaperGraph2DProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Category colors - professional palette
const CATEGORY_COLORS: Record<string, string> = {
  'agentic-ai': '#ef4444',      // Red
  'rag': '#f97316',             // Orange
  'context': '#eab308',         // Yellow
  'code-generation': '#22c55e', // Green
  'multi-agent': '#14b8a6',     // Teal
  'embedding': '#3b82f6',       // Blue
  'transformer': '#8b5cf6',     // Purple
  'prompt': '#ec4899',          // Pink
  'default': '#6366f1'          // Indigo
}

// Detect category from paper title/abstract
function detectCategory(paper: Paper): string {
  const text = ((paper.title || '') + ' ' + (paper.abstract || '')).toLowerCase()
  
  if (text.includes('agent') || text.includes('agentic')) return 'agentic-ai'
  if (text.includes('retrieval') || text.includes('rag')) return 'rag'
  if (text.includes('context') || text.includes('window')) return 'context'
  if (text.includes('code') || text.includes('generation')) return 'code-generation'
  if (text.includes('multi-agent') || text.includes('collaboration')) return 'multi-agent'
  if (text.includes('embed') || text.includes('vector')) return 'embedding'
  if (text.includes('transformer') || text.includes('attention')) return 'transformer'
  if (text.includes('prompt') || text.includes('instruction')) return 'prompt'
  return 'default'
}

// Legend component
function GraphLegend({ 
  categories, 
  activeCategories, 
  onToggle 
}: { 
  categories: { name: string; color: string; count: number }[]
  activeCategories: Set<string>
  onToggle: (cat: string) => void 
}) {
  return (
    <div className="absolute top-4 left-4 bg-gray-900/95 border border-gray-700 rounded-xl p-4 shadow-xl max-w-xs">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <span className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-cyan-500" />
        Categories
      </h3>
      <div className="space-y-2">
        {categories.map(cat => (
          <button
            key={cat.name}
            onClick={() => onToggle(cat.name)}
            className={`w-full flex items-center gap-3 px-2 py-1.5 rounded-lg transition-all ${
              activeCategories.has(cat.name) 
                ? 'bg-gray-800' 
                : 'opacity-40 hover:opacity-70'
            }`}
          >
            <span 
              className="w-4 h-4 rounded-full flex-shrink-0"
              style={{ backgroundColor: cat.color }}
            />
            <span className="text-sm text-gray-200 text-left flex-1 truncate capitalize">
              {cat.name.replace(/-/g, ' ')}
            </span>
            <span className="text-xs text-gray-500">{cat.count}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

// Hover tooltip
function NodeTooltip({ paper, position }: { paper: Paper | null; position: { x: number; y: number } }) {
  if (!paper) return null
  
  return (
    <div 
      className="absolute pointer-events-none bg-gray-900/95 border border-gray-600 rounded-lg p-3 shadow-xl max-w-sm z-50"
      style={{ 
        left: position.x + 15, 
        top: position.y - 10,
        transform: 'translateY(-50%)'
      }}
    >
      <h4 className="text-sm font-medium text-white mb-1 line-clamp-2">
        {paper.title || 'Untitled'}
      </h4>
      {paper.authors && (
        <p className="text-xs text-gray-400 mb-2">{paper.authors}</p>
      )}
      {paper.abstract && (
        <p className="text-xs text-gray-500 line-clamp-3">{paper.abstract}</p>
      )}
      <p className="text-xs text-cyan-400 mt-2">Click to view details</p>
    </div>
  )
}

// Graph events handler
function GraphEvents({ 
  papers, 
  onNodeClick, 
  onHover 
}: { 
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  onHover: (paper: Paper | null, pos: { x: number; y: number }) => void
}) {
  const sigma = useSigma()
  const registerEvents = useRegisterEvents()

  useEffect(() => {
    registerEvents({
      clickNode: ({ node }) => onNodeClick?.(node),
      enterNode: ({ node, event }) => {
        const paper = papers.find(p => p.paper_id === node)
        if (paper) {
          onHover(paper, { x: event.x, y: event.y })
        }
        sigma.getGraph().setNodeAttribute(node, 'highlighted', true)
        sigma.refresh()
      },
      leaveNode: ({ node }) => {
        onHover(null, { x: 0, y: 0 })
        sigma.getGraph().setNodeAttribute(node, 'highlighted', false)
        sigma.refresh()
      }
    })
  }, [registerEvents, papers, onNodeClick, onHover, sigma])

  return null
}

// Graph data loader with ForceAtlas2 layout
function LoadGraphData({ 
  papers, 
  activeCategories 
}: { 
  papers: Paper[]
  activeCategories: Set<string>
}) {
  const loadGraph = useLoadGraph()
  const sigma = useSigma()

  useEffect(() => {
    const graph = new Graph()
    
    // Filter papers by active categories
    const filteredPapers = papers.filter(p => activeCategories.has(detectCategory(p)))
    
    // Create nodes with category-based positioning
    const categoryPositions: Record<string, { x: number; y: number; count: number }> = {}
    
    filteredPapers.forEach((paper, index) => {
      const category = detectCategory(paper)
      
      // Initialize category position
      if (!categoryPositions[category]) {
        const catIndex = Object.keys(categoryPositions).length
        const angle = (2 * Math.PI * catIndex) / 8
        categoryPositions[category] = {
          x: Math.cos(angle) * 200,
          y: Math.sin(angle) * 200,
          count: 0
        }
      }
      
      // Position within category cluster
      const catPos = categoryPositions[category]
      const localAngle = (2 * Math.PI * catPos.count) / 10
      const localRadius = 30 + catPos.count * 5
      catPos.count++
      
      const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.default
      const similarity = paper.similarity || 0.5
      
      graph.addNode(paper.paper_id, {
        label: paper.title?.slice(0, 50) || 'Untitled',
        x: catPos.x + Math.cos(localAngle) * localRadius + (Math.random() - 0.5) * 20,
        y: catPos.y + Math.sin(localAngle) * localRadius + (Math.random() - 0.5) * 20,
        size: 8 + similarity * 12,
        color: color,
        category: category,
        borderColor: '#ffffff',
        type: 'circle'
      })
    })

    // Create edges based on shared concepts/similarity
    filteredPapers.forEach((paper, i) => {
      const paperCategory = detectCategory(paper)
      
      filteredPapers.forEach((other, j) => {
        if (i >= j) return // Avoid duplicates
        
        const otherCategory = detectCategory(other)
        const sameCategory = paperCategory === otherCategory
        
        // Connect papers in same category more strongly
        if (sameCategory && Math.random() < 0.4) {
          graph.addEdge(paper.paper_id, other.paper_id, {
            size: 1.5,
            color: CATEGORY_COLORS[paperCategory] + '40', // 25% opacity
            type: 'line'
          })
        }
        // Occasionally connect across categories
        else if (!sameCategory && Math.random() < 0.05) {
          graph.addEdge(paper.paper_id, other.paper_id, {
            size: 0.5,
            color: '#37415150',
            type: 'line'
          })
        }
      })
    })

    // Apply ForceAtlas2 layout for organic positioning
    if (graph.order > 0) {
      forceAtlas2.assign(graph, {
        iterations: 100,
        settings: {
          gravity: 1,
          scalingRatio: 10,
          strongGravityMode: true,
          barnesHutOptimize: graph.order > 50
        }
      })
    }

    loadGraph(graph)
  }, [papers, activeCategories, loadGraph])

  return null
}

export function PaperGraph2D({ papers, onNodeClick, className = '' }: PaperGraph2DProps) {
  const [hoveredPaper, setHoveredPaper] = useState<Paper | null>(null)
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 })
  const [activeCategories, setActiveCategories] = useState<Set<string>>(new Set(Object.keys(CATEGORY_COLORS)))

  // Calculate category counts
  const categoryStats = useMemo(() => {
    const counts: Record<string, number> = {}
    papers.forEach(p => {
      const cat = detectCategory(p)
      counts[cat] = (counts[cat] || 0) + 1
    })
    return Object.entries(counts)
      .map(([name, count]) => ({
        name,
        color: CATEGORY_COLORS[name] || CATEGORY_COLORS.default,
        count
      }))
      .sort((a, b) => b.count - a.count)
  }, [papers])

  const toggleCategory = useCallback((cat: string) => {
    setActiveCategories(prev => {
      const next = new Set(prev)
      if (next.has(cat)) {
        next.delete(cat)
      } else {
        next.add(cat)
      }
      return next
    })
  }, [])

  const handleHover = useCallback((paper: Paper | null, pos: { x: number; y: number }) => {
    setHoveredPaper(paper)
    setHoverPosition(pos)
  }, [])

  const [graphError, setGraphError] = useState<string | null>(null)

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  if (graphError) {
    return (
      <div className={`flex flex-col items-center justify-center h-full bg-gray-900 ${className}`}>
        <p className="text-red-400 mb-4">Graph rendering error</p>
        <p className="text-gray-500 text-sm mb-4">{graphError}</p>
        <button 
          onClick={() => setGraphError(null)}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-500"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className={`h-full w-full relative ${className}`}>
      <SigmaErrorBoundary onError={setGraphError}>
        <SigmaContainer
          style={{ height: '100%', width: '100%', background: '#0f172a' }}
          settings={{
          renderLabels: true,
          labelSize: 11,
          labelWeight: 'bold',
          labelColor: { color: '#e2e8f0' },
          labelFont: 'Inter, system-ui, sans-serif',
          defaultNodeColor: '#6366f1',
          defaultEdgeColor: '#374151',
          defaultEdgeType: 'line',
          minCameraRatio: 0.1,
          maxCameraRatio: 10,
          labelRenderedSizeThreshold: 4,
          labelDensity: 0.3,
          nodeProgramClasses: {},
          nodeReducer: (node, data) => ({
            ...data,
            size: data.highlighted ? data.size * 1.5 : data.size,
            color: data.highlighted ? '#ffffff' : data.color,
            zIndex: data.highlighted ? 1 : 0
          }),
          edgeReducer: (edge, data) => data
        }}
      >
        <LoadGraphData papers={papers} activeCategories={activeCategories} />
        <GraphEvents papers={papers} onNodeClick={onNodeClick} onHover={handleHover} />
        </SigmaContainer>
      </SigmaErrorBoundary>

      {/* Legend */}
      <GraphLegend 
        categories={categoryStats}
        activeCategories={activeCategories}
        onToggle={toggleCategory}
      />

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-gray-900/95 border border-gray-700 rounded-lg px-4 py-2">
        <p className="text-sm text-cyan-400 font-mono">
          {papers.filter(p => activeCategories.has(detectCategory(p))).length} nodes • WebGL
        </p>
      </div>

      {/* Hover tooltip */}
      <NodeTooltip paper={hoveredPaper} position={hoverPosition} />

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 text-gray-500 text-xs bg-gray-900/80 px-3 py-1.5 rounded-lg">
        Scroll to zoom • Drag to pan • Click node for details
      </div>
    </div>
  )
}

export default PaperGraph2D
