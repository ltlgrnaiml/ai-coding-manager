import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { Paper } from '../../hooks/useResearch'

interface TimelineGraphProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Extract year from paper metadata
function extractYear(paper: Paper): number {
  if (paper.year) return paper.year
  if (paper.published_date) {
    const match = paper.published_date.match(/\d{4}/)
    if (match) return parseInt(match[0])
  }
  return 2024
}

// Get importance score
function getImportance(paper: Paper): number {
  return paper.similarity || 0.5
}

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  'agentic-ai': '#ef4444',
  'rag': '#f97316',
  'context': '#eab308',
  'code-generation': '#22c55e',
  'multi-agent': '#14b8a6',
  'embedding': '#3b82f6',
  'transformer': '#8b5cf6',
  'prompt': '#ec4899',
  'default': '#6366f1'
}

const CATEGORY_LABELS: Record<string, string> = {
  'agentic-ai': 'Agentic AI',
  'rag': 'RAG',
  'context': 'Context',
  'code-generation': 'Code Gen',
  'multi-agent': 'Multi-Agent',
  'embedding': 'Embedding',
  'transformer': 'Transformer',
  'prompt': 'Prompt Eng',
  'default': 'Other'
}

// Detect category from paper
function detectCategory(paper: Paper): string {
  const text = ((paper.title || '') + ' ' + (paper.abstract || '')).toLowerCase()
  
  if (text.includes('agent') || text.includes('agentic')) return 'agentic-ai'
  if (text.includes('retrieval') || text.includes('rag')) return 'rag'
  if (text.includes('context') || text.includes('window') || text.includes('compress')) return 'context'
  if (text.includes('code') && text.includes('generat')) return 'code-generation'
  if (text.includes('multi-agent') || text.includes('collaborat')) return 'multi-agent'
  if (text.includes('embed') || text.includes('vector')) return 'embedding'
  if (text.includes('transformer') || text.includes('attention')) return 'transformer'
  if (text.includes('prompt') || text.includes('instruct')) return 'prompt'
  return 'default'
}

interface NodeData {
  id: string
  paper: Paper
  x: number
  y: number
  size: number
  color: string
  category: string
  year: number
  importance: number
  lane: number
}

interface CitationEdge {
  source: string
  target: string
  yearDiff: number
}

