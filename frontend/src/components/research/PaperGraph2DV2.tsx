import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { Paper } from '../../hooks/useResearch'

interface PaperGraph2DProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Category colors - professional palette
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

// Detect category from paper content
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

// Extract year from paper
function extractYear(paper: Paper): number {
  if (paper.year) return paper.year
  if (paper.published_date) {
    const match = paper.published_date.match(/\d{4}/)
    if (match) return parseInt(match[0])
  }
  return 2024
}

// Get importance/relevance score
function getImportance(paper: Paper): number {
  return paper.similarity || 0.5
}

// Node shape paths (centered at 0,0)
const SHAPES = {
  circle: (size: number) => {
    const r = size
    return `M ${r},0 A ${r},${r} 0 1,1 ${-r},0 A ${r},${r} 0 1,1 ${r},0`
  },
  hexagon: (size: number) => {
    const r = size
    const points = []
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 6
      points.push(`${r * Math.cos(angle)},${r * Math.sin(angle)}`)
    }
    return `M ${points.join(' L ')} Z`
  },
  diamond: (size: number) => {
    const r = size * 1.2
    return `M 0,${-r} L ${r},0 L 0,${r} L ${-r},0 Z`
  },
  square: (size: number) => {
    const r = size * 0.85
    return `M ${-r},${-r} L ${r},${-r} L ${r},${r} L ${-r},${r} Z`
  },
  triangle: (size: number) => {
    const r = size * 1.1
    return `M 0,${-r} L ${r * 0.866},${r * 0.5} L ${-r * 0.866},${r * 0.5} Z`
  }
}

type ShapeType = keyof typeof SHAPES

// Determine shape based on paper attributes
function getNodeShape(paper: Paper, importance: number): ShapeType {
  const year = extractYear(paper)
  const currentYear = new Date().getFullYear()
  
  // Recent papers (last 2 years) = diamond
  if (year >= currentYear - 1) return 'diamond'
  // High importance = hexagon
  if (importance > 0.7) return 'hexagon'
  // Survey/review papers = square
  const title = (paper.title || '').toLowerCase()
  if (title.includes('survey') || title.includes('review') || title.includes('comprehensive')) return 'square'
  // Default = circle
  return 'circle'
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
  shape: ShapeType
  column: number
}

interface EdgeData {
  source: string
  target: string
  weight: number
}

// Calculate column-based layout (papers arranged by year, spread vertically)
function calculateColumnLayout(papers: Paper[], width: number, height: number): NodeData[] {
  if (papers.length === 0) return []

  const padding = 100
  const availableWidth = width - padding * 2
  const availableHeight = height - padding * 2

  // Group papers by year
  const papersByYear: Map<number, Paper[]> = new Map()
  papers.forEach(paper => {
    const year = extractYear(paper)
    if (!papersByYear.has(year)) {
      papersByYear.set(year, [])
    }
    papersByYear.get(year)!.push(paper)
  })

  // Sort years
  const years = Array.from(papersByYear.keys()).sort((a, b) => a - b)
  const numColumns = years.length || 1
  const columnWidth = availableWidth / numColumns

  const nodes: NodeData[] = []

  years.forEach((year, colIndex) => {
    const papersInYear = papersByYear.get(year) || []
    const numInColumn = papersInYear.length
    const rowHeight = availableHeight / (numInColumn + 1)

    // Sort papers in column by importance
    papersInYear.sort((a, b) => getImportance(b) - getImportance(a))

    papersInYear.forEach((paper, rowIndex) => {
      const category = detectCategory(paper)
      const importance = getImportance(paper)
      const shape = getNodeShape(paper, importance)

      // Add some horizontal jitter within column to avoid perfect grid
      const jitterX = (Math.random() - 0.5) * columnWidth * 0.3

      nodes.push({
        id: paper.paper_id,
        paper,
        x: padding + colIndex * columnWidth + columnWidth / 2 + jitterX,
        y: padding + (rowIndex + 1) * rowHeight,
        size: 14 + importance * 20,
        color: CATEGORY_COLORS[category] || CATEGORY_COLORS.default,
        category,
        year,
        importance,
        shape,
        column: colIndex
      })
    })
  })

  return nodes
}

// Calculate edges (connect papers with similar categories or topics)
function calculateEdges(nodes: NodeData[]): EdgeData[] {
  const edges: EdgeData[] = []

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const nodeA = nodes[i]
      const nodeB = nodes[j]

      // Same category = strong connection
      let weight = nodeA.category === nodeB.category ? 0.8 : 0

      // Adjacent years boost
      if (Math.abs(nodeA.year - nodeB.year) <= 1) {
        weight += 0.2
      }

      // Similar importance boost
      const impDiff = Math.abs(nodeA.importance - nodeB.importance)
      if (impDiff < 0.2) {
        weight += 0.1
      }

      // Only show strong connections
      if (weight >= 0.7) {
        edges.push({
          source: nodeA.id,
          target: nodeB.id,
          weight
        })
      }
    }
  }

  // Limit edges to prevent clutter
  return edges.sort((a, b) => b.weight - a.weight).slice(0, Math.min(edges.length, nodes.length * 1.5))
}

