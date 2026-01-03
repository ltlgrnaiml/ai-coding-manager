import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { Paper } from '../../hooks/useResearch'

interface SimilarityGraphProps {
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
  const text = paper.title || ''
  const yearMatch = text.match(/20[0-2]\d/)
  if (yearMatch) return parseInt(yearMatch[0])
  return 2024
}

// Calculate importance score
function getImportance(paper: Paper): number {
  return paper.similarity || 0.5
}

// Color by year (older = lighter blue, newer = darker blue)
function getYearColor(year: number, minYear: number, maxYear: number): string {
  const range = maxYear - minYear || 1
  const normalized = (year - minYear) / range
  const r = Math.round(100 + (1 - normalized) * 100)
  const g = Math.round(130 + (1 - normalized) * 90)
  const b = Math.round(220 + (1 - normalized) * 35)
  return `rgb(${r}, ${g}, ${b})`
}

interface NodeData {
  id: string
  paper: Paper
  x: number
  y: number
  size: number
  color: string
  year: number
  importance: number
}

interface EdgeData {
  source: string
  target: string
  weight: number
}

// Simple force-directed layout (runs once, not continuously)
function calculateLayout(papers: Paper[], width: number, height: number): NodeData[] {
  const centerX = width / 2
  const centerY = height / 2
  
  const years = papers.map(extractYear)
  const minYear = Math.min(...years)
  const maxYear = Math.max(...years)

  // Initial positions in a circle
  const nodes: NodeData[] = papers.map((paper, i) => {
    const angle = (2 * Math.PI * i) / papers.length
    const radius = Math.min(width, height) * 0.35
    const importance = getImportance(paper)
    const year = extractYear(paper)
    
    return {
      id: paper.paper_id,
      paper,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
      size: 12 + importance * 25,
      color: getYearColor(year, minYear, maxYear),
      year,
      importance
    }
  })

  // Simple force simulation (run fixed iterations)
  const iterations = 100
  const repulsion = 2000
  const attraction = 0.01
  const centerPull = 0.005

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between all nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x
        const dy = nodes[j].y - nodes[i].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = nodes[i].size + nodes[j].size + 20
        
        if (dist < minDist * 3) {
          const force = repulsion / (dist * dist)
          const fx = (dx / dist) * force
          const fy = (dy / dist) * force
          
          nodes[i].x -= fx
          nodes[i].y -= fy
          nodes[j].x += fx
          nodes[j].y += fy
        }
      }
    }

    // Attraction to center
    for (const node of nodes) {
      node.x += (centerX - node.x) * centerPull
      node.y += (centerY - node.y) * centerPull
    }

    // Keep in bounds
    const padding = 80
    for (const node of nodes) {
      node.x = Math.max(padding, Math.min(width - padding, node.x))
      node.y = Math.max(padding, Math.min(height - padding, node.y))
    }
  }

  return nodes
}

// Calculate edges based on similarity
function calculateEdges(nodes: NodeData[]): EdgeData[] {
  const edges: EdgeData[] = []
  
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const yearDiff = Math.abs(nodes[i].year - nodes[j].year)
      const yearSim = Math.max(0, 1 - yearDiff / 5)
      const importanceSim = 1 - Math.abs(nodes[i].importance - nodes[j].importance)
      const weight = yearSim * 0.5 + importanceSim * 0.5
      
      // Only show strong connections
      if (weight > 0.6) {
        edges.push({
          source: nodes[i].id,
          target: nodes[j].id,
          weight
        })
      }
    }
  }
  
  // Limit edges to prevent clutter
  return edges.sort((a, b) => b.weight - a.weight).slice(0, Math.min(edges.length, nodes.length * 2))
}

export default function SimilarityGraphV2({ 
  papers, 
  onNodeClick,
  className = ''
}: SimilarityGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [hoveredNode, setHoveredNode] = useState<NodeData | null>(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const isPanning = useRef(false)
  const isDraggingNode = useRef<string | null>(null)
  const lastMouse = useRef({ x: 0, y: 0 })

  // Calculate year range for legend
  const yearRange = useMemo(() => {
    if (papers.length === 0) return { min: 2020, max: 2025 }
    const years = papers.map(extractYear)
    return { min: Math.min(...years), max: Math.max(...years) }
  }, [papers])

  // Calculate initial layout when papers change
  const initialNodes = useMemo(() => {
    if (papers.length === 0) return []
    return calculateLayout(papers, dimensions.width, dimensions.height)
  }, [papers, dimensions.width, dimensions.height])

  // Merge initial positions with dragged positions
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

  // Pan handlers (for background)
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
      // Move the node
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
      // Pan the view
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
    
    // Zoom toward mouse position
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
      className={`h-full w-full relative bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden ${className}`}
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
        {/* Edges */}
        <g opacity={0.3}>
          {edges.map((edge, i) => {
            const source = nodeMap.get(edge.source)
            const target = nodeMap.get(edge.target)
            if (!source || !target) return null
            
            return (
              <line
                key={i}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke="#6366f1"
                strokeWidth={edge.weight * 2}
                strokeOpacity={edge.weight * 0.5}
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
              // Only trigger click if we weren't dragging
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
                filter: hoveredNode?.id === node.id ? 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))' : 'drop-shadow(0 2px 3px rgba(0,0,0,0.1))'
              }}
            />
            
            {/* Label - always show but with background for readability */}
            <rect
              x={-60}
              y={node.size + 4}
              width={120}
              height={18}
              fill="rgba(255,255,255,0.85)"
              rx={4}
              style={{ pointerEvents: 'none' }}
            />
            <text
              y={node.size + 16}
              textAnchor="middle"
              fill="#1f2937"
              fontSize="10"
              fontWeight="500"
              style={{ pointerEvents: 'none' }}
            >
              {node.paper.title?.slice(0, 20)}{(node.paper.title?.length || 0) > 20 ? '...' : ''}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="absolute top-4 left-4 bg-white/95 border border-gray-200 rounded-xl p-4 shadow-lg backdrop-blur-sm">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Year Published</h3>
        <div className="flex items-center gap-2">
          <div className="w-20 h-3 rounded-full" style={{
            background: 'linear-gradient(to right, rgb(200, 220, 255), rgb(100, 130, 220))'
          }} />
          <div className="flex justify-between w-20 text-xs text-gray-500">
            <span>{yearRange.min}</span>
            <span>{yearRange.max}</span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
          <p><strong>Node size</strong> = relevance score</p>
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
          <span className="font-semibold text-blue-600">{papers.length}</span> papers • 
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
          <div className="flex items-center gap-2 text-xs mb-2">
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
              {hoveredNode.year}
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