export default function TimelineGraphV2({ 
  papers, 
  onNodeClick,
  className = ''
}: TimelineGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 1000, height: 600 })
  const [hoveredNode, setHoveredNode] = useState<NodeData | null>(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [hiddenCategories, setHiddenCategories] = useState<Set<string>>(new Set())
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const isPanning = useRef(false)
  const isDraggingNode = useRef<string | null>(null)
  const lastMouse = useRef({ x: 0, y: 0 })

  // Calculate year range
  const yearRange = useMemo(() => {
    if (papers.length === 0) return { min: 2020, max: 2025 }
    const years = papers.map(extractYear)
    return { min: Math.min(...years), max: Math.max(...years) }
  }, [papers])

  // Calculate timeline layout with swim lanes per category
  const { nodes: initialNodes, categories, citationEdges } = useMemo(() => {
    if (papers.length === 0) return { nodes: [], categories: [], citationEdges: [] }

    const padding = { top: 80, right: 60, bottom: 80, left: 120 }
    const timelineWidth = dimensions.width - padding.left - padding.right
    const timelineHeight = dimensions.height - padding.top - padding.bottom

    // Group papers by category
    const papersByCategory: Map<string, Paper[]> = new Map()
    papers.forEach(paper => {
      const cat = detectCategory(paper)
      if (!papersByCategory.has(cat)) {
        papersByCategory.set(cat, [])
      }
      papersByCategory.get(cat)!.push(paper)
    })

    const categoryList = Array.from(papersByCategory.keys()).sort()
    const numLanes = categoryList.length || 1
    const laneHeight = timelineHeight / numLanes

    const nodes: NodeData[] = []

    categoryList.forEach((category, laneIndex) => {
      const papersInLane = papersByCategory.get(category) || []
      const laneY = padding.top + laneIndex * laneHeight + laneHeight / 2

      papersInLane.forEach(paper => {
        const year = extractYear(paper)
        const importance = getImportance(paper)
        const yearProgress = (year - yearRange.min) / (yearRange.max - yearRange.min || 1)
        
        // Add some vertical jitter within lane
        const jitterY = (Math.random() - 0.5) * laneHeight * 0.5

        nodes.push({
          id: paper.paper_id,
          paper,
          x: padding.left + yearProgress * timelineWidth,
          y: laneY + jitterY,
          size: 10 + importance * 20,
          color: CATEGORY_COLORS[category] || CATEGORY_COLORS.default,
          category,
          year,
          importance,
          lane: laneIndex
        })
      })
    })

    // Calculate citation edges (connect papers that might cite each other)
    const edges: CitationEdge[] = []
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i]
        const nodeB = nodes[j]
        const yearDiff = nodeB.year - nodeA.year

        // Only show forward-in-time connections (citations go from newer to older)
        if (yearDiff > 0 && yearDiff <= 3) {
          // Same category or similar importance = likely citation
          if (nodeA.category === nodeB.category || 
              Math.abs(nodeA.importance - nodeB.importance) < 0.2) {
            edges.push({
              source: nodeA.id,
              target: nodeB.id,
              yearDiff
            })
          }
        }
      }
    }

    // Limit edges
    const limitedEdges = edges.slice(0, Math.min(edges.length, nodes.length * 2))

    return { nodes, categories: categoryList, citationEdges: limitedEdges }
  }, [papers, dimensions, yearRange])

  // Merge with dragged positions
  const nodes = useMemo(() => {
    return initialNodes.map(node => {
      const customPos = nodePositions.get(node.id)
      if (customPos) {
        return { ...node, x: customPos.x, y: customPos.y }
      }
      return node
    })
  }, [initialNodes, nodePositions])

  // Filter visible nodes
  const visibleNodes = useMemo(() => {
    return nodes.filter(n => !hiddenCategories.has(n.category))
  }, [nodes, hiddenCategories])

  // Filter visible edges
  const visibleEdges = useMemo(() => {
    const visibleIds = new Set(visibleNodes.map(n => n.id))
    return citationEdges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target))
  }, [citationEdges, visibleNodes])

  // Resize observer
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        })
      }
    })

    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  // Toggle category visibility
  const toggleCategory = useCallback((category: string) => {
    setHiddenCategories(prev => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }, [])

  // Node drag handlers
  const handleNodeMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation()
    isDraggingNode.current = nodeId
    lastMouse.current = { x: e.clientX, y: e.clientY }
  }, [])

  // Pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0 && !isDraggingNode.current) {
      isPanning.current = true
      lastMouse.current = { x: e.clientX, y: e.clientY }
    }
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const dx = e.clientX - lastMouse.current.x
    const dy = e.clientY - lastMouse.current.y
    lastMouse.current = { x: e.clientX, y: e.clientY }

    if (isDraggingNode.current) {
      const nodeId = isDraggingNode.current
      const scaledDx = dx / transform.scale
      const scaledDy = dy / transform.scale

      setNodePositions(prev => {
        const newMap = new Map(prev)
        const currentNode = nodes.find(n => n.id === nodeId)
        if (currentNode) {
          const currentPos = prev.get(nodeId) || { x: currentNode.x, y: currentNode.y }
          newMap.set(nodeId, { x: currentPos.x + scaledDx, y: currentPos.y + scaledDy })
        }
        return newMap
      })
    } else if (isPanning.current) {
      setTransform(t => ({ ...t, x: t.x + dx, y: t.y + dy }))
    }
  }, [transform.scale, nodes])

  const handleMouseUp = useCallback(() => {
    isPanning.current = false
    isDraggingNode.current = null
  }, [])

  // Zoom handler
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const scaleDelta = e.deltaY > 0 ? 0.9 : 1.1
    const newScale = Math.max(0.3, Math.min(3, transform.scale * scaleDelta))

    const rect = containerRef.current?.getBoundingClientRect()
    if (rect) {
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      const scaleChange = newScale / transform.scale

      setTransform(t => ({
        scale: newScale,
        x: mouseX - (mouseX - t.x) * scaleChange,
        y: mouseY - (mouseY - t.y) * scaleChange
      }))
    }
  }, [transform.scale])

  // Reset view
  const resetView = useCallback(() => {
    setTransform({ x: 0, y: 0, scale: 1 })
    setNodePositions(new Map())
    setHiddenCategories(new Set())
  }, [])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  const nodeMap = new Map(visibleNodes.map(n => [n.id, n]))
  const padding = { top: 80, right: 60, bottom: 80, left: 120 }

  return (
    <div
      ref={containerRef}
      className={`h-full w-full relative bg-gradient-to-br from-slate-50 to-amber-50 overflow-hidden ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      style={{ cursor: isPanning.current || isDraggingNode.current ? 'grabbing' : 'grab' }}
    >
      <svg
        width={dimensions.width}
        height={dimensions.height}
        style={{
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
          transformOrigin: '0 0'
        }}
      >
        {/* Background swim lane regions */}
        {categories.map((category, i) => {
          const laneHeight = (dimensions.height - padding.top - padding.bottom) / categories.length
          const laneY = padding.top + i * laneHeight
          const isHidden = hiddenCategories.has(category)
          
          return (
            <g key={category} opacity={isHidden ? 0.3 : 1}>
              {/* Lane background */}
              <rect
                x={padding.left - 10}
                y={laneY}
                width={dimensions.width - padding.left - padding.right + 20}
                height={laneHeight}
                fill={i % 2 === 0 ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.02)'}
                rx={4}
              />
              {/* Lane label */}
              <text
                x={padding.left - 20}
                y={laneY + laneHeight / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fill={CATEGORY_COLORS[category]}
                fontSize="11"
                fontWeight="600"
              >
                {CATEGORY_LABELS[category] || category}
              </text>
            </g>
          )
        })}

        {/* Timeline axis */}
        <line
          x1={padding.left}
          y1={dimensions.height - padding.bottom + 20}
          x2={dimensions.width - padding.right}
          y2={dimensions.height - padding.bottom + 20}
          stroke="#374151"
          strokeWidth={2}
        />

        {/* Year tick marks */}
        {Array.from({ length: yearRange.max - yearRange.min + 1 }, (_, i) => yearRange.min + i).map(year => {
          const x = padding.left + ((year - yearRange.min) / (yearRange.max - yearRange.min || 1)) * (dimensions.width - padding.left - padding.right)
          return (
            <g key={year}>
              <line
                x1={x}
                y1={dimensions.height - padding.bottom + 15}
                x2={x}
                y2={dimensions.height - padding.bottom + 25}
                stroke="#374151"
                strokeWidth={2}
              />
              <line
                x1={x}
                y1={padding.top}
                x2={x}
                y2={dimensions.height - padding.bottom + 15}
                stroke="#e5e7eb"
                strokeWidth={1}
                strokeDasharray="4,4"
              />
              <text
                x={x}
                y={dimensions.height - padding.bottom + 40}
                textAnchor="middle"
                fill="#374151"
                fontSize="12"
                fontWeight="600"
              >
                {year}
              </text>
            </g>
          )
        })}

        {/* Citation arrows */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
          </marker>
        </defs>
        <g opacity={0.4}>
          {visibleEdges.map((edge, i) => {
            const source = nodeMap.get(edge.source)
            const target = nodeMap.get(edge.target)
            if (!source || !target) return null

            // Curved arrow from newer paper pointing to older paper (citation)
            const midX = (source.x + target.x) / 2
            const midY = Math.min(source.y, target.y) - 30

            return (
              <path
                key={i}
                d={`M ${target.x} ${target.y} Q ${midX} ${midY}, ${source.x} ${source.y}`}
                stroke="#94a3b8"
                strokeWidth={1.5}
                fill="none"
                markerEnd="url(#arrowhead)"
                strokeDasharray={edge.yearDiff > 2 ? "4,2" : undefined}
              />
            )
          })}
        </g>

        {/* Nodes */}
        {visibleNodes.map(node => (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            style={{ cursor: isDraggingNode.current === node.id ? 'grabbing' : 'grab' }}
            onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
            onClick={(e) => {
              if (!nodePositions.has(node.id) || e.detail === 2) {
                onNodeClick?.(node.id)
              }
            }}
            onMouseEnter={() => setHoveredNode(node)}
            onMouseLeave={() => setHoveredNode(null)}
          >
            {/* Node circle */}
            <circle
              r={node.size}
              fill={hoveredNode?.id === node.id ? '#1e40af' : node.color}
              stroke="#fff"
              strokeWidth={2}
              style={{
                transition: 'fill 0.15s ease',
                filter: hoveredNode?.id === node.id
                  ? 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))'
                  : 'drop-shadow(0 2px 3px rgba(0,0,0,0.15))'
              }}
            />

            {/* Label */}
            <rect
              x={-50}
              y={node.size + 4}
              width={100}
              height={14}
              fill="rgba(255,255,255,0.9)"
              rx={3}
              style={{ pointerEvents: 'none' }}
            />
            <text
              y={node.size + 14}
              textAnchor="middle"
              fill="#374151"
              fontSize="9"
              fontWeight="500"
              style={{ pointerEvents: 'none' }}
            >
              {node.paper.title?.slice(0, 16)}{(node.paper.title?.length || 0) > 16 ? '...' : ''}
            </text>
          </g>
        ))}

        {/* Axis label */}
        <text
          x={dimensions.width / 2}
          y={dimensions.height - 15}
          textAnchor="middle"
          fill="#374151"
          fontSize="13"
          fontWeight="600"
        >
          Publication Timeline →
        </text>
      </svg>

      {/* Legend with filtering */}
      <div className="absolute top-4 left-4 bg-white/95 border border-gray-200 rounded-xl p-4 shadow-lg backdrop-blur-sm max-w-xs">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Categories (click to filter)</h3>
        <div className="space-y-1.5">
          {categories.map(cat => {
            const isHidden = hiddenCategories.has(cat)
            const count = nodes.filter(n => n.category === cat).length
            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                className={`flex items-center gap-2 w-full px-2 py-1 rounded text-left text-xs transition-all ${
                  isHidden ? 'opacity-40 line-through' : 'hover:bg-gray-100'
                }`}
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: CATEGORY_COLORS[cat] || CATEGORY_COLORS.default }}
                />
                <span className="text-gray-700 flex-1">{CATEGORY_LABELS[cat] || cat}</span>
                <span className="text-gray-400">{count}</span>
              </button>
            )
          })}
        </div>

        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
          <p>← <strong>Arrows</strong> = citation flow</p>
          <p className="mt-1"><strong>Lanes</strong> = category groups</p>
        </div>

        <button
          onClick={resetView}
          className="mt-3 text-xs text-blue-600 hover:text-blue-800"
        >
          Reset view & filters
        </button>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white/95 border border-gray-200 rounded-lg px-4 py-2 shadow-sm backdrop-blur-sm">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-amber-600">{visibleNodes.length}</span>/{papers.length} papers •
          <span className="text-green-600 ml-1">Timeline</span>
        </p>
      </div>

      {/* Hover tooltip */}
      {hoveredNode && (
        <div
          className="absolute z-50 bg-white border border-gray-200 rounded-xl shadow-xl p-4 pointer-events-none max-w-sm"
          style={{
            left: Math.min(hoveredNode.x * transform.scale + transform.x + 20, dimensions.width - 320),
            top: Math.max(hoveredNode.y * transform.scale + transform.y - 60, 20)
          }}
        >
          <h4 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
            {hoveredNode.paper.title || 'Untitled'}
          </h4>
          <div className="flex items-center gap-2 text-xs mb-2 flex-wrap">
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
              {hoveredNode.year}
            </span>
            <span
              className="px-2 py-0.5 rounded text-white"
              style={{ backgroundColor: hoveredNode.color }}
            >
              {CATEGORY_LABELS[hoveredNode.category] || hoveredNode.category}
            </span>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
              {(hoveredNode.importance * 100).toFixed(0)}% match
            </span>
          </div>
          {hoveredNode.paper.abstract && (
            <p className="text-xs text-gray-500 line-clamp-3">{hoveredNode.paper.abstract}</p>
          )}
          <p className="text-xs text-blue-500 mt-2">Click to view details</p>
        </div>
      )}
    </div>
  )
}
