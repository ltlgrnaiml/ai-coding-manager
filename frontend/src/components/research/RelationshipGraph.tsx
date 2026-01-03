import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { Paper } from '../../hooks/useResearch'

interface RelationshipGraphProps {
  papers: Paper[]
  onNodeClick?: (paperId: string) => void
  className?: string
}

// Relationship dimensions
type RelationDimension = 'topic' | 'author' | 'year' | 'citations' | 'source'

const DIMENSION_INFO: Record<RelationDimension, { label: string; description: string }> = {
  topic: { label: 'Topic', description: 'Connect papers with similar topics' },
  author: { label: 'Author', description: 'Connect papers by shared authors' },
  year: { label: 'Year', description: 'Connect papers from same year' },
  citations: { label: 'Citations', description: 'Connect by citation similarity' },
  source: { label: 'Source', description: 'Connect papers from same source/journal' }
}

// Extract author names from paper
function extractAuthors(paper: Paper): string[] {
  if (!paper.authors) return []
  if (Array.isArray(paper.authors)) return paper.authors.map(a => typeof a === 'string' ? a : a.name || '')
  if (typeof paper.authors === 'string') {
    return paper.authors.split(/[,;&]/).map(a => a.trim().toLowerCase())
  }
  return []
}

// Extract source/journal from paper
function extractSource(paper: Paper): string {
  // Use arxiv_id if available
  if (paper.arxiv_id) return 'arxiv'
  // Try to detect from title or abstract
  const text = ((paper.title || '') + ' ' + (paper.abstract || '')).toLowerCase()
  if (text.includes('neurips') || text.includes('nips')) return 'neurips'
  if (text.includes('icml')) return 'icml'
  if (text.includes('iclr')) return 'iclr'
  if (text.includes('acl ') || text.includes('emnlp')) return 'acl'
  if (text.includes('cvpr') || text.includes('iccv')) return 'cvpr'
  return 'preprint'
}

// Extract year
function extractYear(paper: Paper): number {
  if (paper.year) return paper.year
  if (paper.published_date) {
    const match = paper.published_date.match(/\d{4}/)
    if (match) return parseInt(match[0])
  }
  return 2024
}

// Detect topic/category
function detectTopic(paper: Paper): string {
  const text = ((paper.title || '') + ' ' + (paper.abstract || '')).toLowerCase()
  
  if (text.includes('agent') || text.includes('agentic')) return 'agentic-ai'
  if (text.includes('retrieval') || text.includes('rag')) return 'rag'
  if (text.includes('context') || text.includes('window') || text.includes('compress')) return 'context'
  if (text.includes('code') && text.includes('generat')) return 'code-generation'
  if (text.includes('multi-agent') || text.includes('collaborat')) return 'multi-agent'
  if (text.includes('embed') || text.includes('vector')) return 'embedding'
  if (text.includes('transformer') || text.includes('attention')) return 'transformer'
  if (text.includes('prompt') || text.includes('instruct')) return 'prompt'
  return 'other'
}

// Get citation count (use similarity as proxy if not available)
function getCitationTier(paper: Paper): number {
  const citations = paper.citation_count || Math.round((paper.similarity || 0.5) * 100)
  if (citations > 100) return 3 // high
  if (citations > 30) return 2 // medium
  if (citations > 10) return 1 // low
  return 0 // minimal
}

// Topic colors
const TOPIC_COLORS: Record<string, string> = {
  'agentic-ai': '#ef4444',
  'rag': '#f97316',
  'context': '#eab308',
  'code-generation': '#22c55e',
  'multi-agent': '#14b8a6',
  'embedding': '#3b82f6',
  'transformer': '#8b5cf6',
  'prompt': '#ec4899',
  'other': '#6366f1'
}

const TOPIC_LABELS: Record<string, string> = {
  'agentic-ai': 'Agentic AI',
  'rag': 'RAG',
  'context': 'Context',
  'code-generation': 'Code Gen',
  'multi-agent': 'Multi-Agent',
  'embedding': 'Embedding',
  'transformer': 'Transformer',
  'prompt': 'Prompt Eng',
  'other': 'Other'
}

interface NodeData {
  id: string
  paper: Paper
  x: number
  y: number
  topic: string
  year: number
  authors: string[]
  source: string
  citationTier: number
}

interface EdgeData {
  source: string
  target: string
  strength: number
  reason: string
}