export default function PaperGraph2DV2({
  papers,
  onNodeClick,
  className = ''
}: PaperGraph2DProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [hoveredNode, setHoveredNode] = useState<NodeData | null>(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const isPanning = useRef(false)
  const isDraggingNode = useRef<string | null>(null)
  const lastMouse = useRef({ x: 0, y: 0 })

  // Calculate layout
  const initialNodes = useMemo(() => {
    if (papers.length === 0) return []
    return calculateColumnLayout(papers, dimensions.width, dimensions.height)
  }, [papers, dimensions.width, dimensions.height])

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

  const edges = useMemo(() => calculateEdges(nodes), [nodes])

  // Get unique categories for legend
  const categories = useMemo(() => {
    const cats = new Set(nodes.map(n => n.category))
    return Array.from(cats)
  }, [nodes])

  // Get year range
  const yearRange = useMemo(() => {
    if (nodes.length === 0) return { min: 2020, max: 2025 }
    const years = nodes.map(n => n.year)
    return { min: Math.min(...years), max: Math.max(...years) }
  }, [nodes])

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
  }, [])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  return (
    <div
      ref={containerRef}
      className={`h-full w-full relative bg-gradient-to-br from-gray-50 to-indigo-50 overflow-hidden ${className}`}
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
        {/* Year column headers */}
        {Array.from(new Set(nodes.map(n => n.year))).sort().map((year, i, arr) => {
          const columnWidth = (dimensions.width - 200) / arr.length
          const x = 100 + i * columnWidth + columnWidth / 2
          return (
            <g key={year}>
              <text
                x={x}
                y={40}
                textAnchor="middle"
                fill="#6b7280"
                fontSize="14"
                fontWeight="600"
              >
                {year}
              </text>
              <line
                x1={x}
                y1={55}
                x2={x}
                y2={dimensions.height - 50}
                stroke="#e5e7eb"
                strokeWidth={1}
                strokeDasharray="4,4"
              />
            </g>
          )
        })}

        {/* Edges - curved horizontal connections */}
        <g opacity={0.4}>
          {edges.map((edge, i) => {
            const source = nodeMap.get(edge.source)
            const target = nodeMap.get(edge.target)
            if (!source || !target) return null

            // Create curved path for horizontal flow
            const midX = (source.x + target.x) / 2
            const curveOffset = Math.abs(source.y - target.y) * 0.3

            return (
              <path
                key={i}
                d={`M ${source.x} ${source.y} C ${midX} ${source.y - curveOffset}, ${midX} ${target.y - curveOffset}, ${target.x} ${target.y}`}
                stroke={source.color}
                strokeWidth={edge.weight * 2}
                strokeOpacity={edge.weight * 0.6}
                fill="none"
              />
            )
          })}
        </g>

        {/* Nodes */}
        {nodes.map(node => (
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
            {/* Node shape */}
            <path
              d={SHAPES[node.shape](node.size)}
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

            {/* Label with background */}
            <rect
              x={-55}
              y={node.size + 4}
              width={110}
              height={16}
              fill="rgba(255,255,255,0.9)"
              rx={3}
              style={{ pointerEvents: 'none' }}
            />
            <text
              y={node.size + 15}
              textAnchor="middle"
              fill="#374151"
              fontSize="9"
              fontWeight="500"
              style={{ pointerEvents: 'none' }}
            >
              {node.paper.title?.slice(0, 18)}{(node.paper.title?.length || 0) > 18 ? '...' : ''}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/95 border border-gray-200 rounded-xl p-4 shadow-lg backdrop-blur-sm max-w-xs">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Categories</h3>
        <div className="grid grid-cols-2 gap-1.5 text-xs">
          {categories.slice(0, 8).map(cat => (
            <div key={cat} className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: CATEGORY_COLORS[cat] || CATEGORY_COLORS.default }}
              />
              <span className="text-gray-600 truncate">{cat.replace(/-/g, ' ')}</span>
            </div>
          ))}
        </div>

        <div className="mt-3 pt-3 border-t border-gray-100">
          <h4 className="text-xs font-semibold text-gray-600 mb-2">Shapes</h4>
          <div className="grid grid-cols-2 gap-1 text-xs text-gray-500">
            <span>◇ Recent</span>
            <span>⬡ High match</span>
            <span>□ Survey</span>
            <span>○ Standard</span>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
          <p><strong>Columns</strong> = Years ({yearRange.min}–{yearRange.max})</p>
          <p className="mt-1"><strong>Drag</strong> to pan • <strong>Scroll</strong> to zoom</p>
        </div>

        <button
          onClick={resetView}
          className="mt-3 text-xs text-blue-600 hover:text-blue-800"
        >
          Reset view
        </button>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white/95 border border-gray-200 rounded-lg px-4 py-2 shadow-sm backdrop-blur-sm">
        <p className="text-sm text-gray-600">
          <span className="font-semibold text-indigo-600">{papers.length}</span> papers •
          <span className="text-green-600 ml-1">SVG</span>
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
              {hoveredNode.category.replace(/-/g, ' ')}
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
