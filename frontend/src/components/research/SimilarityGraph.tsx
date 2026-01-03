import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import Graph from 'graphology'
import { SigmaContainer, useLoadGraph, useSigma, useRegisterEvents } from '@react-sigma/core'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import '@react-sigma/core/lib/style.css'
import { Paper } from '../../hooks/useResearch'

interface SimilarityGraphProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Professional color palette for year gradient (older = lighter, newer = darker)
function getYearColor(year: number, minYear: number, maxYear: number): string {
  const range = maxYear - minYear || 1
  const normalized = (year - minYear) / range
  // Light blue to dark blue gradient
  const r = Math.round(200 - normalized * 150)
  const g = Math.round(220 - normalized * 140)
  const b = Math.round(255 - normalized * 80)
  return `rgb(${r}, ${g}, ${b})`
}

// Extract year from paper metadata
function extractYear(paper: Paper): number {
  if (paper.year) return paper.year
  if (paper.published_date) {
    const match = paper.published_date.match(/\d{4}/)
    if (match) return parseInt(match[0])
  }
  // Try to extract from title or other fields
  const text = paper.title || ''
  const yearMatch = text.match(/20[0-2]\d/)
  if (yearMatch) return parseInt(yearMatch[0])
  return 2024 // Default to recent
}

// Calculate importance score (use similarity or default)
function getImportance(paper: Paper): number {
  return paper.similarity || paper.citation_count || 0.5
}