// Calculate relationships based on dimension
function calculateEdges(nodes: NodeData[], dimension: RelationDimension): EdgeData[] {
  const edges: EdgeData[] = []

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const nodeA = nodes[i]
      const nodeB = nodes[j]
      let strength = 0
      let reason = ''

      switch (dimension) {
        case 'topic':
          if (nodeA.topic === nodeB.topic) {
            strength = 1.0
            reason = nodeA.topic
          }
          break

        case 'author':
          const sharedAuthors = nodeA.authors.filter(a => 
            nodeB.authors.some(b => a.includes(b) || b.includes(a))
          )
          if (sharedAuthors.length > 0) {
            strength = Math.min(1, sharedAuthors.length * 0.5)
            reason = sharedAuthors[0]
          }
          break

        case 'year':
          const yearDiff = Math.abs(nodeA.year - nodeB.year)
          if (yearDiff === 0) {
            strength = 1.0
            reason = nodeA.year.toString()
          } else if (yearDiff === 1) {
            strength = 0.5
            reason = `${Math.min(nodeA.year, nodeB.year)}-${Math.max(nodeA.year, nodeB.year)}`
          }
          break

        case 'citations':
          if (nodeA.citationTier === nodeB.citationTier && nodeA.citationTier > 0) {
            strength = 0.3 + nodeA.citationTier * 0.2
            reason = ['Low', 'Medium', 'High'][nodeA.citationTier - 1] || ''
          }
          break

        case 'source':
          if (nodeA.source === nodeB.source && nodeA.source !== 'unknown') {
            strength = 1.0
            reason = nodeA.source
          }
          break
      }

      if (strength > 0) {
        edges.push({ source: nodeA.id, target: nodeB.id, strength, reason })
      }
    }
  }

  return edges
}

// Force-directed layout with better spacing
function calculateLayout(papers: Paper[], width: number, height: number): NodeData[] {
  if (papers.length === 0) return []

  const centerX = width / 2
  const centerY = height / 2
  const radius = Math.min(width, height) * 0.4

  // Initial positions in a spiral for better distribution
  const nodes: NodeData[] = papers.map((paper, i) => {
    const angle = (2 * Math.PI * i) / papers.length
    const spiralRadius = radius * (0.5 + 0.5 * (i / papers.length))
    
    return {
      id: paper.paper_id,
      paper,
      x: centerX + Math.cos(angle) * spiralRadius,
      y: centerY + Math.sin(angle) * spiralRadius,
      topic: detectTopic(paper),
      year: extractYear(paper),
      authors: extractAuthors(paper),
      source: extractSource(paper),
      citationTier: getCitationTier(paper)
    }
  })

  // Force simulation for better spacing
  const iterations = 150
  const repulsion = 3500  // Increased for more separation
  const centerPull = 0.003

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion between all nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].x - nodes[i].x
        const dy = nodes[j].y - nodes[i].y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const minDist = 80  // Minimum distance between nodes

        if (dist < minDist * 2) {
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

    // Pull toward center
    for (const node of nodes) {
      node.x += (centerX - node.x) * centerPull
      node.y += (centerY - node.y) * centerPull
    }

    // Keep within bounds
    const padding = 80
    for (const node of nodes) {
      node.x = Math.max(padding, Math.min(width - padding, node.x))
      node.y = Math.max(padding, Math.min(height - padding, node.y))
    }
  }

  return nodes
}

export default function RelationshipGraph({
  papers,
  onNodeClick,
  className = ''
}: RelationshipGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 1000, height: 700 })
  const [hoveredNode, setHoveredNode] = useState<NodeData | null>(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [nodePositions, setNodePositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const [dimension, setDimension] = useState<RelationDimension>('topic')
  const [hiddenTopics, setHiddenTopics] = useState<Set<string>>(new Set())
  const isPanning = useRef(false)
  const isDraggingNode = useRef<string | null>(null)
  const lastMouse = useRef({ x: 0, y: 0 })

  // Calculate layout
  const initialNodes = useMemo(() => {
    if (papers.length === 0) return []
    return calculateLayout(papers, dimensions.width, dimensions.height)
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

  // Get unique topics
  const topics = useMemo(() => {
    const t = new Set(nodes.map(n => n.topic))
    return Array.from(t)
  }, [nodes])

  // Filter visible nodes
  const visibleNodes = useMemo(() => {
    return nodes.filter(n => !hiddenTopics.has(n.topic))
  }, [nodes, hiddenTopics])

  // Calculate edges based on current dimension
  const edges = useMemo(() => {
    return calculateEdges(visibleNodes, dimension)
  }, [visibleNodes, dimension])

  // Get unique connection reasons for current dimension
  const connectionGroups = useMemo(() => {
    const groups = new Map<string, number>()
    edges.forEach(e => {
      groups.set(e.reason, (groups.get(e.reason) || 0) + 1)
    })
    return Array.from(groups.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8)
  }, [edges])

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

  // Toggle topic visibility
  const toggleTopic = useCallback((topic: string) => {
    setHiddenTopics(prev => {
      const next = new Set(prev)
      if (next.has(topic)) {
        next.delete(topic)
      } else {
        next.add(topic)
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
    setHiddenTopics(new Set())
  }, [])

  if (papers.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-50 ${className}`}>
        <p className="text-gray-500">No papers to visualize</p>
      </div>
    )
  }

  const nodeMap = new Map(visibleNodes.map(n => [n.id, n]))
  const nodeSize = 12  // Uniform smaller size for readability

  return (
    <div
      ref={containerRef}
      className={`h-full w-full relative bg-gradient-to-br from-gray-900 to-slate-800 overflow-hidden ${className}`}
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
        {/* Edges with gradient based on dimension */}
        <defs>
          {connectionGroups.map(([reason], i) => (
            <linearGradient key={reason} id={`edge-gradient-${i}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={`hsl(${(i * 40) % 360}, 70%, 60%)`} stopOpacity="0.6" />
              <stop offset="100%" stopColor={`hsl(${(i * 40 + 30) % 360}, 70%, 60%)`} stopOpacity="0.6" />
            </linearGradient>
          ))}
        </defs>

        <g>
          {edges.map((edge, i) => {
            const source = nodeMap.get(edge.source)
            const target = nodeMap.get(edge.target)
            if (!source || !target) return null

            const gradientIndex = connectionGroups.findIndex(([r]) => r === edge.reason)
            const midX = (source.x + target.x) / 2
            const midY = (source.y + target.y) / 2
            const dx = target.x - source.x
            const dy = target.y - source.y
            const dist = Math.sqrt(dx * dx + dy * dy)
            
            // Curve the line slightly
            const perpX = -dy / dist * 20
            const perpY = dx / dist * 20

            return (
              <path
                key={i}
                d={`M ${source.x} ${source.y} Q ${midX + perpX} ${midY + perpY}, ${target.x} ${target.y}`}
                stroke={gradientIndex >= 0 ? `url(#edge-gradient-${gradientIndex})` : 'rgba(255,255,255,0.2)'}
                strokeWidth={1 + edge.strength}
                fill="none"
                opacity={0.5}
              />
            )
          })}
        </g>

        {/* Nodes - uniform size with glow effect */}
        {visibleNodes.map(node => {
          const isHovered = hoveredNode?.id === node.id
          const color = TOPIC_COLORS[node.topic] || TOPIC_COLORS.other

          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              style={{ cursor: isDraggingNode.current === node.id ? 'grabbing' : 'pointer' }}
              onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
              onClick={(e) => {
                if (!nodePositions.has(node.id) || e.detail === 2) {
                  onNodeClick?.(node.id)
                }
              }}
              onMouseEnter={() => setHoveredNode(node)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              {/* Glow effect */}
              <circle
                r={nodeSize + 4}
                fill="none"
                stroke={color}
                strokeWidth={2}
                opacity={isHovered ? 0.8 : 0.3}
                style={{ filter: 'blur(3px)' }}
              />
              
              {/* Node circle - semi-transparent */}
              <circle
                r={nodeSize}
                fill={color}
                fillOpacity={0.85}
                stroke={isHovered ? '#fff' : 'rgba(255,255,255,0.5)'}
                strokeWidth={isHovered ? 2 : 1}
                style={{
                  transition: 'all 0.15s ease'
                }}
              />

              {/* Always visible label with dark background */}
              <rect
                x={-55}
                y={nodeSize + 6}
                width={110}
                height={16}
                fill="rgba(0,0,0,0.75)"
                rx={3}
                style={{ pointerEvents: 'none' }}
              />
              <text
                y={nodeSize + 17}
                textAnchor="middle"
                fill="#e5e7eb"
                fontSize="9"
                fontWeight="500"
                style={{ pointerEvents: 'none' }}
              >
                {node.paper.title?.slice(0, 18)}{(node.paper.title?.length || 0) > 18 ? '...' : ''}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Dimension Selector - Top Center */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-gray-800/95 border border-gray-600 rounded-xl p-2 shadow-xl backdrop-blur-sm">
        <div className="flex items-center gap-1">
          <span className="text-xs text-gray-400 mr-2 font-medium">Connect by:</span>
          {(Object.keys(DIMENSION_INFO) as RelationDimension[]).map(dim => (
            <button
              key={dim}
              onClick={() => setDimension(dim)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                dimension === dim
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              title={DIMENSION_INFO[dim].description}
            >
              {DIMENSION_INFO[dim].label}
            </button>
          ))}
        </div>
      </div>

      {/* Topics Legend - Left */}
      <div className="absolute top-20 left-4 bg-gray-800/95 border border-gray-600 rounded-xl p-4 shadow-lg backdrop-blur-sm max-w-xs">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Topics (click to filter)</h3>
        <div className="space-y-1">
          {topics.map(topic => {
            const isHidden = hiddenTopics.has(topic)
            const count = nodes.filter(n => n.topic === topic).length
            return (
              <button
                key={topic}
                onClick={() => toggleTopic(topic)}
                className={`flex items-center gap-2 w-full px-2 py-1 rounded text-left text-xs transition-all ${
                  isHidden ? 'opacity-40 line-through' : 'hover:bg-gray-700'
                }`}
              >
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: TOPIC_COLORS[topic] || TOPIC_COLORS.other }}
                />
                <span className="text-gray-200 flex-1">{TOPIC_LABELS[topic] || topic}</span>
                <span className="text-gray-500">{count}</span>
              </button>
            )
          })}
        </div>

        <button
          onClick={resetView}
          className="mt-3 text-xs text-blue-400 hover:text-blue-300"
        >
          Reset view & filters
        </button>
      </div>

      {/* Connection Groups Legend - Right */}
      {connectionGroups.length > 0 && (
        <div className="absolute top-20 right-4 bg-gray-800/95 border border-gray-600 rounded-xl p-4 shadow-lg backdrop-blur-sm max-w-xs">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">
            Connections ({edges.length})
          </h3>
          <div className="space-y-1 text-xs">
            {connectionGroups.map(([reason, count], i) => (
              <div key={reason} className="flex items-center gap-2">
                <div
                  className="w-8 h-1 rounded"
                  style={{ 
                    background: `linear-gradient(90deg, hsl(${(i * 40) % 360}, 70%, 60%), hsl(${(i * 40 + 30) % 360}, 70%, 60%))`
                  }}
                />
                <span className="text-gray-300 flex-1 truncate">{reason}</span>
                <span className="text-gray-500">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="absolute bottom-4 right-4 bg-gray-800/95 border border-gray-600 rounded-lg px-4 py-2 shadow-sm backdrop-blur-sm">
        <p className="text-sm text-gray-300">
          <span className="font-semibold text-blue-400">{visibleNodes.length}</span>/{papers.length} papers •
          <span className="font-semibold text-purple-400 ml-2">{edges.length}</span> connections
        </p>
      </div>

      {/* Hover tooltip */}
      {hoveredNode && (
        <div
          className="absolute z-50 bg-gray-900 border border-gray-600 rounded-xl shadow-xl p-4 pointer-events-none max-w-sm"
          style={{
            left: Math.min(hoveredNode.x * transform.scale + transform.x + 25, dimensions.width - 320),
            top: Math.max(hoveredNode.y * transform.scale + transform.y - 80, 20)
          }}
        >
          <h4 className="font-semibold text-gray-100 text-sm mb-2 line-clamp-2">
            {hoveredNode.paper.title || 'Untitled'}
          </h4>
          <div className="flex items-center gap-2 text-xs mb-2 flex-wrap">
            <span className="px-2 py-0.5 bg-blue-900 text-blue-300 rounded">
              {hoveredNode.year}
            </span>
            <span
              className="px-2 py-0.5 rounded text-white"
              style={{ backgroundColor: TOPIC_COLORS[hoveredNode.topic] }}
            >
              {TOPIC_LABELS[hoveredNode.topic] || hoveredNode.topic}
            </span>
            {hoveredNode.source !== 'unknown' && (
              <span className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded">
                {hoveredNode.source}
              </span>
            )}
          </div>
          {hoveredNode.authors.length > 0 && (
            <p className="text-xs text-gray-400 mb-1">
              <strong>Authors:</strong> {hoveredNode.authors.slice(0, 3).join(', ')}
              {hoveredNode.authors.length > 3 ? '...' : ''}
            </p>
          )}
          {hoveredNode.paper.abstract && (
            <p className="text-xs text-gray-400 line-clamp-2">{hoveredNode.paper.abstract}</p>
          )}
          <p className="text-xs text-blue-400 mt-2">Click to view details</p>
        </div>
      )}
    </div>
  )
}