// Tooltip component
function NodeTooltip({ 
  paper, 
  position 
}: { 
  paper: Paper | null
  position: { x: number; y: number } 
}) {
  if (!paper) return null
  
  const year = extractYear(paper)
  
  return (
    <div 
      className="absolute z-50 bg-white border border-gray-200 rounded-xl shadow-xl p-4 max-w-sm pointer-events-none"
      style={{ 
        left: position.x + 15, 
        top: position.y + 15,
        transform: 'translateY(-50%)'
      }}
    >
      <h4 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
        {paper.title || 'Untitled'}
      </h4>
      {paper.authors && (
        <p className="text-xs text-gray-600 mb-2">{paper.authors}</p>
      )}
      <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
        <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{year}</span>
        {paper.similarity && (
          <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">
            {(paper.similarity * 100).toFixed(0)}% match
          </span>
        )}
      </div>
      {paper.abstract && (
        <p className="text-xs text-gray-500 line-clamp-3">{paper.abstract}</p>
      )}
      <p className="text-xs text-blue-600 mt-2 font-medium">Click to view details</p>
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
  const registerEvents = useRegisterEvents()

  useEffect(() => {
    registerEvents({
      clickNode: ({ node }) => onNodeClick?.(node),
      enterNode: ({ node, event }) => {
        const paper = papers.find(p => p.paper_id === node)
        if (paper) {
          onHover(paper, { x: event.x, y: event.y })
        }
      },
      leaveNode: () => {
        onHover(null, { x: 0, y: 0 })
      }
    })
  }, [registerEvents, papers, onNodeClick, onHover])

  return null
}

// Graph data loader with similarity-based layout
function LoadGraphData({ 
  papers,
  yearRange
}: { 
  papers: Paper[]
  yearRange: { min: number; max: number }
}) {
  const loadGraph = useLoadGraph()
  const sigma = useSigma()
  const initializedRef = useRef(false)
  const paperIdsRef = useRef<string>('')

  useEffect(() => {
    // Only re-initialize if papers actually changed
    const paperIds = papers.map(p => p.paper_id).sort().join(',')
    if (initializedRef.current && paperIds === paperIdsRef.current) {
      return
    }
    paperIdsRef.current = paperIds

    const graph = new Graph()
    
    if (papers.length === 0) return

    // Add nodes with year-based colors and importance-based sizes
    papers.forEach((paper, index) => {
      const year = extractYear(paper)
      const importance = getImportance(paper)
      const color = getYearColor(year, yearRange.min, yearRange.max)
      
      // Initial circular layout
      const angle = (2 * Math.PI * index) / papers.length
      const radius = 200
      
      graph.addNode(paper.paper_id, {
        label: paper.title?.slice(0, 40) + (paper.title && paper.title.length > 40 ? '...' : '') || 'Untitled',
        x: Math.cos(angle) * radius + (Math.random() - 0.5) * 50,
        y: Math.sin(angle) * radius + (Math.random() - 0.5) * 50,
        size: 8 + importance * 20, // Size by importance/similarity
        color: color,
        year: year,
        borderColor: '#ffffff'
      })
    })

    // Create edges based on similarity (using cosine similarity from embeddings)
    // Papers with higher similarity get thicker, more visible edges
    papers.forEach((paper, i) => {
      papers.forEach((other, j) => {
        if (i >= j) return // Avoid duplicates
        
        // Calculate pseudo-similarity based on year proximity and random factor
        // In production, this would use actual embedding similarity
        const yearDiff = Math.abs(extractYear(paper) - extractYear(other))
        const yearSimilarity = Math.max(0, 1 - yearDiff / 10)
        const baseSimilarity = (paper.similarity || 0.5) * (other.similarity || 0.5)
        const similarity = yearSimilarity * 0.3 + baseSimilarity * 0.7
        
        // Only show edges above threshold
        if (similarity > 0.3) {
          graph.addEdge(paper.paper_id, other.paper_id, {
            size: similarity * 3, // Edge thickness by similarity
            color: `rgba(100, 120, 180, ${similarity * 0.6})`, // Opacity by similarity
            type: 'line'
          })
        }
      })
    })

    // Apply ForceAtlas2 layout - clusters similar papers together
    if (graph.order > 0) {
      forceAtlas2.assign(graph, {
        iterations: 150,
        settings: {
          gravity: 0.5,
          scalingRatio: 20,
          strongGravityMode: true,
          barnesHutOptimize: graph.order > 30,
          slowDown: 2
        }
      })
    }

    loadGraph(graph)
    
    // Center and zoom to fit only on first load
    if (!initializedRef.current) {
      initializedRef.current = true
      setTimeout(() => {
        sigma.getCamera().animatedReset()
      }, 100)
    }
  }, [loadGraph, papers, yearRange, sigma])

  return null
}

// Main component
export default function SimilarityGraph({ 
  papers, 
  onNodeClick,
  className = ''
}: SimilarityGraphProps) {
  const [hoveredPaper, setHoveredPaper] = useState<Paper | null>(null)
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 })

  // Calculate year range for color gradient
  const yearRange = useMemo(() => {
    if (papers.length === 0) return { min: 2020, max: 2025 }
    const years = papers.map(extractYear)
    return {
      min: Math.min(...years),
      max: Math.max(...years)
    }
  }, [papers])

  const handleHover = useCallback((paper: Paper | null, pos: { x: number; y: number }) => {
    setHoveredPaper(paper)
    setHoverPosition(pos)
  }, [])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  return (
    <div className={`h-full w-full relative ${className}`}>
      <SigmaContainer
        style={{ height: '100%', width: '100%', background: '#fafbfc' }}
        settings={{
          renderLabels: true,
          labelSize: 10,
          labelWeight: '500',
          labelColor: { color: '#374151' },
          labelFont: 'Inter, system-ui, sans-serif',
          defaultNodeColor: '#6366f1',
          defaultEdgeColor: '#94a3b8',
          defaultEdgeType: 'line',
          minCameraRatio: 0.1,
          maxCameraRatio: 10,
          labelRenderedSizeThreshold: 6,
          labelDensity: 0.15,
          nodeProgramClasses: {},
          nodeReducer: (node, data) => ({
            ...data,
            size: data.highlighted ? data.size * 1.3 : data.size,
            color: data.highlighted ? '#1e40af' : data.color,
            zIndex: data.highlighted ? 1 : 0
          }),
          edgeReducer: (edge, data) => data
        }}
      >
        <LoadGraphData papers={papers} yearRange={yearRange} />
        <GraphEvents papers={papers} onNodeClick={onNodeClick} onHover={handleHover} />
      </SigmaContainer>

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white border border-gray-200 rounded-xl p-4 shadow-lg">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Year Published</h3>
        <div className="flex items-center gap-2">
          <div className="w-20 h-3 rounded-full" style={{
            background: 'linear-gradient(to right, rgb(200, 220, 255), rgb(50, 80, 175))'
          }} />
          <div className="flex justify-between w-20 text-xs text-gray-500">
            <span>{yearRange.min}</span>
            <span>{yearRange.max}</span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-200 mr-1" /> Older papers
          </p>
          <p className="text-xs text-gray-500 mt-1">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-700 mr-1" /> Newer papers
          </p>
          <p className="text-xs text-gray-500 mt-1">
            <span className="font-medium">Node size</span> = relevance score
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-blue-600">{papers.length}</span> papers • 
          <span className="text-green-600 ml-1">WebGL</span>
        </p>
      </div>

      {/* Hover tooltip */}
      <NodeTooltip paper={hoveredPaper} position={hoverPosition} />

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 text-gray-500 text-xs bg-white/90 border border-gray-200 px-3 py-1.5 rounded-lg">
        Scroll to zoom • Drag to pan • Click node for details
      </div>
    </div>
  )
}
